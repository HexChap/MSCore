from tortoise import Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator

from ms_core.bases.base_crud import crud_for
from tests.models.test1 import Test1

Tortoise.init_models(["tests.models.test1"], "models")
Test1Schema = pydantic_model_creator(Test1, name="Test1Schema")
Test1Create = pydantic_model_creator(Test1, name="Test1Create", exclude_readonly=True)

Test1CRUD = crud_for(Test1, Test1Schema)
