from multimethod import multimethod
from tortoise import Model as TortoiseModel
from tortoise.contrib.pydantic import PydanticModel

from ms_core.bases import BaseCRUD


class I18nCRUD[Model: TortoiseModel, Schema: PydanticModel](BaseCRUD[Model, Schema]):
    """ Alternated CRUD for i18n models """
    @classmethod
    @BaseCRUD.get_by_id.register
    async def get_by_id(cls, id_: int, lang: str) -> Schema | None:
        return await cls.get_by(id=id_, tuple_lang=lang)

    @classmethod
    @multimethod
    async def get_all(cls, lang: str = None, *args, **kwargs) -> list[Model]:
        return await super().get_all(*args, **kwargs, tuple_lang=lang)
