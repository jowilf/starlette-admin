import starlette_admin
from . import types as t, utils
import asyncio


class BaseModelView(starlette_admin.BaseModelView):
    repo: t.ClassVar[t.Type[t.TortoiseModel]]

    async def find_all(
        self,
        request,
        skip: int = 0,
        limit: int = 100,
        where: t.Where = None,
        order_by: t.OrderBy = None,
    ) -> t.Sequence[t.TortoiseModel]:
        q = self.repo.all().limit(limit).offset(skip)
        if order_by is not None:
            q.order_by(*utils.starlette_admin_order_by2tortoise_order_by(order_by))
        return await self._find_all(request, q)

    async def _find_all(self, request, query):
        return query

    async def find_by_pk(self, request, pk: t.Pk) -> t.TortoiseModel:
        return await self.repo.get_or_none(pk=pk)

    async def find_by_pks(self, request, pks: t.Pks) -> t.Sequence[t.TortoiseModel]:
        return await self.repo.get_or_none(pk__in=pks)

    @classmethod
    def _insert_filters(cls, request, data):
        data_ = utils.remove_keys(
            data,
            iftrue=lambda k, v: k not in cls.repo._meta.o2o_fields and v is not None,
        )
        data_ = utils.add_id2fk_field(data_, cls.repo._meta.fk_fields)
        return data_

    async def create(self, request, data: dict) -> t.TortoiseModel:
        data = self._insert_filters(request, data)
        return await self._create(request, data)

    async def _create(self, request, data: dict):
        return self.repo.create(**data)

    async def delete(self, request, pks: t.Pks) -> t.Optional[int]:
        items = await self.find_by_pks(request, pks)
        return len(await asyncio.gather(*tuple(map(lambda item: item.delete(), items))))

    async def edit(self, request, pk: t.Pk, data: dict) -> t.TortoiseModel:
        item = await self.find_by_pk(request, pk)
        data = self._insert_filters(request, data)
        return await item.update_from_dict(data).save()

    @classmethod
    def from_model(cls, model: t.TortoiseModel):
        model_full_name_parts = model._meta.full_name

        class tmp(cls):
            repo = model
            identity = model_full_name_parts[-1].lower()
            name = model_full_name_parts[-1]
            label = f"{model_full_name_parts[-1].title()}s"
            fields = utils.model_fields2starlette_admin(model)

        return tmp
