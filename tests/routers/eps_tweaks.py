from ms_core import (
    BaseCRUDRouter,
    DefaultEndpoint,
    EndpointConfig,
)
from tests.cruds.crud1 import Test1CRUD, Test1Create, Test1Schema

router = BaseCRUDRouter[Test1Schema, Test1Create](
    crud=Test1CRUD,
    schema=Test1Schema,
    schema_create=Test1Create,
    include_endpoints=[
        DefaultEndpoint.CREATE,
        DefaultEndpoint.GET_ALL,
        DefaultEndpoint.GET_ITEM,
        DefaultEndpoint.UPDATE,
    ],
    endpoint_configs={
        DefaultEndpoint.CREATE: EndpointConfig(
            path="/create-item",
            methods=["POST"],
            summary="Create Test Item",
            description="Create a new test item with validation",
            tags=["creation", "validation"],
        ),
        DefaultEndpoint.GET_ALL: EndpointConfig(
            path="/search",
            methods=["GET"],
            summary="Search Test Items",
            description="Search and paginate through test items",
            tags=["search"],
        ),
        DefaultEndpoint.GET_ITEM: EndpointConfig(
            path="/details/{item_id}",
            methods=["GET"],
            summary="Get Item Details",
            description="Retrieve detailed information about a specific item",
        ),
    },
    prefix="/eps-tweaks",
    tags=["eps-tweaks"],
    limit=25,  # Custom default limit
    offset=0,
)


@router.get("/custom")
async def custom_foo():
    return "custom"
