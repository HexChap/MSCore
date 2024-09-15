from inspect import signature
from typing import Callable

from fastapi import APIRouter, Path, Query, Body
from makefun import create_function
from pydantic import BaseModel

from ms_core.bases import BaseCRUD


class BaseCRUDRouter[
    Schema: BaseModel,
    SchemaCreate: BaseModel
](APIRouter):
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
                "response_model": list[schema]
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
        return await self.crud.create(payload)

    async def get_all(
            self,
            prefetch: bool = Query(False),
            limit: int = Query(50),
            offset: int = Query(0)
    ) -> tuple[list[Schema], int]:
        """ Returns all items in the specified range and total count """
        return await self.crud.get_all(prefetch, limit, offset), await self.crud.model.all().count()

    async def get_item(self, item_id: int = Path()) -> Schema | None:
        return await self.crud.get_by_id(item_id)

    async def update(self, payload: SchemaCreate = Body(), item_id: int = Path()) -> Schema | None:
        return await self.crud.update_by(payload, id=item_id)

    async def delete_item(self, item_id: int = Path()) -> bool:
        return await self.crud.delete_by(id=item_id)
