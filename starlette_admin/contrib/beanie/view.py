import functools
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    get_args,
    get_origin,
)

import bson.errors
import starlette_admin.fields as sa
from beanie import Document, Link, PydanticObjectId
from mongoengine.queryset import QNode
from mongoengine.queryset.visitor import QCombination
from pydantic import ValidationError
from starlette.requests import Request
from starlette_admin._types import RequestAction
from starlette_admin.contrib.beanie.converters import (
    BeanieModelConverter,
)
from starlette_admin.contrib.beanie.helpers import (
    Q,
    build_order_clauses,
    flatten_qcombination,
    is_link_type,
    is_list_of_links_type,
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
        exclude_fields_from_detail: Optional[List[str]] = None,
        full_text_override_order_by: bool = False,
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
        self.full_text_override_order_by = full_text_override_order_by
        self.has_full_text_index: Optional[bool] = None

        self.fields_pydantic = list(document.model_fields.items())

        self.field_infos = []
        self.link_fields = []
        self.exclude_fields_from_create = exclude_fields_from_create or []
        self.exclude_fields_from_create.append("revision_id")

        self.exclude_fields_from_edit = exclude_fields_from_edit or []
        self.exclude_fields_from_edit.extend(("revision_id", "id"))

        self.exclude_fields_from_list = exclude_fields_from_list or []
        self.exclude_fields_from_list.append("revision_id")

        self.exclude_fields_from_detail = exclude_fields_from_detail or []
        self.exclude_fields_from_detail.append("revision_id")

        for name, field in document.model_fields.items():
            field_type = field.annotation
            while get_origin(field_type) is Union:
                field_type = get_args(field_type)[0]
            if is_link_type(field_type) or is_list_of_links_type(field_type):
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

    async def check_full_text_index(self) -> None:
        indexes = await self.document.get_motor_collection().index_information()
        for index in indexes.values():
            if any(field_type == "text" for _, field_type in index["key"]):
                self.has_full_text_index = True
                return
        self.has_full_text_index = False

    async def _build_query(
        self, request: Request, where: Union[Dict[str, Any], str, None] = None
    ) -> Tuple[QNode, bool]:
        if where is None:
            return Q.empty(), False
        if isinstance(where, dict):
            return resolve_deep_query(where, self.document), False
        return await self.build_full_text_search_query(request, where)

    async def build_full_text_search_query(
        self, request: Request, term: str
    ) -> Tuple[QNode, bool]:
        # use a full text index if the collection has one,
        # otherwise use a combination of $icontains queries
        if self.has_full_text_index is None:
            await self.check_full_text_index()
        if self.has_full_text_index:
            return (
                Q(field="$text", value={"$search": term, "$caseSensitive": False}),
                True,
            )
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
        if queries:
            return (
                functools.reduce(lambda q1, q2: QCombination(Q.OR, [q1, q2]), queries),
                False,
            )
        return Q.empty(), False

    async def count(
        self, request: Request, where: Union[Dict[str, Any], str, None] = None
    ) -> int:
        query, _ = await self._build_query(request, where)
        if isinstance(query, QCombination):
            flattened_query = flatten_qcombination(query)
            result = self.document.find(flattened_query)
        else:
            if not bool(query):
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
        query, is_full_text_query = await self._build_query(request, where)
        if isinstance(query, QCombination):
            flattened_query = flatten_qcombination(query)
            result = self.document.find(flattened_query, **kwargs)
        else:
            result = self.document.find(query.query, **kwargs)

        # handle order_by
        if is_full_text_query and self.full_text_override_order_by:
            result = result.sort(("score", {"$meta": "textScore"}))  # type: ignore
        elif order_by:
            result = result.sort(build_order_clauses(order_by))
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
        assert doc is not None, "Document not found"
        data = {k: v for k, v in data.items() if k not in self.exclude_fields_from_edit}
        try:

            for key in data:
                field_type = self.document.model_fields[key].annotation
                if is_link_type(field_type):
                    if not isinstance(data[key], PydanticObjectId):
                        data[key] = (
                            None if not data[key] else PydanticObjectId(data[key])
                        )
                elif is_list_of_links_type(field_type):
                    data[key] = [PydanticObjectId(item) for item in data[key] if item]

                setattr(doc, key, data[key])

            # ensure doc still passes validation
            validated_doc: Document = self.document.model_validate(doc.model_dump())
            return await validated_doc.replace()

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
