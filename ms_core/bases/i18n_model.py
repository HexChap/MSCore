from tortoise import fields, Model


class I18nModel(Model):
    tuple_lang = fields.CharField(max_length=3)

    class Meta:
        abstract = True
