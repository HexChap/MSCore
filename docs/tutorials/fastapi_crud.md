# User Guide: CRUD Router Usage

This module provides a dynamic CRUD router for FastAPI, allowing you to
easily create standard API endpoints with minimal boilerplate
and flexible endpoint configuration.

## What does it provide?

A subclass of `fastapi.APIRouter` called `BaseCRUDRouter` that automatically
generates endpoints for:

* Create item
* Get all items
* Get item by id
* Update item by id
* Delete item by id

## Basic Usage

```python
from fastapi import FastAPI
from app.models import User, UserCreate
from ms_core.routers import BaseCRUDRouter
from ms_core.bases import BaseCRUD

app = FastAPI()

class UserCRUD(BaseCRUD):
    model = User

# Basic router with all default endpoints
router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=User,         # Read schema
    schema_create=UserCreate,  # Create/update schema
    prefix="/users",
    tags=["users"]
)

app.include_router(router)
```

## Endpoint Selection

You can control which endpoints are included or excluded:

### Include specific endpoints only

```python
from ms_core.routers import BaseCRUDRouter, DefaultEndpoint

# Only create and get endpoints
router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=User,
    schema_create=UserCreate,
    include_endpoints=[DefaultEndpoint.CREATE, DefaultEndpoint.GET_ALL],
    prefix="/users",
    tags=["users"]
)
```

### Exclude specific endpoints

```python
# All endpoints except delete
router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=User,
    schema_create=UserCreate,
    exclude_endpoints=[DefaultEndpoint.DELETE],
    prefix="/users",
    tags=["users"]
)
```

## Customizing Endpoint Configuration

You can customize individual endpoints using the `endpoint_configs` parameter:

```python
from ms_core.routers import BaseCRUDRouter, DefaultEndpoint, EndpointConfig

router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=User,
    schema_create=UserCreate,
    endpoint_configs={
        DefaultEndpoint.CREATE: EndpointConfig(
            path="/create-user",
            methods=["POST"],
            summary="Create a new user account",
            description="Creates a new user with the provided information",
            tags=["user-management"]
        ),
        DefaultEndpoint.GET_ALL: EndpointConfig(
            path="/list",
            methods=["GET"],
            summary="List all users",
            description="Retrieve paginated list of all users",
            deprecated=False
        )
    },
    prefix="/users",
    tags=["users"]
)
```

## Path Prefix

Use `path_prefix` to add a common prefix to all endpoint paths:

```python
router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=User,
    schema_create=UserCreate,
    path_prefix="/api/v1/users",  # All paths will start with this
    tags=["users"]
)
```

## Auto-generated Endpoints

By default, the following endpoints are created:

| Method | Path          | Purpose        |
| ------ | ------------- | -------------- |
| POST   | `/`           | Create item    |
| GET    | `/`           | List all items |
| GET    | `/{item_id}`  | Get item by id |
| PUT    | `/{item_id}`  | Update item    |
| DELETE | `/{item_id}`  | Delete item    |

Note: Paths will be prefixed with the router's `prefix` and `path_prefix` settings.

## Response Models

### Single Item Responses

Most endpoints return the schema model directly or `None` for optional responses.

### List Response

The `get_all` endpoint returns a structured response:

```python
{
    "items": [/* array of schema objects */],
    "total": 150  // total count of items
}
```

## Query Parameters

### Get All Endpoint

* `limit`: Number of items to return (default: 50, max: 100)
* `offset`: Number of items to skip (default: 0)
* `prefetch`: Whether to prefetch related models (default: false)

## Complete Example

```python
from fastapi import FastAPI
from ms_core.routers import BaseCRUDRouter, DefaultEndpoint, EndpointConfig
from app.models import User, UserCreate
from app.cruds import UserCRUD

app = FastAPI()

# Customized CRUD router
router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=User,
    schema_create=UserCreate,
    # Only include read operations
    include_endpoints=[
        DefaultEndpoint.GET_ALL, 
        DefaultEndpoint.GET_ITEM
    ],
    # Custom configuration for list endpoint
    endpoint_configs={
        DefaultEndpoint.GET_ALL: EndpointConfig(
            path="/list",
            methods=["GET"],
            summary="Get user list",
            description="Retrieve a paginated list of users"
        )
    },
    path_prefix="/api/v1/users",
    tags=["users"],
    limit=25  # Default page size
)

app.include_router(router)
```

This creates:

* `GET /api/v1/users/list` → List users with pagination
* `GET /api/v1/users/{item_id}` → Get specific user

## Notes

* `schema` is a Pydantic model for output responses
* `schema_create` is a Pydantic model for input (create/update operations)
* All endpoints support full OpenAPI documentation generation
* Type safety is maintained through dynamic signature replacement
