import pytest
from tortoise import Tortoise, fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import DoesNotExist
from pydantic import BaseModel

from ms_core.bases.abstract_model import AbstractModel
from ms_core.bases.base_crud import crud_for


class DemoModel(AbstractModel):
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)


# Additional model for extra CRUD tests
class ItemModel(AbstractModel):
    name = fields.CharField(max_length=50)
    value = fields.IntField(default=0)


@pytest.fixture(scope="session", autouse=True)
async def init_tortoise():
    """Initialize Tortoise ORM once per session."""
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": [__name__]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
def schemas():
    """Re-use the same schemas fixture for CRUD tests."""
    return {
        "full": pydantic_model_creator(DemoModel, name="DemoSchema"),
        "create": pydantic_model_creator(
            DemoModel, name="DemoCreate", exclude_readonly=True
        ),
        "update": pydantic_model_creator(
            DemoModel, name="DemoUpdate", exclude_readonly=True, exclude=("id",)
        ),
    }


@pytest.fixture
def item_schema():
    return pydantic_model_creator(ItemModel, name="ItemSchema")


@pytest.fixture
def item_schema_create():
    return pydantic_model_creator(ItemModel, name="ItemCreate", exclude_readonly=True)


@pytest.fixture
def item_crud(item_schema):
    return crud_for(ItemModel, item_schema)


@pytest.mark.asyncio
async def test_full_crud_cycle(schemas):
    CreateSchema = schemas["create"]
    UpdateSchema = schemas["update"]
    crud_instance = crud_for(DemoModel, schemas["full"])

    # CREATE
    to_create = CreateSchema(name="Item", description="Desc", is_active=False)
    created = await crud_instance.create(to_create)
    assert created.id is not None
    assert created.name == "Item"

    # READ
    fetched = await crud_instance.get_by_id(created.id)
    assert fetched and fetched.name == "Item"

    # UPDATE
    upd = UpdateSchema(name="New", description="New desc")
    updated = await crud_instance.update_by(upd, id=created.id)
    assert updated and updated.name == "New"

    # DELETE
    assert await crud_instance.delete_by(id=created.id) is True
    assert await crud_instance.get_by_id(created.id) is None


# --- Additional CRUD tests from test_crud_and_router_extra.py ---


@pytest.mark.asyncio
async def test_create_and_get_or_create(item_crud):
    # create
    create_schema = pydantic_model_creator(
        ItemModel, name="ItemCreate", exclude_readonly=True
    )
    payload = create_schema(name="A", value=1)  # type: ignore
    created = await item_crud.create(payload)
    assert created.id is not None
    assert created.name == "A"

    # get_or_create when exists
    inst1, created_flag1 = await item_crud.get_or_create(name="A")
    assert not created_flag1
    assert inst1.id == created.id

    # get_or_create when new
    inst2, created_flag2 = await item_crud.get_or_create(name="B", value=2)
    assert created_flag2
    assert inst2.name == "B"


@pytest.mark.asyncio
async def test_get_by_and_get_by_id(item_crud):
    # get non-existent
    assert await item_crud.get_by(name="nope") is None
    assert await item_crud.get_by_id(999) is None

    # create and retrieve
    inst = await item_crud.create(
        pydantic_model_creator(ItemModel, exclude_readonly=True)(name="X", value=10)  # type: ignore
    )
    by_kw = await item_crud.get_by(name="X")
    assert by_kw and by_kw.name == "X"
    by_id = await item_crud.get_by_id(inst.id)
    assert by_id and by_id.id == inst.id


@pytest.mark.asyncio
async def test_get_all_prefetch_and_nonprefetch(item_crud):
    # clear table
    await ItemModel.all().delete()
    # create
    for i in range(3):
        await ItemModel.create(name=f"N{i}", value=i)
    # non-prefetch
    res1 = await item_crud.get_all(prefetch=False, limit=2, offset=1)
    assert len(res1) == 2
    assert all(isinstance(item, BaseModel) for item in res1)
    # prefetch
    res2 = await item_crud.get_all(prefetch=True, limit=3, offset=0)
    assert len(res2) == 3
    assert all(hasattr(item, "dict") for item in res2)


@pytest.mark.asyncio
async def test_filter_by_and_error(item_crud, monkeypatch):
    # normal filter
    await ItemModel.create(name="F1", value=5)
    result = await item_crud.filter_by(name="F1")
    assert isinstance(result, list) and result[0].name == "F1"

    # simulate DoesNotExist
    async def fake_filter(**kwargs):
        raise DoesNotExist(model=ItemModel)

    monkeypatch.setattr(ItemModel, "filter", fake_filter)
    assert await item_crud.filter_by(name="anything") is None


@pytest.mark.asyncio
async def test_update_by_and_delete_by(item_crud):
    # create
    created = await item_crud.create(
        pydantic_model_creator(ItemModel, exclude_readonly=True)(name="U1", value=100)  # type: ignore
    )
    # update non-existent
    assert await item_crud.update_by({"name": "nope"}, id=999) is None
    # update with dict
    updated = await item_crud.update_by({"name": "U2", "value": None}, id=created.id)
    assert updated and updated.name == "U2"
    # update with schema
    schema_up = pydantic_model_creator(ItemModel, exclude_readonly=True)(
        name="U3",  # type: ignore
        value=3,  # type: ignore
    )
    updated2 = await item_crud.update_by(schema_up, id=created.id)
    assert updated2 and updated2.name == "U3"
    # delete non-existent
    assert await item_crud.delete_by(id=9999) is False
    # delete existent
    assert await item_crud.delete_by(id=created.id) is True
