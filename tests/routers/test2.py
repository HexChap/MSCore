from ms_core import BaseCRUDRouter
from tests.cruds.crud2 import Test2CRUD, Test2Schema, Test2Create

router = BaseCRUDRouter[Test2Schema, Test2Create](
    crud=Test2CRUD,
    schema=Test2Schema,
    schema_create=Test2Create,
    prefix="/test2",
    tags=["test2"]
)
