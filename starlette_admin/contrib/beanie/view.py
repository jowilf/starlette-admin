from typing import Any, Dict, Iterable, List, Mapping, Optional, Type, Union, get_args, get_origin

from beanie import Document, PydanticObjectId, Link
from mongoengine.queryset import QNode
from mongoengine.queryset.visitor import QCombination
from pydantic import ValidationError
from starlette.requests import Request
from starlette_admin.contrib.beanie.converters import (
    BeanieModelConverter,
    get_pydantic_field_type,
)
from starlette_admin.contrib.beanie.helpers import (
    Q,
    build_order_clauses,
    normalize_list,
    resolve_deep_query,
)
from starlette_admin.fields import FileField, RelationField
from starlette_admin.helpers import (
    not_none,
    prettify_class_name,
    slugify_class_name,
)
from starlette_admin.views import BaseModelView
from starlette_admin.fields import (
    HasOne,
)
from starlette_admin._types import RequestAction


class ModelView(BaseModelView):
    def __init__(
        self,
        document: Type[Document],
        icon: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        identity: Optional[str] = None,
        converter: Optional[BeanieModelConverter] = None,
    ):
        self.document = document
        self.identity = (
            identity or self.identity or slugify_class_name(self.document.__name__)
        )
        self.label = (
            label or self.label or prettify_class_name(self.document.__name__) + "s"
        )
        self.name = name or self.name or prettify_class_name(self.document.__name__)
        self.icon = icon
        self.pk_attr = "id"
        self.fields_pydantic = list(document.model_fields.items())

        self.field_infos = []
        self.link_fields = []
        for name, field in document.model_fields.items():
            field_type = get_pydantic_field_type(field)
            if self.is_link_type(field_type):
                self.link_fields.append({"name": name, "type": field_type, "required": field.is_required()})
            else:
                self.field_infos.append({"name": name, "type": field_type, "required": field.is_required()})
        self.fields = list((converter or BeanieModelConverter()).convert_fields_list(fields=self.field_infos, model=self.document))

        self.fields.extend(BeanieModelConverter().conv_link(**link_field) for link_field in self.link_fields)

        super().__init__()

    def is_link_type(self, field_type):
        # Check if the type is a Link
        if get_origin(field_type) == Link:
            return True

        # Check if the type is a list of Links
        if get_origin(field_type) == list:
            field_args = get_args(field_type)
            if len(field_args) == 1 and get_origin(field_args[0]) == Link:
                return True

        return False

    async def _build_query(
        self, request: Request, where: Union[Dict[str, Any], str, None] = None
    ) -> QNode:
        if where is None:
            return Q.empty()
        if isinstance(where, dict):
            return resolve_deep_query(where, self.document)
        return await self.build_full_text_search_query(request, where)

    async def count(
        self,
        request: Request,
        where: Union[Dict[str, Any], str, None] = None,
        **kwargs
    ) -> int:
        query = await self._build_query(request, where)

        if isinstance(query, QCombination):
            result = self.document.find(*[q.query for q in query.children], **kwargs)
        else:
            if query.empty:
                return await self.document.get_motor_collection().estimated_document_count()
            result = self.document.find(query.query, **kwargs)
        return await result.count()

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        **kwargs
    ) -> List[Dict]:
        if not where:
            where = {}
        query = await self._build_query(request, where)
        order_by = kwargs.pop("order_by", None)
        if isinstance(query, QCombination):
            result = self.document.find(*[q.query for q in query.children], **kwargs)
        else:
            result = self.document.find(query.query, **kwargs)

        if order_by:
            order_by = build_order_clauses(order_by)
            result = result.sort(*order_by)
        return await result.skip(skip).limit(limit).to_list()

    async def find_by_pk(self, request: Request, pk: PydanticObjectId, **kwargs) -> Optional[Document]:
        return await self.document.get(pk, **kwargs)

    async def find_by_pks(self, request: Request, pks: Iterable[PydanticObjectId], **kwargs) -> List[Document]:
        docs = []
        for pk in pks:
            doc = await self.document.get(pk, **kwargs)
            if doc:
                docs.append(doc)
        return docs

    async def get_pk_value(self, request: Request, obj: Any) -> Any:
        if isinstance(obj, Link):
            return getattr(obj.ref, not_none(self.pk_attr))

        return getattr(obj, not_none(self.pk_attr))

    async def serialize(
        self,
        obj: Any,
        request: Request,
        action: RequestAction,
        include_relationships: bool = True,
        include_select2: bool = False,
    ) -> Dict[str, Any]:
        obj_serialized: Dict[str, Any] = {}
        obj_meta: Dict[str, Any] = {}
        for field in self.get_fields_list(request, action):
            if isinstance(field, RelationField) and include_relationships:
                value = getattr(obj, field.name, None)
                foreign_model = self._find_foreign_model(field.identity)  # type: ignore
                if value is None:
                    obj_serialized[field.name] = None
                elif isinstance(field, HasOne):
                    if action == RequestAction.EDIT:
                        obj_serialized[field.name] = (
                            await foreign_model.get_serialized_pk_value(request, value)
                        )
                    else:
                        obj_serialized[field.name] = await foreign_model.serialize(
                            value.ref, request, action, include_relationships=False
                        )
                else:
                    if action == RequestAction.EDIT:
                        obj_serialized[field.name] = [
                            (await foreign_model.get_serialized_pk_value(request, obj))
                            for obj in value
                        ]
                    else:
                        obj_serialized[field.name] = [
                            await foreign_model.serialize(
                                v.ref, request, action, include_relationships=False
                            )
                            for v in value
                        ]
            elif not isinstance(field, RelationField):
                value = await field.parse_obj(request, obj)
                obj_serialized[field.name] = await self.serialize_field_value(
                    value, field, action, request
                )
        if include_select2:
            obj_meta["select2"] = {
                "selection": await self.select2_selection(obj, request),
                "result": await self.select2_result(obj, request),
            }
        obj_meta["repr"] = await self.repr(obj, request)

        # Make sure the primary key is always available
        pk_attr = not_none(self.pk_attr)
        if pk_attr not in obj_serialized:
            pk_value = await self.get_serialized_pk_value(request, obj)
            obj_serialized[pk_attr] = pk_value

        pk = await self.get_pk_value(request, obj)
        route_name = request.app.state.ROUTE_NAME
        obj_meta["detailUrl"] = str(
            request.url_for(route_name + ":detail", identity=self.identity, pk=pk)
        )
        obj_serialized["_meta"] = obj_meta
        return obj_serialized

    async def create(self, request: Request, data: Document):
        return await data.create()

    async def edit(self, request: Request, pk, data: Document, **kwargs):
        await data.save(**kwargs)

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        cnt = 0
        for pk in pks:
            value = await self.find_by_pk(request, pk)
            if value is not None:
                await value.delete()
                cnt += 1
        return cnt
