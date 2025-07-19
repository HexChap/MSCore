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
