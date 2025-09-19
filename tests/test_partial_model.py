import pytest
from pydantic import BaseModel, field_validator

from ms_core.utils import partial_model


def test_partial_makes_all_fields_optional():
    class User(BaseModel):
        id: int
        name: str
        active: bool = True

    PartialUser = partial_model(User)

    # All original field names should still be present as model fields
    assert set(PartialUser.model_fields.keys()) == {"id", "name", "active"}

    # Creating without any fields must succeed (fields are optional)
    inst = PartialUser()
    data = inst.model_dump()  # include None values by default

    # Fields should exist and be None or default (partial -> Optional with default None)
    assert data["id"] is None
    assert data["name"] is None
    assert data["active"] is None


def test_partial_with_without_fields_removes_fields_from_model():
    class Article(BaseModel):
        title: str
        content: str
        internal_note: str

    PartialArticle = partial_model(Article, without_fields=["internal_note"])

    # internal_note should be omitted from model_fields (ClassVar)
    assert "internal_note" not in PartialArticle.model_fields
    # other fields remain
    assert set(PartialArticle.model_fields.keys()) == {"title", "content"}


def test_partial_preserves_model_name_and_config_title():
    class A(BaseModel):
        foo: int

    PartialA = partial_model(A, model_name="MyCustomPartial")
    # model_config is a ConfigDict; title should match supplied model_name
    # Access via dictionary-style to avoid attribute access quirks across pydantic versions
    cfg = PartialA.model_config
    assert cfg.get("title") == "MyCustomPartial"


def test_partial_with_validators_does_not_raise_on_creation_and_accepts_values():
    class WithValidator(BaseModel):
        x: int

        @field_validator("x", mode="before")
        @classmethod
        def ensure_positive(cls, v):
            # a validator that would raise if given a non-positive integer
            if v is None:
                # normally this validator might not expect None; the decorator-modifying
                # code should avoid breaking creation of the partial model.
                return v
            if v <= 0:
                raise ValueError("x must be > 0")
            return v

    PartialWithValidator = partial_model(WithValidator)

    # Creating without x should succeed (field becomes optional)
    inst = PartialWithValidator()
    dd = inst.model_dump()
    assert "x" in dd and dd["x"] is None

    # Creating with a valid x works
    inst2 = PartialWithValidator(x=42)
    assert inst2.x == 42

    # And invalid value still is validated when provided
    with pytest.raises(Exception):
        PartialWithValidator(x=0)


def test_partial_field_defaults_are_overridden_to_none():
    class DefaultsModel(BaseModel):
        a: int = 1
        b: str = "hello"

    PartialDefaults = partial_model(DefaultsModel)
    inst = PartialDefaults()
    dd = inst.model_dump()
    # original defaults should be overridden to None by partial_model
    assert dd["a"] is None
    assert dd["b"] is None
