from multimethod import multimethod
from tortoise import Model as TortoiseModel
from tortoise.contrib.pydantic import PydanticModel
from tortoise.exceptions import DoesNotExist


class BaseCRUD[Model: TortoiseModel, Schema: PydanticModel]:
    model: Model
    schema: Schema

    @classmethod
    async def create(cls, payload: PydanticModel, **kwargs) -> Schema:
        instance = await cls.model.create(
            **payload.model_dump(exclude_none=True), **kwargs
        )

        return await cls.schema.from_tortoise_orm(instance)

    @classmethod
    async def get_or_create(cls, **kwargs) -> tuple[Schema, bool]:
        instance, status = await cls.model.get_or_create(**kwargs)

        return await cls.schema.from_tortoise_orm(instance), status

    @classmethod
    @multimethod
    async def get_by_id(cls, id_: int) -> Schema | None:
        return await cls.get_by(id=id_)

    @classmethod
    async def get_by(cls, **kwargs) -> Schema | None:
        if not (instance := await cls.model.get_or_none(**kwargs)):
            return None

        return await cls.schema.from_tortoise_orm(instance)

    @classmethod
    @multimethod
    async def get_all_prefetch(cls) -> list[Schema]:
        result = []

        for item in await cls.model.all():
            result.append(await cls.schema.from_tortoise_orm(item))

        return result

    @classmethod
    @multimethod
    async def get_all(cls, limit: int = 50, offset: int = 0) -> list[Model]:
        """Bulk fetches from db, but without prefetching and validating. For prefetched result use *get_all_prefetch*"""

        query = cls.model.all().offset(offset).limit(limit)
        result = []

        for item in await query:
            result.append(item)

        return result

    @classmethod
    async def filter_by(cls, **kwargs) -> list[Schema] | None:
        try:
            return [
                await cls.schema.from_tortoise_orm(item)
                for item in await cls.model.filter(**kwargs)
            ]

        except DoesNotExist as _:
            return None

    @classmethod
    async def update_by(cls, payload: Schema | dict, **kwargs) -> Schema | None:
        if not (instance := await cls.get_by(**kwargs)):
            return None

        as_dict = (
            payload.items()
            if isinstance(payload, dict)
            else payload.model_dump().items()
        )

        await instance.update_from_dict(
            {key: value for key, value in as_dict if value is not None}
        ).save()
        return await cls.schema.from_tortoise_orm(instance)

    @classmethod
    async def delete_by(cls, **kwargs) -> bool:
        """
        Delete an item by given kwargs.

        :param kwargs: Search parameters
        :return: False if couldn't find the item, True if deleted successfully
        """
        if not (instance := await cls.model.get_or_none(**kwargs)):
            return False

        await instance.delete()
        return True
