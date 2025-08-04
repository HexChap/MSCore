"""Integration tests for BaseCRUDRouter with full CRUD operations."""

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from tortoise import Tortoise, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from ms_core.bases.abstract_model import AbstractModel
from ms_core.bases.base_crud import crud_for
from ms_core.bases.base_crud_router import (
    BaseCRUDRouter,
    DefaultEndpoint,
    EndpointConfig,
)
from tests.conftest import fake_auth


class DemoModel(AbstractModel):
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)


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
def demo_schemas():
    """Fixture for DemoModel schemas."""
    return {
        "schema": pydantic_model_creator(DemoModel),
        "schema_create": pydantic_model_creator(DemoModel, exclude_readonly=True),
    }


@pytest.fixture
def demo_crud(demo_schemas):
    """Fixture for DemoModel CRUD instance."""
    return crud_for(DemoModel, demo_schemas["schema"])


@pytest.fixture
def app(demo_schemas, demo_crud):
    """FastAPI app with multiple router configurations for testing."""
    app = FastAPI()
    schema = demo_schemas["schema"]
    schema_create = demo_schemas["schema_create"]

    # Basic CRUD router at /demo
    app.include_router(
        BaseCRUDRouter(
            crud=demo_crud,
            schema=schema,
            schema_create=schema_create,
            prefix="/demo",
            tags=["demo"],
        )
    )

    # Router with dependency on UPDATE endpoint
    update_cfg = {
        DefaultEndpoint.UPDATE: EndpointConfig(
            path="/{item_id}",
            methods=["PUT"],
            response_model=schema | None,
            dependencies=[fake_auth],
        )
    }
    app.include_router(
        BaseCRUDRouter(
            crud=demo_crud,
            schema=schema,
            schema_create=schema_create,
            prefix="/demo_update",
            include_endpoints="all",
            endpoint_configs=update_cfg,
        )
    )

    # Router excluding DELETE endpoint
    app.include_router(
        BaseCRUDRouter(
            crud=demo_crud,
            schema=schema,
            schema_create=schema_create,
            prefix="/demo_nodelete",
            include_endpoints="all",
            exclude_endpoints=[DefaultEndpoint.DELETE],
        )
    )

    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestBasicCRUDOperations:
    """Test basic CRUD operations on /demo endpoints."""

    def test_create_item(self, client):
        resp = client.post(
            "/demo/", json={"name": "Item1", "description": "Desc1", "is_active": True}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] and data["name"] == "Item1"

    def test_get_item(self, client):
        # Create item first
        post_resp = client.post(
            "/demo/", json={"name": "GetMe", "description": "", "is_active": True}
        )
        item_id = post_resp.json()["id"]

        # Get the item
        get_resp = client.get(f"/demo/{item_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "GetMe"

    def test_get_all_items(self, client):
        # Create test items
        client.post("/demo/", json={"name": "A", "description": "", "is_active": True})
        client.post("/demo/", json={"name": "B", "description": "", "is_active": True})

        # Get all items
        resp = client.get("/demo/")
        assert resp.status_code == 200

        payload = resp.json()
        assert isinstance(payload["items"], list)
        assert payload["total"] >= 2

    def test_update_item(self, client):
        # Create item
        post_resp = client.post(
            "/demo/", json={"name": "Original", "description": "", "is_active": True}
        )
        item_id = post_resp.json()["id"]

        # Update item
        update_resp = client.put(
            f"/demo/{item_id}",
            json={"name": "Updated", "description": "New desc", "is_active": False},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated"

    def test_delete_item(self, client):
        # Create item
        post_resp = client.post(
            "/demo/", json={"name": "DelMe", "description": "", "is_active": True}
        )
        item_id = post_resp.json()["id"]

        # Delete item
        del_resp = client.delete(f"/demo/{item_id}")
        assert del_resp.status_code == 200
        assert del_resp.json() is True

        # Confirm item is gone
        get_resp = client.get(f"/demo/{item_id}")
        assert get_resp.status_code == 200
        assert get_resp.json() is None


class TestRouteConfiguration:
    """Test different router configurations."""

    def test_router_with_dependencies(self, client):
        """Test router with dependencies on UPDATE endpoint."""
        # Create item
        post_resp = client.post(
            "/demo_update/",
            json={"name": "TestAuth", "description": "", "is_active": True},
        )
        item_id = post_resp.json()["id"]

        # Update should work normally (fake_auth allows by default)
        update_resp = client.put(
            f"/demo_update/{item_id}",
            json={"name": "Updated", "description": "", "is_active": False},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Updated"

    def test_dependency_blocks_update(self, client, app):
        """Test that dependency can block access to endpoint."""
        # Override fake_auth to raise HTTP 403
        app.dependency_overrides[fake_auth] = lambda: (_ for _ in ()).throw(
            HTTPException(status_code=403)
        )

        # Create item
        post_resp = client.post(
            "/demo_update/", json={"name": "Auth", "description": "", "is_active": True}
        )
        item_id = post_resp.json()["id"]

        # Update should be blocked
        blocked_resp = client.put(
            f"/demo_update/{item_id}",
            json={"name": "Fail", "description": "", "is_active": False},
        )
        assert blocked_resp.status_code == 403

        # Clean up override
        app.dependency_overrides.pop(fake_auth, None)

    def test_excluded_endpoint(self, client):
        """Test that excluded endpoints return 405 Method Not Allowed."""
        # Create item
        post_resp = client.post(
            "/demo_nodelete/", json={"name": "ND", "description": "", "is_active": True}
        )
        item_id = post_resp.json()["id"]

        # DELETE should not be available
        resp = client.delete(f"/demo_nodelete/{item_id}")
        assert resp.status_code == 405
