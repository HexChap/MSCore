import pytest
from tortoise import fields, Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from ms_core.bases.abstract_model import AbstractModel
from ms_core.bases.i18n_crud import i18n_crud_for
from ms_core.bases.i18n_model import I18nModel


class I18nDemoModel(AbstractModel, I18nModel):
    name = fields.CharField(max_length=50)


@pytest.fixture(scope="session", autouse=True)
async def init_db():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": [__name__]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
def i18n_crud():
    schema = pydantic_model_creator(I18nDemoModel)
    return i18n_crud_for(I18nDemoModel, schema)


@pytest.mark.asyncio
async def test_i18n_crud_get_by_id(i18n_crud):
    item = await I18nDemoModel.create(name="Test I18n", tuple_lang="en")
    # correct lang
    res = await i18n_crud.get_by_id(item.id, lang="en")
    assert res and res.name == "Test I18n"
    # wrong lang
    assert await i18n_crud.get_by_id(item.id, lang="de") is None


@pytest.mark.asyncio
async def test_i18n_crud_get_all(i18n_crud):
    # clear out any prior rows
    await I18nDemoModel.all().delete()

    # create two languages
    await I18nDemoModel.create(name="One", tuple_lang="en")
    await I18nDemoModel.create(name="Zwei", tuple_lang="de")

    en_list = await i18n_crud.get_all(lang="en")
    assert len(en_list) == 1
    assert en_list[0].name == "One"

    # no lang filter → get both
    full = await i18n_crud.get_all()
    assert len(full) == 2
    names = {o.name for o in full}
    assert names == {"One", "Zwei"}
