# User Guide: CRUD Router Usage

This module provides a dynamic CRUD router for FastAPI,
allowing you to easily create standard API endpoints with minimal boilerplate.

## What does it provide?

A subclass of `fastapi.APIRouter` called `BaseCRUDRouter` that automatically
generates endpoints for:

* Create item
* Get all items
* Get item by id
* Update item by id
* Delete item by id

## Example usage

```python
from fastapi import FastAPI
from app.models import User, UserCreate
from ms_core.routers import BaseCRUDRouter
from ms_core.bases import BaseCRUD

app = FastAPI()

class UserCRUD(BaseCRUD):
    model = User

router = BaseCRUDRouter(
    crud=UserCRUD,
    schema=User,         # Read schema
    schema_create=UserCreate,  # Create/update schema
    prefix="/users",
    tags=["users"]
)

app.include_router(router)
```

## Overriding Endpoints

You can override the default endpoints by passing a custom `endpoints` dictionary.
Each key is a callable (e.g. a custom handler function), and each value is
a dict that defines the route's `path`, `methods`, and `response_model`.

### Example

```python
from ms_core import BaseCRUDRouter
from tests.cruds.crud1 import Test1CRUD, Test1Create, Test1Schema

async def hello():
    return {"msg": "hi"}

router = BaseCRUDRouter[Test1Schema, Test1Create](
    crud=Test1CRUD,
    schema=Test1Schema,
    schema_create=Test1Create,
    prefix="/eps-override",
    tags=["eps-override"],
    endpoints={hello: {"path": "/hi", "methods": ["GET"], "response_model": dict}},
)
```

This will add a new endpoint:

* `GET /eps-override/hi` → returns `{"msg": "hi"}`

## Auto-generated endpoints

| Method | Path          | Purpose        |
| ------ | ------------- | -------------- |
| POST   | `/users/`     | Create item    |
| GET    | `/users/`     | List all items |
| GET    | `/users/{id}` | Get item by id |
| PUT    | `/users/{id}` | Update item    |
| DELETE | `/users/{id}` | Delete item    |

## Notes

* `schema` is a Pydantic model for output
* `schema_create` is a Pydantic model for input (create/update)
* Pagination is supported with `limit` and `offset` query parameters on GET all
* Prefetch related models with `prefetch=true`
