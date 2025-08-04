# CRUD Operations

`ms_core.bases.CRUD` provides a generic CRUD interface for TortoiseORM models. It defines common database operations such as create, get, update, and delete through an instance-based approach.

[`ms_core.bases.I18nCRUD`][2] extends `CRUD` to support internationalization (i18n) models by enabling language-specific data fetching through method overloads.

## Design overview

`CRUD` is designed to reduce boilerplate and enforce consistency when interacting with database models. It provides out-of-the-box support for:

- Creating records
- Fetching records (single / multiple / with filters)
- Updating records
- Deleting records

The class uses generics to provide type safety and is instantiated with a model and schema pair, rather than using class inheritance.

Additionally, `I18nCRUD` uses method overloads to support clean language-aware queries for internationalized models without modifying the base implementation or using fragile conditionals.

---

## Folder layout

This tutorial assumes the following folder layout. For example, the root contains `main.py` and an `app` directory. The `app` directory contains `models.py` and `crud` for CRUD logic.

```
├── main.py
├── app
│   ├── crud
│   │   ├── user.py
│   ├── models.py
```

---

## Create a model

Create `models.py` inside `app`:

```python
from tortoise import fields
from ms_core import AbstractModel, I18nModel

class User(AbstractModel):
    name = fields.CharField(max_length=32)

    class Meta:
        table = "users"

class UserI18n(I18nModel):  # I18nModel already has tuple_lang field
    name = fields.CharField(max_length=32)

    class Meta:
        table = "users_i18n"
```

---

## Create CRUD instance

Create `crud/user.py` with CRUD logic:

```python
from tortoise.contrib.pydantic import pydantic_model_creator
from ms_core.bases import CRUD, I18nCRUD, crud_for, i18n_crud_for
from app.models import User, UserI18n

UserSchema = pydantic_model_creator(User)
UserI18nSchema = pydantic_model_creator(UserI18n)

# Regular CRUD
# Method 1: Direct instantiation
user_crud = CRUD(User, UserSchema)

# Method 2: Factory function (recommended)
user_crud = crud_for(User, UserSchema)

# I18n CRUD
# Method 1: Direct instantiation
user_i18n_crud = I18nCRUD(UserI18n, UserI18nSchema)

# Method 2: Factory function (recommended)
user_i18n_crud = i18n_crud_for(UserI18n, UserI18nSchema)
```

---

## Using CRUD operations

### Basic operations

```python
# Create a new user
user_data = UserSchema(name="John Doe")
new_user = await user_crud.create(user_data)

# Get user by ID
user = await user_crud.get_by_id(1)

# Get user by custom filter
user = await user_crud.get_by(name="John Doe")

# Get or create
user, created = await user_crud.get_or_create(name="Jane Doe")

# Update user
updated_data = {"name": "John Smith"}
updated_user = await user_crud.update_by(updated_data, id=1)

# Delete user
success = await user_crud.delete_by(id=1)
```

### I18n operations

```python
# Get user by ID for specific language
user_en = await user_i18n_crud.get_by_id(1, lang="en")
user_es = await user_i18n_crud.get_by_id(1, lang="es")

# Get user by ID without language filter (returns any language)
user = await user_i18n_crud.get_by_id(1)

# Get all users for specific language
users_en = await user_i18n_crud.get_all(lang="en", limit=10)

# Get all users without language filter
all_users = await user_i18n_crud.get_all(limit=10)
```

### Querying multiple records

```python
# Get all users with pagination
users = await user_crud.get_all(limit=10, offset=0)

# Get all users with additional filters
active_users = await user_crud.get_all(is_active=True, limit=20)

# Filter users by criteria
filtered_users = await user_crud.filter_by(name__icontains="John")
```

### Performance optimization

The `get_all` method supports a `prefetch` parameter:

```python
# Fast loading (uses model_construct, no ORM relationships)
users = await user_crud.get_all(prefetch=False)

# Full ORM loading (slower but includes relationships)
users = await user_crud.get_all(prefetch=True)
```

---

## Use CRUD in router

Example `app/routers/users.py`:

```python
from fastapi import APIRouter, HTTPException
from app.crud.user import user_crud, user_i18n_crud

router = APIRouter(prefix="/users", tags=["users"])

# Regular CRUD endpoints
@router.get("/{id_}")
async def get_user(id_: int):
    user = await user_crud.get_by_id(id_)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# I18n CRUD endpoints
@router.get("/{id_}/i18n")
async def get_user_i18n(id_: int, lang: str | None = None):
    if lang:
        user = await user_i18n_crud.get_by_id(id_, lang=lang)
    else:
        user = await user_i18n_crud.get_by_id(id_)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

See also: [Even less boilerplate with BaseRouterCRUD](tutorials/fastapi_crud)

---

## Custom CRUD classes

If you need custom behavior, you can extend the CRUD classes:

```python
from ms_core.bases import CRUD, I18nCRUD
from app.models import User, UserI18n

class UserCRUD(CRUD[User, UserSchema]):
    def __init__(self):
        super().__init__(User, UserSchema)
    
    async def get_active_users(self) -> list[UserSchema]:
        return await self.filter_by(is_active=True)
    
    async def deactivate_user(self, id_: int) -> UserSchema | None:
        return await self.update_by({"is_active": False}, id=id_)

class UserI18nCRUD(I18nCRUD[UserI18n, UserI18nSchema]):
    def __init__(self):
        super().__init__(UserI18n, UserI18nSchema)
    
    async def get_active_users_by_lang(self, lang: str) -> list[UserI18nSchema]:
        return await self.get_all(lang=lang, is_active=True)

# Usage
user_crud = UserCRUD()
user_i18n_crud = UserI18nCRUD()

active_users = await user_crud.get_active_users()
active_spanish_users = await user_i18n_crud.get_active_users_by_lang("es")
```

---

## Notes on Method Overloading

`I18nCRUD` uses Python's `@overload` decorator to provide type-safe method signatures for both language-aware and language-agnostic queries:

```python
# Without language filter
user = await user_i18n_crud.get_by_id(1)

# With language filter
user_en = await user_i18n_crud.get_by_id(1, lang="en")
```

This pattern provides clean, type-safe APIs without mixing all possible method variations into a single method with complex conditionals.

---

<!-- [1]: ../../reference/bases#ms_core.bases.CRUD -->
[2]: ../../reference/tortoise_cruds/#ms_core.bases.i18n_crud.I18nCRUD
