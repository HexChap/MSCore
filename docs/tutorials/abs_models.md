## Abstract Models in `ms_core`

`ms_core.models` provides base abstract models designed to standardize common fields across your TortoiseORM models.

These abstract models are not meant to be used directly. Instead, inherit from them when defining your own models to automatically include common fields like `id` and `created_at`.

## Design Motivation

Defining these abstract models helps to:

- Ensure consistency across database tables.
- Reduce duplication of common field declarations.
- Provide a clean, extendable structure for future shared fields (like `updated_at` or `is_deleted`).

---

## Available Abstract Models

### `AbstractModel`
Located in: `ms_core.models`

Base model that provides:

| Field       | Type        | Description                        |
|-------------|-------------|------------------------------------|
| id          | IntField    | Primary key auto-increment field.  |
| created_at  | DatetimeField | Auto-populated creation timestamp. |

```python
from tortoise import Model, fields

class AbstractModel(Model):
    """ Abstract Tortoise model, containing essential fields. """

    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True
```

---

## Usage Example

### Folder Layout

```
├── main.py
├── app
│   ├── models.py
```

### Define Your Model

```python
from ms_core import AbstractModel
from tortoise import fields

class User(AbstractModel):
    name = fields.CharField(max_length=32)

    class Meta:
        table = "users"
```

By inheriting from `AbstractModel` you automatically get the `id` and `created_at` fields.

---

> Note: Always declare `Meta.abstract = True` in abstract models to prevent them from creating their own database tables.

