from tortoise import Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator

from ms_core import I18nCRUD
from tests.models.test1 import Test1

Tortoise.init_models(["tests.models.test1"], "models")
Test1Schema = pydantic_model_creator(Test1, name="Test1Schema")
Test1Create = pydantic_model_creator(Test1, name="Test1Create", exclude_readonly=True)


class Test1CRUD(I18nCRUD[Test1, Test1Schema]):
    model = Test1
    schema = Test1Schema
