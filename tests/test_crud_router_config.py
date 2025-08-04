"""Unit tests for BaseCRUDRouter configuration and EndpointConfig."""

import pytest
from fastapi import FastAPI, params
from fastapi.testclient import TestClient
from pydantic import BaseModel
from tortoise import Tortoise, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from ms_core.bases.abstract_model import AbstractModel
from ms_core.bases.base_crud import crud_for
from ms_core.bases.base_crud_router import (
    BaseCRUDRouter,
    DefaultEndpoint,
    EndpointConfig,
)


class ItemModel(AbstractModel):
    name = fields.CharField(max_length=50)
    value = fields.IntField(default=0)


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
def item_schemas():
    """Fixture for ItemModel schemas."""
    return {
        "schema": pydantic_model_creator(ItemModel),
        "schema_create": pydantic_model_creator(ItemModel, exclude_readonly=True),
    }


@pytest.fixture
def item_crud(item_schemas):
    """Fixture for ItemModel CRUD instance."""
    return crud_for(ItemModel, item_schemas["schema"])


class TestEndpointConfig:
    """Test EndpointConfig class functionality."""

    def test_to_route_kwargs_basic(self):
        """Test basic kwargs conversion without dependencies."""
        cfg = EndpointConfig(path="/test", methods=["GET"])
        kwargs = cfg.to_route_kwargs()

        assert kwargs["methods"] == ["GET"]
        assert "path" not in kwargs  # Should be excluded
        assert "dependencies" not in kwargs
        assert "response_model" not in kwargs  # None values excluded

    def test_to_route_kwargs_with_all_fields(self):
        """Test kwargs conversion with all possible fields."""

        def dummy_dep():
            pass

        cfg = EndpointConfig(
            path="/test",
            methods=["POST"],
            response_model=dict,
            include_in_schema=False,
            tags=["test"],
            summary="Test endpoint",
            description="Test description",
            deprecated=True,
            dependencies=[dummy_dep],
        )
        kwargs = cfg.to_route_kwargs()

        assert kwargs["methods"] == ["POST"]
        assert kwargs["response_model"] == dict
        assert kwargs["include_in_schema"] is False
        assert kwargs["tags"] == ["test"]
        assert kwargs["summary"] == "Test endpoint"
        assert kwargs["description"] == "Test description"
        assert kwargs["deprecated"] is True
        assert len(kwargs["dependencies"]) == 1
        assert isinstance(kwargs["dependencies"][0], params.Depends)

    def test_to_route_kwargs_excludes_none_values(self):
        """Test that None values are properly excluded."""
        cfg = EndpointConfig(
            path="/test",
            methods=["GET"],
            response_model=None,
            tags=None,
            summary=None,
            description=None,
            dependencies=None,
        )
        kwargs = cfg.to_route_kwargs()

        # All None values should be excluded
        excluded_fields = [
            "response_model",
            "tags",
            "summary",
            "description",
            "dependencies",
        ]
        for field in excluded_fields:
            assert field not in kwargs

        assert kwargs["methods"] == ["GET"]

    def test_dependencies_conversion(self):
        """Test that dependencies are properly converted to Depends objects."""

        def dep1():
            pass

        def dep2():
            pass

        cfg = EndpointConfig(path="/test", methods=["POST"], dependencies=[dep1, dep2])
        kwargs = cfg.to_route_kwargs()

        deps = kwargs["dependencies"]
        assert len(deps) == 2
        assert all(isinstance(dep, params.Depends) for dep in deps)


class TestBaseCRUDRouterConfiguration:
    """Test BaseCRUDRouter configuration options."""

    def test_router_with_specific_endpoints(self, item_schemas, item_crud):
        """Test router with specific endpoints list (hits line 91: else branch)."""
        app = FastAPI()

        # Create router with specific endpoints (not "all")
        router = BaseCRUDRouter(
            crud=item_crud,
            schema=item_schemas["schema"],
            schema_create=item_schemas["schema_create"],
            include_endpoints=[DefaultEndpoint.CREATE, DefaultEndpoint.GET_ITEM],
            prefix="/specific",
        )

        app.include_router(router)
        client = TestClient(app)

        # Test that included endpoints work
        create_resp = client.post("/specific/", json={"name": "test", "value": 42})
        assert create_resp.status_code == 200

        item_id = create_resp.json()["id"]
        get_resp = client.get(f"/specific/{item_id}")
        assert get_resp.status_code == 200

        # Test that excluded endpoint returns 405
        get_all_resp = client.get("/specific/")
        assert get_all_resp.status_code == 405

    def test_custom_endpoint_addition(self, item_schemas, item_crud):
        """Test adding custom endpoints to router."""
        app = FastAPI()

        router = BaseCRUDRouter(
            crud=item_crud,
            schema=item_schemas["schema"],
            schema_create=item_schemas["schema_create"],
        )

        # Add custom endpoint
        class EchoSchema(BaseModel):
            msg: str

        async def echo_handler(payload: EchoSchema):
            return payload

        config = EndpointConfig(
            path="/echo", methods=["POST"], response_model=EchoSchema
        )
        router.add_custom_endpoint(echo_handler, config)

        app.include_router(router)
        client = TestClient(app)

        # Test custom endpoint
        resp = client.post("/echo", json={"msg": "hello"})
        assert resp.status_code == 200
        assert resp.json() == {"msg": "hello"}

    def test_endpoint_configs_override(self, item_schemas, item_crud):
        """Test that endpoint_configs override default configurations."""
        app = FastAPI()

        # Custom config for CREATE endpoint
        custom_create_config = EndpointConfig(
            path="/custom-create",
            methods=["POST"],
            response_model=item_schemas["schema"],
            summary="Custom create endpoint",
        )

        router = BaseCRUDRouter(
            crud=item_crud,
            schema=item_schemas["schema"],
            schema_create=item_schemas["schema_create"],
            include_endpoints=[DefaultEndpoint.CREATE],
            endpoint_configs={DefaultEndpoint.CREATE: custom_create_config},
        )

        app.include_router(router)
        client = TestClient(app)

        # Test that custom path works
        resp = client.post("/custom-create", json={"name": "test", "value": 1})
        assert resp.status_code == 200

        # Test that default path doesn't exist
        default_resp = client.post("/", json={"name": "test", "value": 1})
        assert default_resp.status_code == 404
