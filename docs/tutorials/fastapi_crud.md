# User Guide: CRUD Router Usage

This module provides a dynamic CRUD router for FastAPI,
allowing you to easily create standard API endpoints with minimal boilerplate.

## What does it provide?

A subclass of `fastapi.APIRouter` called `BaseCRUDRouter` that automatically
generates endpoints for:

- Create item
- Get all items
- Get item by id
- Update item by id
- Delete item by id

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

## Auto-generated endpoints

| Method  | Path           | Purpose           |
|---------|----------------|------------------|
| POST    | `/users/`      | Create item      |
| GET     | `/users/`      | List all items   |
| GET     | `/users/{id}`  | Get item by id   |
| PUT     | `/users/{id}`  | Update item      |
| DELETE  | `/users/{id}`  | Delete item      |

## Notes

- `schema` is a Pydantic model for output
- `schema_create` is a Pydantic model for input (create/update)
- Pagination is supported with `limit` and `offset` query parameters on GET all
- Prefetch related models with `prefetch=true`
