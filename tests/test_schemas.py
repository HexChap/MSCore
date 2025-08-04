import pytest
import json

from tortoise import Tortoise, fields
from tortoise.contrib.pydantic import pydantic_model_creator
from ms_core.bases.abstract_model import AbstractModel


class DemoModel(AbstractModel):
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)


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
    """
    Returns a namespace of Pydantic schemas:
      - full: all fields
      - create: exclude readonly
      - update: exclude readonly + 'id'
    """
    full = pydantic_model_creator(DemoModel, name="DemoSchema")
    create = pydantic_model_creator(DemoModel, name="DemoCreate", exclude_readonly=True)
    update = pydantic_model_creator(
        DemoModel, name="DemoUpdate", exclude_readonly=True, exclude=("id",)
    )
    return {"full": full, "create": create, "update": update}


class TestPydanticSchemas:
    @pytest.mark.parametrize(
        "key, expected_fields",
        [
            ("full", {"id", "name", "description", "is_active", "created_at"}),
            ("create", {"name", "description", "is_active"}),
            ("update", {"name", "description", "is_active"}),
        ],
    )
    def test_model_fields(self, schemas, key, expected_fields):
        """Schemas expose exactly the expected model fields."""
        model = schemas[key]
        assert set(model.model_fields.keys()) == expected_fields

    @pytest.mark.parametrize(
        "schema_name, constructor_kwargs, should_raise",
        [
            ("create", {"name": "A", "description": "B", "is_active": True}, False),
            ("create", {"name": None}, True),
        ],
    )
    def test_validation_and_serialization(
        self, schemas, schema_name, constructor_kwargs, should_raise
    ):
        """Validate data and ensure serialization works or errors as expected."""
        Schema = schemas[schema_name]
        if should_raise:
            with pytest.raises(Exception):
                Schema(**constructor_kwargs)
        else:
            inst = Schema(**constructor_kwargs)
            dumped = inst.model_dump()
            for k, v in constructor_kwargs.items():
                assert dumped[k] == v
            # JSON round-trip
            json_str = inst.model_dump_json()
            for v in constructor_kwargs.values():
                assert json.dumps(v) in json_str
