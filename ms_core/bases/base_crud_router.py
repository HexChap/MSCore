from inspect import signature
from typing import Callable

from fastapi import APIRouter, Path, Query, Body
from makefun import create_function
from pydantic import BaseModel

from ms_core.bases import BaseCRUD


class GetAllResponse[Schema: BaseModel](BaseModel):
    items: list[Schema]
    total: int


class BaseCRUDRouter[
    Schema: BaseModel,
    SchemaCreate: BaseModel
](APIRouter):
    """
    A router that dynamically generates CRUD endpoints based on provided schemas and CRUD class.

    Args:
        crud: The CRUD class to handle the database operations.
        schema: The Pydantic model for reading data.
        schema_create: The Pydantic model for creating data.
        limit: The default number of items to fetch in the get_all endpoint.
        offset: The default offset for fetching items.
        *args: Additional arguments for the APIRouter initialization.
        **kwargs: Additional keyword arguments for the APIRouter initialization.
    """

    def __init__(
        self,
        crud: type[BaseCRUD],
        schema: type[Schema],
        schema_create: type[SchemaCreate],
        limit: int = 50,
        offset: int = 0,
        *args,
        **kwargs
    ):
        """
        Initializes the BaseCRUDRouter with the provided CRUD class and schemas.

        Args:
            crud: The CRUD class to handle the database operations.
            schema: The Pydantic model for reading data.
            schema_create: The Pydantic model for creating data.
            limit: The default number of items to fetch in the get_all endpoint.
            offset: The default offset for fetching items.
            *args: Additional arguments for the APIRouter initialization.
            **kwargs: Additional keyword arguments for the APIRouter initialization.
        """
        super().__init__(*args, **kwargs)

        self.crud = crud
        self.schema_create = schema_create
        self.schema = schema

        self.limit = limit
        self.offset = offset

        endpoints = {
            self.create: {
                "path": "/",
                "methods": ["POST"],
                "response_model": schema
            },
            self.get_all: {
                "path": "/",
                "methods": ["GET"],
                "response_model": GetAllResponse[schema]
            },
            self.get_item: {
                "path": "/{item_id}",
                "methods": ["GET"],
                "response_model": schema | None
            },
            self.update: {
                "path": "/{item_id}",
                "methods": ["PUT"],
                "response_model": schema | None
            },
            self.delete_item: {
                "path": "/{item_id}",
                "methods": ["DELETE"],
                "response_model": bool
            }
        }
        self.endpoints = self._set_actual_schemas(endpoints)

        for ep, info in self.endpoints.items():
            self.add_api_route(endpoint=ep, **info)

    def _set_actual_schemas(self, endpoints: dict[Callable, dict]) -> dict[Callable, dict]:
        """
        Updates endpoint schemas to use the actual provided schema classes.

        Args:
            endpoints: A dictionary mapping endpoint functions to their route information.

        Returns:
            A dictionary with updated endpoints, where the schemas are replaced with actual types.
        """
        new_eps = {}
        for ep, _ in endpoints.items():
            sig = signature(ep)
            params = dict(sig.parameters)
            is_replaced = True

            for name, param in params.items():
                match param.annotation.__name__:
                    case "Schema":
                        params[name] = param.replace(annotation=self.schema)
                        break
                    case "SchemaCreate":
                        params[name] = param.replace(annotation=self.schema_create)
                        break
                    case _:
                        is_replaced = False

            new_ep = create_function(
                sig.replace(parameters=list(params.values())), ep
            ) if is_replaced else ep

            new_eps[new_ep] = endpoints[ep]

        return new_eps

    async def create(self, payload: SchemaCreate = Body()) -> Schema:
        """
        Creates a new item using the provided schema.

        Args:
            payload: The data required to create a new item.

        Returns:
            The created item as a Pydantic model.
        """
        return await self.crud.create(payload)

    async def get_all(
            self,
            prefetch: bool = Query(False),
            limit: int = Query(50, ge=1, le=100),
            offset: int = Query(0, ge=0)
    ) -> GetAllResponse[type[Schema]]:
        """
        Returns all items in the specified range and total count.

        Args:
            prefetch: Whether to prefetch related items.
            limit: The maximum number of items to return.
            offset: The offset for pagination.

        Returns:
            A GetAllResponse object containing a list of items and the total count.
        """
        return GetAllResponse(
            items=await self.crud.get_all(prefetch, limit, offset),
            total=await self.crud.model.all().count()
        )

    async def get_item(self, item_id: int = Path()) -> Schema | None:
        """
        Fetches a single item by its ID.

        Args:
            item_id: The ID of the item to fetch.

        Returns:
            The item if found, or None if not found.
        """
        return await self.crud.get_by_id(item_id)

    async def update(self, payload: SchemaCreate = Body(), item_id: int = Path()) -> Schema | None:
        """
        Updates an existing item.

        Args:
            payload: The data to update the item.
            item_id: The ID of the item to update.

        Returns:
            The updated item, or None if the item does not exist.
        """
        return await self.crud.update_by(payload, id=item_id)

    async def delete_item(self, item_id: int = Path()) -> bool:
        """
        Deletes an item by its ID.

        Args:
            item_id: The ID of the item to delete.

        Returns:
            True if the item was deleted, False if it was not found.
        """
        return await self.crud.delete_by(id=item_id)
