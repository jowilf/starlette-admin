from typing import Any, Dict, List, Optional, Type, Union, no_type_check

import starlette_admin
from bson import ObjectId
from mongoengine.base.fields import BaseField as MongoBaseField
from mongoengine.document import Document
from mongoengine.errors import DoesNotExist, ValidationError
from mongoengine.fields import GridFSProxy
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin import HasMany, HasOne
from starlette_admin.contrib.mongoengine.helpers import (
    build_order_clauses,
    build_raw_query,
    convert_mongoengine_field_to_admin_field,
    normalize_list,
)
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import BaseField
from starlette_admin.helpers import prettify_class_name, slugify_class_name
from starlette_admin.views import BaseModelView


class ModelViewMeta(type):
    @no_type_check
    def __new__(mcs, name, bases, attrs: dict, **kwargs: Any):
        cls: Type["ModelView"] = super().__new__(mcs, name, bases, attrs)
        document: Optional[Document] = kwargs.get("document")
        if document is None:
            return cls
        cls.document = document
        cls.identity = attrs.get("identity", slugify_class_name(document.__name__))
        cls.label = attrs.get("label", prettify_class_name(document.__name__) + "s")
        cls.name = attrs.get("name", prettify_class_name(document.__name__))
        fields = attrs.get("fields", document._fields_ordered)
        converted_fields = []
        for value in fields:
            if isinstance(value, BaseField):
                converted_fields.append(value)
            else:
                field = None
                if isinstance(value, MongoBaseField):
                    field = value
                elif isinstance(value, str):
                    field = getattr(document, value)
                else:
                    raise ValueError(f"Can't find column with key {value}")
                converted_fields.append(convert_mongoengine_field_to_admin_field(field))
        cls.fields = converted_fields
        cls.exclude_fields_from_list = normalize_list(
            attrs.get("exclude_fields_from_list", [])
        )
        cls.exclude_fields_from_detail = normalize_list(
            attrs.get("exclude_fields_from_detail", [])
        )
        cls.exclude_fields_from_create = normalize_list(
            attrs.get("exclude_fields_from_create", [])
        )
        cls.exclude_fields_from_edit = normalize_list(
            attrs.get("exclude_fields_from_edit", [])
        )
        cls.searchable_fields = normalize_list(attrs.get("searchable_fields", None))
        cls.sortable_fields = normalize_list(attrs.get("sortable_fields", None))
        cls.export_fields = normalize_list(attrs.get("export_fields", None))
        return cls


class ModelView(BaseModelView, metaclass=ModelViewMeta):
    document: Type[Document]
    identity: Optional[str] = None
    pk_attr: Optional[str] = "id"
    fields: List[BaseField] = []

    async def count(
        self,
        request: Request,
        where: Union[Dict[str, Any], str, None] = None,
    ) -> int:
        if where is None:
            where = {}
        elif isinstance(where, dict):
            where = build_raw_query(where)
        else:
            where = self.build_full_text_search_query(request, where)
        return self.document.objects(__raw__=where).count()

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[Any]:
        if where is None:
            where = {}
        elif isinstance(where, dict):
            where = build_raw_query(where)
        else:
            where = self.build_full_text_search_query(request, where)
        objs = self.document.objects(__raw__=where).order_by(
            *build_order_clauses(order_by or [])
        )
        if limit > 0:
            return objs[skip : skip + limit]
        return objs[skip:]

    async def find_by_pk(self, request: Request, pk: Any) -> Optional[Document]:
        try:
            return self.document.objects(id=pk).get()
        except (DoesNotExist, ValidationError):
            return None

    async def find_by_pks(self, request: Request, pks: List[Any]) -> List[Document]:
        return self.document.objects(id__in=pks)

    async def create(self, request: Request, data: Dict[str, Any]) -> None:
        try:
            return (await self._populate_obj(request, self.document(), data)).save()
        except Exception as e:
            self.handle_exception(e)

    async def edit(self, request: Request, pk: Any, data: Dict[str, Any]) -> Any:
        try:
            obj = await self.find_by_pk(request, pk)
            return (await self._populate_obj(request, obj, data, True)).save()
        except Exception as e:
            self.handle_exception(e)

    async def _populate_obj(
        self,
        request: Request,
        obj: Document,
        data: Dict[str, Any],
        is_edit: bool = False,
    ) -> Document:
        for field in self.fields:
            if (is_edit and field.exclude_from_edit) or (
                not is_edit and field.exclude_from_create
            ):
                continue
            name, value = field.name, data.get(field.name, None)
            if isinstance(field, starlette_admin.FileField):
                proxy: GridFSProxy = getattr(obj, name)
                if data.get(f"_{name}-delete", False):
                    proxy.delete()
                elif isinstance(value, UploadFile):
                    if proxy.grid_id is not None:
                        proxy.replace(
                            value.file,
                            filename=value.filename,
                            content_type=value.content_type,
                        )
                    else:
                        proxy.put(
                            value.file,
                            filename=value.filename,
                            content_type=value.content_type,
                        )
            elif isinstance(field, HasOne) and value is not None:
                setattr(obj, name, ObjectId(value))
            elif isinstance(field, HasMany) and value is not None:
                setattr(obj, name, [ObjectId(v) for v in value])
            else:
                setattr(obj, name, value)
        return obj

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        return self.document.objects(id__in=pks).delete()

    def handle_exception(self, exc: Exception) -> None:
        if isinstance(exc, ValidationError):
            raise FormValidationError(exc.errors)
        raise exc  # pragma: no cover

    def build_full_text_search_query(
        self, request: Request, term: str
    ) -> Dict[str, Any]:
        query: Dict[str, Any] = {"$or": []}
        for field in self.fields:
            if field.searchable:
                query["$or"].append(
                    {field.name: {"$regex": str(term), "$options": "mi"}}
                )
        return query

    async def serialize_field_value(
        self, value: Any, field: BaseField, action: str, request: Request
    ) -> Any:
        if isinstance(value, GridFSProxy):
            if value.grid_id:
                id = value.grid_id
                if action == "API" and getattr(value, "thumbnail_id", None) is not None:
                    id = getattr(value, "thumbnail_id")
                return {
                    "filename": getattr(value, "filename", "unamed"),
                    "content_type": getattr(
                        value, "content_type", "application/octet-stream"
                    ),
                    "url": request.url_for(
                        request.app.state.ROUTE_NAME + ":api:file",
                        db=value.db_alias,
                        col=value.collection_name,
                        pk=id,
                    ),
                }
            return None
        return await super().serialize_field_value(value, field, action, request)
