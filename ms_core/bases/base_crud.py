from typing import Type, TypeVar, Generic
from tortoise.contrib.pydantic import PydanticModel
from tortoise.exceptions import DoesNotExist
from tortoise import Model as TortoiseModel

M = TypeVar("M", bound=TortoiseModel)
S = TypeVar("S", bound=PydanticModel)


class CRUD(Generic[M, S]):
    def __init__(self, model: Type[M], schema: Type[S]) -> None:
        self._model: Type[M] = model
        self._schema: Type[S] = schema

    async def create(self, payload: S, **kwargs) -> S:
        inst = await self._model.create(
            **payload.model_dump(exclude_none=True), **kwargs
        )
        return await self._schema.from_tortoise_orm(inst)

    async def get_or_create(self, **kwargs) -> tuple[S, bool]:
        inst, created = await self._model.get_or_create(**kwargs)
        return await self._schema.from_tortoise_orm(inst), created

    async def get_by_id(self, id_: int) -> S | None:
        return await self.get_by(id=id_)

    async def get_by(self, **kwargs) -> S | None:
        inst = await self._model.get_or_none(**kwargs)
        if not inst:
            return None
        return await self._schema.from_tortoise_orm(inst)

    async def get_all(
        self, prefetch: bool = False, limit: int = 50, offset: int = 0, **extra_filters
    ) -> list[S]:
        queryset = self._model.all().filter(**extra_filters).offset(offset).limit(limit)
        out: list[S] = []
        for item in await queryset:
            if prefetch:
                out.append(await self._schema.from_tortoise_orm(item))
            else:
                out.append(self._schema.model_construct(**item.__dict__))
        return out

    async def filter_by(self, **kwargs) -> list[S] | None:
        try:
            items = await self._model.filter(**kwargs)
            return [await self._schema.from_tortoise_orm(i) for i in items]
        except DoesNotExist:
            return None

    async def update_by(self, payload: S | dict, **kwargs) -> S | None:
        inst = await self._model.get_or_none(**kwargs)
        if not inst:
            return None

        updates = (
            payload.items()
            if isinstance(payload, dict)
            else payload.model_dump().items()
        )
        await inst.update_from_dict({k: v for k, v in updates if v is not None}).save()
        return await self._schema.from_tortoise_orm(inst)

    async def delete_by(self, **kwargs) -> bool:
        inst = await self._model.get_or_none(**kwargs)
        if not inst:
            return False
        await inst.delete()
        return True


def crud_for(model: Type[M], schema: Type[S]) -> CRUD[M, S]:
    """
    Factory that returns a CRUD instance with all methods typed correctly
    (e.g. .create expects S and returns S).
    """
    return CRUD(model, schema)
