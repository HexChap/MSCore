[`ms_core.bases.BaseCRUD`][1] provides an abstract generic CRUD interface for TortoiseORM models. It defines common database operations such as create, get, update, and delete.

[`ms_core.bases.I18nCRUD`][2] extends `BaseCRUD` to support internationalization (i18n) models by enabling language-specific data fetching through method overloading with `multimethod`.

## Design overview

`BaseCRUD` is designed to reduce boilerplate and enforce consistency when interacting with database models. It provides out-of-the-box support for:

- Creating records
- Fetching records (single / multiple / with filters)
- Updating records
- Deleting records

Additionally, the code uses [`multimethod`][3] to support clean method overloading. This enables subclassing to provide specialized behavior (such as language-aware queries) without modifying the base implementation or using fragile conditionals.

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

class UserI18n(I18nModel):  # I18n abstract model already have tuple_lang field
    name = fields.CharField(max_length=32)

    class Meta:
        table = "users_i18n"
---

## Create CRUD class

Create `crud/user.py` with CRUD logic:

```python
from ms_core.bases import BaseCRUD
from app.models import User
from tortoise.contrib.pydantic import pydantic_model_creator

UserSchema = pydantic_model_creator(User)

class UserCRUD(BaseCRUD[User, UserSchema]):
    model = User
    schema = UserSchema
```

For multilingual models, inherit from `I18nCRUD`:

```python
from tortoise.contrib.pydantic import pydantic_model_creator
from ms_core.bases import I18nCRUD

from app.models import UserI18n

UserSchema = pydantic_model_creator(UserI18n)


class UserI18nCRUD(I18nCRUD[UserI18n, UserSchema]):
    model = UserI18n
    schema = UserSchema
```

---

## Extending and modifying your CRUD

Using the inheritance design, we have the ability to naturally create new CRUD methods or overload already existing ones.

```python
class UserCRUD(BaseCRUD[User, UserSchema]):
    model = User
    schema = UserSchema
    
    async def get_by_id(cls, id_: int) -> UserSchema:
        print("Muhehehe")
        
        return cls.get_by_id(id_=id_)

    async def get_unused(cls) -> list[UserSchema]:
        return await cls.filter_by(is_used=False)
```

## Use CRUD in router

Example `app/routers/users.py`:

```python
from fastapi import APIRouter
from app.crud.user import UserCRUD

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{id_}")
async def get_user(id_: int):
    return await UserCRUD.get_by_id(id_)
```

For i18n CRUD:

```python
@router.get("/{id_}/i18n")
async def get_user_i18n(id_: int, lang: str):
    return await UserI18nCRUD.get_by_id(id_, lang=lang)
```

---

## Notes on `multimethod`

We use [`multimethod`][3] to overload methods based on parameters. This allows context-aware logic (e.g., fetching by ID with language filters) without sacrificing clarity or maintainability.

For example:

```python
class I18nCRUD(BaseCRUD):

    @BaseCRUD.get_by_id.register
    async def get_by_id(cls, id_: int, lang: str):
        return await cls.get_by(id=id_, tuple_lang=lang)
```

This pattern avoids mixing all possible method variations into a single method with `if`/`else` conditions.

---

[1]: /reference/bases#ms_core.bases.BaseCRUD
[2]: /reference/bases#ms_core.bases.I18nCRUD
[3]: https://github.com/coady/multimethod

