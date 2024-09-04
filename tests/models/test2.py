from tortoise import fields

from ms_core import AbstractModel


class Test2(AbstractModel):
    test = fields.IntField()

    test1: fields.ReverseRelation

    class Meta:
        table = "test2"
