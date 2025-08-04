from tortoise import fields
from ms_core import AbstractModel
from tests.models.test2 import Test2


class Test1(AbstractModel):
    test = fields.TextField()
    # test_migrate = fields.IntField()

    test2: fields.ForeignKeyRelation[Test2] = fields.ForeignKeyField(
        "models.Test2", "test1"
    )

    class Meta:
        table = "test1"
