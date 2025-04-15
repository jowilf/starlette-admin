import functools
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
)

import bson.errors
import starlette_admin.fields as sa
from beanie import Document, Link, PydanticObjectId
from bson import DBRef
from mongoengine.queryset import QNode
from mongoengine.queryset.visitor import QCombination
from pydantic import ValidationError
from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.contrib.beanie.converters import (
    BeanieModelConverter,
    get_pydantic_field_type,
)
from starlette_admin.contrib.beanie.helpers import (
    Q,
    build_order_clauses,
    flatten_qcombination,
    resolve_deep_query,
)
from starlette_admin.fields import (
    HasOne,
    RelationField,
)
from starlette_admin.helpers import (
    not_none,
    prettify_class_name,
    pydantic_error_to_form_validation_errors,
    slugify_class_name,
)
from starlette_admin.views import BaseModelView


class ModelView(BaseModelView):
    def __init__(
        self,
        document: Type[Document],
        icon: Optional[str] = None,
        name: Optional[str] = None,
        label: Optional[str] = None,
        identity: Optional[str] = None,
        converter: Optional[BeanieModelConverter] = None,
        exclude_fields_from_create: Optional[List[str]] = None,
        exclude_fields_from_edit: Optional[List[str]] = None,
        exclude_fields_from_list: Optional[List[str]] = None,
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
        self.exclude_fields_from_create = exclude_fields_from_create or []
        self.exclude_fields_from_create.append("revision_id")

        self.exclude_fields_from_edit = exclude_fields_from_edit or []
        self.exclude_fields_from_edit.extend(("revision_id", "id"))

        self.exclude_fields_from_list = exclude_fields_from_list or []
        self.exclude_fields_from_list.append("revision_id")

        for name, field in document.model_fields.items():
            field_type = get_pydantic_field_type(field)
            if self.is_link_type(field_type):
                self.link_fields.append(
                    {"name": name, "type": field_type, "required": field.is_required()}
                )
            else:
                self.field_infos.append(
                    {"name": name, "type": field_type, "required": field.is_required()}
                )
        self.fields = list(
            (converter or BeanieModelConverter()).convert_fields_list(
                fields=self.field_infos, model=self.document
            )
        )

        self.fields.extend(
            BeanieModelConverter().conv_link(**link_field)
            for link_field in self.link_fields
        )

        super().__init__()

    def id_to_link(self, id: str, model: Type[Document]) -> Link:
        return Link(
            ref=DBRef(collection=model.get_collection_name(), id=PydanticObjectId(id)),
            document_class=model,
        )

    def is_link_type(self, field_type: Type) -> bool:
        if get_origin(field_type) is Link:
            return True
        if get_origin(field_type) is list:
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

    async def build_full_text_search_query(self, request: Request, term: str) -> QNode:
        queries = []
        for field in self.get_fields_list(request):
            if (
                field.searchable
                and field.name != "id"
                and type(field)
                in [
                    sa.StringField,
                    sa.TextAreaField,
                    sa.EmailField,
                    sa.URLField,
                    sa.PhoneField,
                    sa.ColorField,
                ]
            ):
                queries.append(Q(field.name, term, "$icontains"))
        return (
            functools.reduce(lambda q1, q2: QCombination(Q.OR, [q1, q2]), queries)
            if queries
            else Q.empty()
        )

    async def count(
        self, request: Request, where: Union[Dict[str, Any], str, None] = None
    ) -> int:
        query = await self._build_query(request, where)
        if isinstance(query, QCombination):
            flattened_query = flatten_qcombination(query)
            result = self.document.find(flattened_query)
        else:
            if query.empty:
                return (
                    await self.document.get_motor_collection().estimated_document_count()
                )
            result = self.document.find(query.query)
        return await result.count()

    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        where: Union[Dict[str, Any], str, None] = None,
        order_by: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[Dict]:
        if not where:
            where = {}
        query = await self._build_query(request, where)
        if isinstance(query, QCombination):
            flattened_query = flatten_qcombination(query)
            result = self.document.find(flattened_query, **kwargs)
        else:
            result = self.document.find(query.query, **kwargs)
        if order_by:
            order_by = build_order_clauses(order_by)
            result = result.sort(*order_by)
        return await result.skip(skip).limit(limit).to_list()

    async def find_by_pk(
        self, request: Request, pk: PydanticObjectId
    ) -> Optional[Document]:
        if not isinstance(pk, PydanticObjectId):
            try:
                pk = PydanticObjectId(pk)
            except bson.errors.InvalidId:
                return None

        return await self.document.get(pk)

    async def find_by_pks(
        self, request: Request, pks: Iterable[PydanticObjectId]
    ) -> List[Document]:
        docs = []
        for pk in pks:
            doc = await self.document.get(pk)
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

    async def create(self, request: Request, data: dict) -> Document:
        data = {
            k: v for k, v in data.items() if k not in self.exclude_fields_from_create
        }
        try:
            doc = self.document(**data)
        except ValidationError as ve:
            raise pydantic_error_to_form_validation_errors(ve) from ve
        return await doc.create()

    async def edit(
        self, request: Request, pk: PydanticObjectId, data: dict
    ) -> Document:
        doc: Document | None = await self.document.get(pk)
        if doc is None:
            raise ValueError("Document not found")
        data = {k: v for k, v in data.items() if k not in self.exclude_fields_from_edit}
        try:
            doc_dump: dict = doc.model_dump(mode="python")
            doc_dump.update(data)
            # ensure doc still passes validation
            for k, v in doc_dump.items():
                field = self.document.model_fields[k].annotation
                if self.is_link_type(field):
                    link_model_type = get_args(field)
                    link_origin_type = get_origin(field)

                    # if it's a link field, we need to set the ref
                    if link_origin_type is list:
                        link_model_type = get_args(link_model_type[0])
                        links = [
                            self.id_to_link(id=item, model=link_model_type[0])
                            for item in v
                        ]
                        setattr(doc, k, links)
                    else:
                        link = self.id_to_link(id=v, model=link_model_type[0])
                        setattr(doc, k, link)
                else:
                    setattr(doc, k, v)

            # ensure doc still passes validation
            self.document.model_validate(doc_dump)
            return await doc.replace()

        except ValidationError as ve:
            raise pydantic_error_to_form_validation_errors(ve) from ve

    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        cnt = 0
        for pk in pks:
            value = await self.find_by_pk(request, pk)
            if value is not None:
                await value.delete()
                cnt += 1
        return cnt
