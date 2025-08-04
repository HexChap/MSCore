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
from tortoise.contrib.pydantic import pydantic_model_creator
from ms_core.routers import BaseCRUDRouter
from ms_core.bases import crud_for
from app.models import User

app = FastAPI()

# Create schemas
User_Pydantic = pydantic_model_creator(User, name="User")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)

# Create CRUD instance
user_crud = crud_for(User, User_Pydantic)

# Basic router with all default endpoints
router = BaseCRUDRouter(
    crud=user_crud,
    schema=User_Pydantic,         # Read schema
    schema_create=UserIn_Pydantic,  # Create/update schema
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
    crud=user_crud,
    schema=User_Pydantic,
    schema_create=UserIn_Pydantic,
    include_endpoints=[DefaultEndpoint.CREATE, DefaultEndpoint.GET_ALL],
    prefix="/users",
    tags=["users"]
)
```

### Exclude specific endpoints

```python
# All endpoints except delete
router = BaseCRUDRouter(
    crud=user_crud,
    schema=User_Pydantic,
    schema_create=UserIn_Pydantic,
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
    crud=user_crud,
    schema=User_Pydantic,
    schema_create=UserIn_Pydantic,
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
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from ms_core.routers import BaseCRUDRouter, DefaultEndpoint, EndpointConfig

security = HTTPBearer()

# Define your dependency functions
async def get_current_user(token: str = Depends(security)):
    # Your token validation logic
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user_id": 123, "username": "john_doe"}

async def admin_required(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin required")
    return current_user

def validate_permissions():
    # Your validation logic here
    return True

router = BaseCRUDRouter(
    crud=user_crud,
    schema=User_Pydantic,
    schema_create=UserIn_Pydantic,
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
from fastapi import Path, Depends
from ms_core.routers import EndpointConfig

@router.get("/profile/{user_id}", dependecies=[Depends(get_current_user)])
async def get_user_profile(user_id: int = Path(...)):
    # Your custom logic here
    user = await user_crud.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"profile": user, "additional_data": "..."}
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

## Integration with I18n CRUD

For internationalized models, you can use the router with `I18nCRUD`:

```python
from ms_core.bases import i18n_crud_for
from app.models import UserI18n

# Create I18n CRUD instance
user_i18n_crud = i18n_crud_for(UserI18n, UserI18n_Pydantic)

# Custom handler for language-aware endpoints
async def get_user_by_lang(user_id: int = Path(...), lang: str = Query(...)):
    return await user_i18n_crud.get_by_id(user_id, lang=lang)

router = BaseCRUDRouter(
    crud=user_i18n_crud,
    schema=UserI18n_Pydantic,
    schema_create=UserI18nIn_Pydantic,
    prefix="/users",
    tags=["users"]
)

# Add custom language-aware endpoint
router.add_custom_endpoint(
    handler=get_user_by_lang,
    config=EndpointConfig(
        path="/by-lang/{user_id}",
        methods=["GET"],
        summary="Get user by language",
        description="Get user data for specific language"
    )
)
```

## Complete Example with Dependencies

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from tortoise.contrib.pydantic import pydantic_model_creator
from ms_core.routers import BaseCRUDRouter, DefaultEndpoint, EndpointConfig
from ms_core.bases import crud_for
from app.models import User

app = FastAPI()
security = HTTPBearer()

# Create schemas
User_Pydantic = pydantic_model_creator(User, name="User")
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)

# Create CRUD instance
user_crud = crud_for(User, User_Pydantic)

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
    crud=user_crud,
    schema=User_Pydantic,
    schema_create=UserIn_Pydantic,
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
