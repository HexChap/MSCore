# Contributor Guide: Design of BaseCRUDRouter

This document explains the internal design and key decisions
behind the `BaseCRUDRouter` implementation.

## Goals

- Auto-generate standard CRUD endpoints
- Minimal boilerplate for users
- Safe and type-correct endpoint signatures

## Key Design Points

### Multi-method API via `BaseCRUD`

This router relies on a `crud` object based on `BaseCRUD` abstraction,
which provides methods like:

- `create`
- `get_all`
- `get_by_id`
- `update_by`
- `delete_by`

This separation enforces SRP (Single Responsibility Principle) and allows
easy swapping or customizing of storage logic.

### Dynamic Signature Replacement

Pydantic generic models (like `Schema`, `SchemaCreate`) are passed to the router.
To ensure FastAPI/OpenAPI generates correct docs and validations, endpoint signatures
are dynamically replaced using:

```python
from makefun import create_function
```

Method `_set_actual_schemas` inspects the method signature using `inspect.signature`
and replaces type annotations for parameters where a
placeholder (`Schema`, `SchemaCreate`) was used.

This guarantees correct typing in route definitions without forcing
inheritance or metaclass hacks.

### Endpoint Registration

All routes are registered in a declarative dict in `__init__`:

```python
endpoints = {
    self.create: {"path": "/", "methods": ["POST"], ...},
    self.get_all: {"path": "/", "methods": ["GET"], ...},
    ...
}
```

This enables clean, transparent route mapping.

### Generic Response Models

List responses use a wrapper model:

```python
class GetAllResponse[Schema: BaseModel](BaseModel):
    items: list[Schema]
    total: int
```

It provides standard pagination responses while retaining schema typing.
