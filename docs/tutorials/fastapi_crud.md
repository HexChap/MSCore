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

## Adding Dependencies

You can add FastAPI dependencies to any endpoint using the `dependencies` field in `EndpointConfig`:

```python
from fastapi import Depends
from ms_core.routers import BaseCRUDRouter, DefaultEndpoint, EndpointConfig

# Define your dependency functions
def get_current_user():
    return {"user_id": 123, "username": "john_doe"}

def admin_required():
    return {"is_admin": True}

def validate_permissions():
    # Your validation logic here
    return True

router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=User,
    schema_create=UserCreate,
    endpoint_configs={
        # Require authentication for create operations
        DefaultEndpoint.CREATE: EndpointConfig(
            path="/",
            methods=["POST"],
            dependencies=[get_current_user, admin_required]
        ),
        # Only authentication for read operations
        DefaultEndpoint.GET_ALL: EndpointConfig(
            path="/",
            methods=["GET"],
            dependencies=[get_current_user]
        ),
        # Multiple dependencies for sensitive operations
        DefaultEndpoint.DELETE: EndpointConfig(
            path="/{item_id}",
            methods=["DELETE"],
            dependencies=[get_current_user, admin_required, validate_permissions]
        )
    },
    prefix="/users",
    tags=["users"]
)
```

## Custom Endpoints with Dependencies

You can also add custom endpoints after router initialization:

```python
from fastapi import Path
from ms_core.routers import EndpointConfig

async def get_user_profile(user_id: int = Path(...)):
    # Your custom logic here
    return {"profile": "data"}

# Add custom endpoint with dependencies
router.add_custom_endpoint(
    handler=get_user_profile,
    config=EndpointConfig(
        path="/profile/{user_id}",
        methods=["GET"],
        summary="Get user profile", 
        description="Get detailed user profile information",
        dependencies=[get_current_user]  # Require authentication
    )
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

Note: Paths will be prefixed with the router's `prefix` setting.

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

* `limit`: Number of items to return (default: 50, min: 1, max: 100)
* `offset`: Number of items to skip (default: 0, min: 0)
* `prefetch`: Whether to prefetch related models (default: false)

## Complete Example with Dependencies

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from ms_core.routers import BaseCRUDRouter, DefaultEndpoint, EndpointConfig
from app.models import User, UserCreate
from app.cruds import UserCRUD

app = FastAPI()
security = HTTPBearer()

# Authentication dependency
async def get_current_user(token: str = Depends(security)):
    # Your token validation logic
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user_id": 123, "username": "john_doe"}

# Admin permission dependency  
async def require_admin(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin required")
    return current_user

# Customized CRUD router with dependencies
router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=User,
    schema_create=UserCreate,
    endpoint_configs={
        # Public read access
        DefaultEndpoint.GET_ALL: EndpointConfig(
            path="/",
            methods=["GET"],
            summary="List users",
            description="Get paginated list of users"
        ),
        DefaultEndpoint.GET_ITEM: EndpointConfig(
            path="/{item_id}",
            methods=["GET"],
            summary="Get user",
            description="Get user by ID"
        ),
        # Authenticated write operations
        DefaultEndpoint.CREATE: EndpointConfig(
            path="/",
            methods=["POST"],
            summary="Create user",
            description="Create a new user account",
            dependencies=[get_current_user]
        ),
        DefaultEndpoint.UPDATE: EndpointConfig(
            path="/{item_id}",
            methods=["PUT"],
            summary="Update user", 
            description="Update existing user",
            dependencies=[get_current_user]
        ),
        # Admin-only operations
        DefaultEndpoint.DELETE: EndpointConfig(
            path="/{item_id}",
            methods=["DELETE"],
            summary="Delete user",
            description="Delete user (admin only)",
            dependencies=[require_admin]
        )
    },
    prefix="/users",
    tags=["users"],
    limit=25  # Default page size
)

app.include_router(router)
```

This creates a fully configured CRUD API with:

* Public read endpoints (no authentication required)
* Authenticated write endpoints (user token required)
* Admin-only delete endpoint (admin permissions required)
* Proper OpenAPI documentation with security schemes

## Notes

* `schema` is a Pydantic model for output responses
* `schema_create` is a Pydantic model for input (create/update operations)
* Dependencies are applied using FastAPI's native dependency injection system
* All endpoints support full OpenAPI documentation generation
* Type safety is maintained through dynamic signature replacement
* Dependencies are processed by FastAPI's `add_api_route` method, ensuring proper dependency injection
