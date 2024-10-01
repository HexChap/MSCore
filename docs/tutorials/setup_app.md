[`ms_core.setup_app`][1] function configures TortoiseORM to work with 
FastAPI, registers Tortoise models and includes `fastapi.APIRouter`s to the provided 
FastAPI instance. Doing these action separately is possible by using 
[`ms_core.setup.conf_db`][2] and [`ms_core.setup.include_routers`][3]

## Folder layout

This tutorial implies specific folder layout. Following example have `main.py` and `app` directory
in their root. `app` directory contains `routers` and `models.py`
```
├── main.py
├── app
│   ├── routers
│   │   ├── users.py
│   ├── models.py
```

## Create a model

Create a file named `models.py` in the `app` directory. Inside the file place model named `User`

```python
from tortoise import Model
from tortoise import fields


class User(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=32)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "users"
```

## Create a router

Create `routers` in `app` directory. Inside it place `users.py` with a router and some route:

```python
from fastapi import APIRouter

from app.models import User

router = APIRouter(prefix="/users/", tags=["users"])


@router.get("/{id_}")
async def get_by_id(id_: int):
    return await User.get_or_none(id=id_)
```

## Setup app

Create a file named `main.py` in the root directory with:

```python
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from ms_core import setup_app

application = FastAPI()

setup_app(
    application,
    "sqlite:///:memory:",
    Path("app") / "routers",
    ["app.models"]  # module path to a file containing models
)

if __name__ == "__main__":
    uvicorn.run("main:application", port=8000, reload=True)
```

[1]: /reference/setup#ms_core.setup.setup_app
[2]: /reference/setup#ms_core.setup.conf_db
[3]: /reference/setup#ms_core.setup.include_routers