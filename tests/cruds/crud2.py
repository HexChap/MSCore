from tortoise import Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator

from ms_core import I18nCRUD
from tests.models.test2 import Test2

Test2Schema = pydantic_model_creator(Test2)
Test2Payload = pydantic_model_creator(Test2, name="Test2Payload", exclude_readonly=True)


class Test2CRUD(I18nCRUD[Test2, Test2Schema]):
    model = Test2
    schema = Test2Schema
