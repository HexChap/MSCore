from typing import TYPE_CHECKING

from tortoise import fields, Tortoise

from ms_core import AbstractModel, I18nModel
from tests.models.test2 import Test2


class Test1(I18nModel):
    test = fields.TextField()

    test2: fields.ForeignKeyRelation[Test2] = fields.ForeignKeyField(
        "models.Test2", "test2"
    )

    class Meta:
        table = "test1"
