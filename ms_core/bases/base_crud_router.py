from fastapi import APIRouter, Path, Query, Body
from pydantic import BaseModel
from tortoise import Model

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

        self.add_api_route("/", self.create, methods=["POST"], response_model=schema)
        self.add_api_route("/", self.get_all, methods=["GET"], response_model=list[schema])
        self.add_api_route("/{item_id}", self.get_item, methods=["GET"], response_model=schema | None)
        self.add_api_route("/{item_id}", self.update, methods=["PUT"], response_model=schema | None)
        self.add_api_route("/{item_id}", self.delete_item, methods=["DELETE"], response_model=bool)

    async def create(self, payload: SchemaCreate = Body()) -> Schema:
        print()
        return await self.crud.create(payload)

    async def get_all(self, prefetch: bool = Query(False)) -> list[Schema]:
        return await (self.crud.get_all_prefetch() if prefetch else self.crud.get_all())

    async def get_item(self, item_id: int = Path()) -> Schema | None:
        return await self.crud.get_by_id(item_id)

    async def update(self, payload: Schema = Body(), item_id: int = Path()) -> Schema | None:
        return await self.crud.update_by(payload, id=item_id)

    async def delete_item(self, item_id: int = Path()) -> bool:
        return await self.crud.delete_by(id=item_id)
