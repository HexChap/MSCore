from tortoise import fields

from ms_core.bases.abstract_model import AbstractModel
from ms_core.bases.i18n_model import I18nModel


class Test2(AbstractModel, I18nModel):
    test = fields.IntField()

    test1: fields.ReverseRelation

    class Meta:
        table = "test2"
