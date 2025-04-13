from typing import Any, Dict, Optional, Type, Iterable, Mapping, List, Union, get_args

from beanie import Document, PydanticObjectId
from pydantic import ValidationError
from starlette.requests import Request
from starlette_admin.views import BaseModelView
from starlette_admin.fields import FileField, RelationField
from starlette_admin.contrib.beanie.converters import BeanieModelConverter, get_pydantic_field_type
from starlette_admin.helpers import (
    prettify_class_name,
    slugify_class_name,
)
from starlette_admin.contrib.beanie.helpers import (
    Q,
    build_order_clauses,
    normalize_list,
    resolve_deep_query,
)
from mongoengine.queryset import QNode
from mongoengine.queryset.visitor import QCombination


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
        for name, field in document.model_fields.items():
            field_type = get_pydantic_field_type(field)
            self.field_infos.append({"name": name, "type": field_type, "required": field.is_required()})

        self.fields = (converter or BeanieModelConverter()).convert_fields_list(fields=self.field_infos, model=self.document)

        super().__init__()

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
        order_by = kwargs.pop("order_by", None)

        if isinstance(query, QCombination):
            result = self.document.find(*[q.query for q in query.children], **kwargs)
        else:
            result = self.document.find(query.query, **kwargs)
        if order_by:
            order_by = build_order_clauses(order_by)
            result = result.sort(*order_by)
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
