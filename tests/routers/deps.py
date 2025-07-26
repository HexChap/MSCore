from fastapi import HTTPException, Query
from ms_core import BaseCRUDRouter
from ms_core.bases.base_crud_router import DefaultEndpoint, EndpointConfig
from tests.cruds.crud2 import Test2CRUD, Test2Create, Test2Schema


async def get_user_profile(user_id: int = Query()):
    # Your custom logic here
    if user_id != 1:
        raise HTTPException(401, "Only user_id=1 is allowed")
    return {"profile_id": user_id}


router = BaseCRUDRouter[Test2Schema, Test2Create](
    crud=Test2CRUD,
    schema=Test2Schema,
    schema_create=Test2Create,
    prefix="/deps",
    tags=["deps"],
    endpoint_configs={
        DefaultEndpoint.GET_ALL: EndpointConfig(
            path="/test",
            methods=["GET"],
            summary="Test dependency inject",
            dependencies=[get_user_profile],
        ),
    },
)
