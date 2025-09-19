from enum import Enum
from inspect import signature
from typing import Any, Callable, Literal

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi.params import Security
from makefun import create_function
from pydantic import BaseModel, ConfigDict

from ms_core.bases import CRUD
from ms_core.utils import partial_model


class GetAllResponse[Schema: BaseModel](BaseModel):
    items: list[Schema]
    total: int


class DefaultEndpoint(Enum):
    """Enum for default CRUD endpoints"""

    CREATE = "create"
    GET_ALL = "get_all"
    GET_ITEM = "get_item"
    UPDATE = "update"
    DELETE = "delete"


class EndpointConfig(BaseModel):
    """Configuration for individual endpoints"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str
    methods: list[str]
    response_model: Any = None
    include_in_schema: bool = True
    tags: list[str] | None = None
    summary: str | None = None
    description: str | None = None
    deprecated: bool = False
    dependencies: list[Callable | Security] | None = None

    def to_route_kwargs(self) -> dict:
        """Convert config to kwargs for add_api_route, excluding path and endpoint"""
        config_dict = self.model_dump(exclude={"path"}, exclude_none=True)

        if self.dependencies:
            config_dict["dependencies"] = [
                Depends(dep) if isinstance(dep, Callable) else dep
                for dep in self.dependencies
            ]

        return config_dict


class BaseCRUDRouter[
    Schema: BaseModel,
    SchemaCreate: BaseModel,
    SchemaUpdate: BaseModel,
](APIRouter):
    def __init__(
        self,
        crud: CRUD,
        schema: type[Schema],
        schema_create: type[SchemaCreate],
        schema_update: type[SchemaUpdate] | None = None,
        limit: int = 50,
        offset: int = 0,
        include_endpoints: list[DefaultEndpoint] | Literal["all"] = "all",
        exclude_endpoints: list[DefaultEndpoint] | None = None,
        endpoint_configs: dict[DefaultEndpoint, EndpointConfig] | None = None,
        *args,
        **kwargs,
    ):
        """
        Initializes the BaseCRUDRouter with flexible endpoint configuration.

        Args:
            crud: The CRUD instance to handle the database operations.
            schema: The Pydantic model for reading data.
            schema_create: The Pydantic model for creating data.
            limit: The default number of items to fetch in the get_all endpoint.
            offset: The default offset for fetching items.
            include_endpoints: Which default endpoints to include. Use "all" for all endpoints.
            exclude_endpoints: Which default endpoints to exclude.
            endpoint_configs: Custom configurations for default endpoints.
            *args: Additional arguments for the APIRouter initialization.
            **kwargs: Additional keyword arguments for the APIRouter initialization.
        """
        super().__init__(*args, **kwargs)

        self.crud = crud
        self.schema_create = schema_create
        self.schema = schema
        self.limit = limit
        self.offset = offset

        self.schema_update = (
            schema_update if schema_update else partial_model(schema_create)
        )

        # Determine which endpoints to include
        if include_endpoints == "all":
            endpoints_to_include = set(DefaultEndpoint)
        else:
            endpoints_to_include = set(include_endpoints)

        if exclude_endpoints:
            endpoints_to_include -= set(exclude_endpoints)

        # Build endpoint configurations
        self._build_endpoints(endpoints_to_include, endpoint_configs or {})

    def _get_default_endpoint_config(self, endpoint: DefaultEndpoint) -> EndpointConfig:
        """Get default configuration for a given endpoint"""
        configs = {
            DefaultEndpoint.CREATE: EndpointConfig(
                path="/",
                methods=["POST"],
                response_model=self.schema,
                summary="Create new item",
                description="Create a new item with the provided data",
            ),
            DefaultEndpoint.GET_ALL: EndpointConfig(
                path="/",
                methods=["GET"],
                response_model=GetAllResponse[self.schema],
                summary="Get all items",
                description="Retrieve all items with pagination support",
            ),
            DefaultEndpoint.GET_ITEM: EndpointConfig(
                path="/{item_id}",
                methods=["GET"],
                response_model=self.schema | None,
                summary="Get item by ID",
                description="Retrieve a specific item by its ID",
            ),
            DefaultEndpoint.UPDATE: EndpointConfig(
                path="/{item_id}",
                methods=["PUT"],
                response_model=self.schema | None,
                summary="Update item",
                description="Update an existing item by its ID",
            ),
            DefaultEndpoint.DELETE: EndpointConfig(
                path="/{item_id}",
                methods=["DELETE"],
                response_model=bool,
                summary="Delete item",
                description="Delete an item by its ID",
            ),
        }
        return configs[endpoint]

    def _build_endpoints(
        self,
        endpoints_to_include: set[DefaultEndpoint],
        endpoint_configs: dict[DefaultEndpoint, EndpointConfig],
    ):
        """Build and register all endpoints"""

        # Map of endpoint enum to handler method
        endpoint_handlers = {
            DefaultEndpoint.CREATE: self._create,
            DefaultEndpoint.GET_ALL: self._get_all,
            DefaultEndpoint.GET_ITEM: self._get_item,
            DefaultEndpoint.UPDATE: self._update,
            DefaultEndpoint.DELETE: self._delete_item,
        }

        # Register default endpoints
        for endpoint_type in endpoints_to_include:
            handler = endpoint_handlers[endpoint_type]

            # Use custom config if provided, otherwise use default
            config = endpoint_configs.get(
                endpoint_type
            ) or self._get_default_endpoint_config(endpoint_type)

            # Update handler signature for type safety
            updated_handler = self._update_handler_signature(handler)

            # Register the endpoint
            self.add_api_route(
                path=config.path, endpoint=updated_handler, **config.to_route_kwargs()
            )

    def _update_handler_signature(self, handler: Callable) -> Callable:
        """Update handler signature to use actual schema types"""
        sig = signature(handler)
        params = dict(sig.parameters)
        is_replaced = False

        # Replace schema types
        for name, param in params.items():
            if hasattr(param.annotation, "__name__"):
                match param.annotation.__name__:
                    case "Schema":
                        params[name] = param.replace(annotation=self.schema)
                        is_replaced = True
                    case "SchemaCreate":
                        params[name] = param.replace(annotation=self.schema_create)
                        is_replaced = True
                    case "SchemaUpdate":
                        params[name] = param.replace(annotation=self.schema_update)
                        is_replaced = True

        return (
            create_function(sig.replace(parameters=list(params.values())), handler)
            if is_replaced
            else handler
        )

    # Method to add endpoints after initialization
    def add_custom_endpoint(self, handler: Callable, config: EndpointConfig):
        """Add a custom endpoint after router initialization"""
        updated_handler = self._update_handler_signature(handler)
        self.add_api_route(
            path=config.path, endpoint=updated_handler, **config.to_route_kwargs()
        )

    # Original handler methods remain the same
    async def _create(self, payload: SchemaCreate = Body()) -> Schema:
        """Creates a new item using the provided schema."""
        return await self.crud.create(payload)

    async def _get_all(
        self,
        prefetch: bool = Query(False),
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ) -> GetAllResponse[Schema]:
        """Returns all items in the specified range and total count."""
        return GetAllResponse(
            items=await self.crud.get_all(prefetch, limit, offset),
            total=await self.crud._model.all().count(),
        )

    async def _get_item(self, item_id: int = Path()) -> Schema | None:
        """Fetches a single item by its ID."""
        return await self.crud.get_by_id(item_id)

    async def _update(
        self, payload: SchemaUpdate = Body(), item_id: int = Path()
    ) -> Schema | None:
        """Updates an existing item."""
        return await self.crud.update_by(payload, id=item_id)

    async def _delete_item(self, item_id: int = Path()) -> bool:
        """Deletes an item by its ID."""
        return await self.crud.delete_by(id=item_id)
