"""Unit tests for BaseCRUDRouter internal methods and edge cases."""

import pytest
from inspect import Parameter, Signature
from makefun import create_function
from tortoise import Tortoise, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from ms_core.bases.abstract_model import AbstractModel
from ms_core.bases.base_crud import crud_for
from ms_core.bases.base_crud_router import BaseCRUDRouter, DefaultEndpoint


class TestModel(AbstractModel):
    name = fields.CharField(max_length=50)
    value = fields.IntField(default=0)


@pytest.fixture(scope="session", autouse=True)
async def init_db():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": [__name__]},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
def router_components():
    """Fixture providing router components for testing."""
    schema = pydantic_model_creator(TestModel)
    schema_create = pydantic_model_creator(TestModel, exclude_readonly=True)
    crud = crud_for(TestModel, schema)

    router = BaseCRUDRouter(
        crud=crud,
        schema=schema,
        schema_create=schema_create,
    )

    return {
        "router": router,
        "schema": schema,
        "schema_create": schema_create,
        "crud": crud,
    }


class TestHandlerSignatureUpdate:
    """Test the _update_handler_signature method."""

    def test_no_signature_replacement_needed(self, router_components):
        """Test handler with no Schema annotations (unchanged)."""
        router = router_components["router"]

        def handler(x: int, y: str) -> int:
            return x

        updated = router._update_handler_signature(handler)
        assert updated is handler  # Should be unchanged

    def test_annotation_without_name_attribute(self, router_components):
        """Test handler with annotation that has no __name__ attribute."""
        router = router_components["router"]

        # Create annotation without __name__ attribute
        class NoNameAnnotation:
            pass

        def mock_handler(param):
            pass

        # Create parameter with annotation that has no __name__
        param = Parameter(
            "param", Parameter.POSITIONAL_OR_KEYWORD, annotation=NoNameAnnotation()
        )
        mock_sig = Signature([param])
        mock_handler_with_sig = create_function(mock_sig, mock_handler)

        # Should not cause replacement since hasattr(annotation, "__name__") is False
        updated = router._update_handler_signature(mock_handler_with_sig)
        assert updated is mock_handler_with_sig

    def test_schema_annotation_replacement(self, router_components):
        """Test replacement of Schema and SchemaCreate annotations."""
        router = router_components["router"]
        schema = router_components["schema"]
        schema_create = router_components["schema_create"]

        # Create mock annotations with __name__ attributes
        class SchemaAnnotation:
            __name__ = "Schema"

        class SchemaCreateAnnotation:
            __name__ = "SchemaCreate"

        class OtherAnnotation:
            __name__ = "SomeOtherType"

        def mock_handler(schema_param, create_param, other_param):
            pass

        # Create parameters with annotations that should be replaced
        schema_param = Parameter(
            "schema_param",
            Parameter.POSITIONAL_OR_KEYWORD,
            annotation=SchemaAnnotation(),
        )
        create_param = Parameter(
            "create_param",
            Parameter.POSITIONAL_OR_KEYWORD,
            annotation=SchemaCreateAnnotation(),
        )
        other_param = Parameter(
            "other_param", Parameter.POSITIONAL_OR_KEYWORD, annotation=OtherAnnotation()
        )

        mock_sig = Signature([schema_param, create_param, other_param])
        mock_handler_with_sig = create_function(mock_sig, mock_handler)  # type: ignore

        # Test the update method
        updated = router._update_handler_signature(mock_handler_with_sig)

        # Function should be different (replaced) because we had Schema annotations
        assert updated is not mock_handler_with_sig

        # Check that the signature was actually updated
        import inspect

        updated_sig = inspect.signature(updated)
        updated_params = list(updated_sig.parameters.values())

        # Schema annotations should be replaced with actual types
        assert updated_params[0].annotation == schema
        assert updated_params[1].annotation == schema_create
        # Other annotations should remain unchanged (compare with the original instance)
        assert updated_params[2].annotation.__class__ == OtherAnnotation
        assert updated_params[2].annotation.__name__ == "SomeOtherType"

    def test_partial_schema_replacement(self, router_components):
        """Test replacement when only some parameters have Schema annotations."""
        router = router_components["router"]
        schema = router_components["schema"]

        class SchemaAnnotation:
            __name__ = "Schema"

        def mock_handler(schema_param, regular_param: int):
            pass

        # Only first parameter has Schema annotation
        schema_param = Parameter(
            "schema_param",
            Parameter.POSITIONAL_OR_KEYWORD,
            annotation=SchemaAnnotation(),
        )
        regular_param = Parameter(
            "regular_param", Parameter.POSITIONAL_OR_KEYWORD, annotation=int
        )

        mock_sig = Signature([schema_param, regular_param])
        mock_handler_with_sig = create_function(mock_sig, mock_handler)  # type: ignore

        updated = router._update_handler_signature(mock_handler_with_sig)

        # Should be replaced because at least one Schema annotation was found
        assert updated is not mock_handler_with_sig

        # Check signature
        import inspect

        updated_sig = inspect.signature(updated)
        updated_params = list(updated_sig.parameters.values())

        assert updated_params[0].annotation == schema
        assert updated_params[1].annotation == int


class TestRouterInitialization:
    """Test router initialization edge cases."""

    def test_minimal_router_creation(self, router_components):
        """Test creating router with minimal required parameters."""
        crud = router_components["crud"]
        schema = router_components["schema"]
        schema_create = router_components["schema_create"]

        # Should not raise any exceptions
        router = BaseCRUDRouter(
            crud=crud,
            schema=schema,
            schema_create=schema_create,
        )

        assert router.crud is crud
        assert router.schema is schema
        assert router.schema_create is schema_create
        assert router.limit == 50  # default
        assert router.offset == 0  # default

    def test_router_with_all_parameters(self, router_components):
        """Test creating router with all possible parameters."""
        crud = router_components["crud"]
        schema = router_components["schema"]
        schema_create = router_components["schema_create"]

        router = BaseCRUDRouter(
            crud=crud,
            schema=schema,
            schema_create=schema_create,
            limit=100,
            offset=10,
            include_endpoints=[DefaultEndpoint.CREATE, DefaultEndpoint.GET_ALL],
            exclude_endpoints=[DefaultEndpoint.DELETE],
            endpoint_configs={},
            prefix="/test",
            tags=["test"],
        )

        assert router.limit == 100
        assert router.offset == 10
        assert router.prefix == "/test"
        assert router.tags == ["test"]

    def test_empty_include_endpoints(self, router_components):
        """Test router with empty include_endpoints list."""
        crud = router_components["crud"]
        schema = router_components["schema"]
        schema_create = router_components["schema_create"]

        # Empty list should result in no endpoints
        router = BaseCRUDRouter(
            crud=crud,
            schema=schema,
            schema_create=schema_create,
            include_endpoints=[],
        )

        # Router should be created successfully with no routes
        assert len(router.routes) == 0
