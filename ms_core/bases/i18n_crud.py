from multimethod import multimethod
from tortoise import Model as TortoiseModel
from tortoise.contrib.pydantic import PydanticModel

from ms_core.bases import BaseCRUD


class I18nCRUD[Model: TortoiseModel, Schema: PydanticModel](BaseCRUD[Model, Schema]):
    @classmethod
    @BaseCRUD.get_by_id.register
    async def get_by_id(cls, id_: int, lang: str) -> Schema | None:
        return await cls.get_by(id=id_, tuple_lang=lang)

    @classmethod
    @multimethod
    async def get_all_prefetch(cls, lang: str = None) -> list[Schema]:
        result = []
        query = cls.model.filter(tuple_lang=lang) if lang else cls.model

        for item in await query.all():
            result.append(await cls.schema.from_tortoise_orm(item))

        return result

    @classmethod
    @multimethod
    async def get_all(cls, limit: int = 50, offset: int = 0, lang: str = None) -> list[Model]:
        result = []
        query = cls.model.filter(tuple_lang=lang) if lang else cls.model
        query = query.all().offset(offset).limit(limit)

        for item in await query:
            result.append(cls.schema.model_construct(**item.__dict__))

        return result
