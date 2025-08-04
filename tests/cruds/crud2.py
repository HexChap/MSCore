from tortoise.contrib.pydantic import pydantic_model_creator

from ms_core.bases.i18n_crud import i18n_crud_for
from tests.models.test2 import Test2

Test2Schema = pydantic_model_creator(Test2, name="Test2Schema")
Test2Create = pydantic_model_creator(Test2, name="Test2Create", exclude_readonly=True)

Test2CRUD = i18n_crud_for(Test2, Test2Schema)
