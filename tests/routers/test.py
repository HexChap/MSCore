from fastapi import APIRouter, Query

from tests.cruds.crud1 import Test1CRUD, Test1Payload
from tests.cruds.crud2 import Test2CRUD, Test2Payload

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/create")
async def create(lang: str = Query("bg")):
    test2 = await Test2CRUD.create(Test2Payload(test=123))
    return await Test1CRUD.create(Test1Payload(test="str", test2_id=test2.id, tuple_lang=lang))


@router.get("/get-all")
async def get(limit: int = Query(50), offset: int = Query(0), lang: str = Query("bg")):
    return await Test1CRUD.get_all(limit, offset, lang)
