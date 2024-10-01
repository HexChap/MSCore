from tortoise import fields, Model


class I18nModel(Model):
    """ Same abstract model but with tuple_lang field used to indicate row's language """
    tuple_lang = fields.CharField(max_length=3)

    class Meta:
        abstract = True
