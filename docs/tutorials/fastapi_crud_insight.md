# Contributor Guide: Design of BaseCRUDRouter

This document explains the internal design and key decisions behind
the `BaseCRUDRouter` implementation.

## Goals

- Auto-generate standard CRUD endpoints with flexible configuration
- Minimal boilerplate for users
- Safe and type-correct endpoint signatures
- Selective endpoint inclusion/exclusion
- Customizable endpoint behavior without losing type safety

## Key Design Points

### Multi-method API via `BaseCRUD`

This router relies on a `crud` object based on `BaseCRUD` abstraction,
which provides methods like:

- `create`
- `get_all`
- `get_by_id`
- `update_by`
- `delete_by`

This separation enforces SRP (Single Responsibility Principle) and allows
easy swapping or customizing of storage logic.

### Flexible Endpoint Configuration System

#### Endpoint Selection

The router supports flexible endpoint selection through:

```python
include_endpoints: list[DefaultEndpoint] | Literal["all"] = "all"
exclude_endpoints: list[DefaultEndpoint] | None = None
```

This allows users to:

- Include all endpoints by default (`"all"`)
- Selectively include only specific endpoints
- Exclude unwanted endpoints from the default set

The logic combines these parameters using set operations:

```python
if include_endpoints == "all":
    endpoints_to_include = set(DefaultEndpoint)
else:
    endpoints_to_include = set(include_endpoints)

if exclude_endpoints:
    endpoints_to_include -= set(exclude_endpoints)
```

#### Endpoint Configuration

Each endpoint can be customized via the `EndpointConfig` model:

```python
class EndpointConfig(BaseModel):
    path: str
    methods: list[str]
    response_model: Any = None
    include_in_schema: bool = True
    tags: list[str] | None = None
    summary: str | None = None
    description: str | None = None
    deprecated: bool = False
```

This provides fine-grained control over each endpoint's FastAPI route configuration.

### Default Configuration System

The `_get_default_endpoint_config` method provides sensible defaults
for each endpoint type:

```python
configs = {
    DefaultEndpoint.CREATE: EndpointConfig(
        path=f"{self.path_prefix}/",
        methods=["POST"],
        response_model=self.schema,
        summary="Create new item",
        # ... other defaults
    ),
    # ... other endpoint configurations
}
```

Custom configurations merge with or override these defaults, allowing
users to customize only what they need.

### Dynamic Signature Replacement

Pydantic generic models (like `Schema`, `SchemaCreate`) are passed to the router.
To ensure FastAPI/OpenAPI generates correct docs and validations,
endpoint signatures are dynamically replaced using:

```python
from makefun import create_function
```

The `_update_handler_signature` method inspects method signatures using `inspect.signature`
and replaces type annotations for parameters where placeholders (`Schema`, `SchemaCreate`)
were used:

```python
for name, param in params.items():
    if hasattr(param.annotation, "__name__"):
        match param.annotation.__name__:
            case "Schema":
                params[name] = param.replace(annotation=self.schema)
                is_replaced = True
            case "SchemaCreate":
                params[name] = param.replace(annotation=self.schema_create)
                is_replaced = True
```

This guarantees correct typing in route definitions without
forcing inheritance or metaclass hacks.

### Endpoint Registration Flow

The endpoint building process follows this flow:

1. **Selection**: Determine which endpoints to include
based on `include_endpoints` and `exclude_endpoints`
2. **Configuration**: For each selected endpoint,
get its configuration (custom or default)
3. **Registration**: Register each endpoint with FastAPI using the resolved configuration

```python
def _build_endpoints(self, endpoints_to_include, endpoint_configs):
    endpoint_handlers = {
        DefaultEndpoint.CREATE: self.create,
        DefaultEndpoint.GET_ALL: self.get_all,
        # ... other mappings
    }
    
    for endpoint_type in endpoints_to_include:
        handler = endpoint_handlers[endpoint_type]
        config = endpoint_configs.get(endpoint_type) or self._get_default_endpoint_config(endpoint_type)
        updated_handler = self._update_handler_signature(handler)
        self.add_api_route(path=config.path, endpoint=updated_handler, **config.to_route_kwargs())
```

### Path Management

The router supports flexible path management through:

- Router `prefix` (FastAPI standard)
- `path_prefix` parameter (custom prefix for all endpoint paths)
- Individual endpoint `path` configuration

Paths are constructed by combining these elements, with `path_prefix` being
stripped of trailing slashes to ensure clean URL construction.

### Generic Response Models

List responses use a generic wrapper model:

```python
class GetAllResponse[Schema: BaseModel](BaseModel):
    items: list[Schema]
    total: int
```

This provides standard pagination responses while retaining schema
typing and allowing proper OpenAPI documentation generation.

### Type Safety Considerations

The router maintains type safety through several mechanisms:

1. **Generic type parameters**: `BaseCRUDRouter[Schema, SchemaCreate]`
ensures compile-time type checking
2. **Dynamic signature replacement**: Runtime signature updates
ensure FastAPI sees correct types
3. **Pydantic model validation**: All configurations use Pydantic
models for runtime validation

### Configuration Extensibility

The `EndpointConfig.to_route_kwargs()` method cleanly separates path from other
route configuration, making it easy to extend supported FastAPI route parameters
without breaking existing code.

## Future Extensibility

The design supports future enhancements:

- **Custom endpoint handlers**: The infrastructure exists to add non-CRUD endpoints
- **Middleware integration**: Endpoint-specific middleware could be added to `EndpointConfig`
- **Response transformation**: Custom response models could be configured per endpoint
- **Authentication/authorization**: Permission-based endpoint filtering
could be added

## Testing Considerations

The modular design enables focused testing:

- Endpoint selection logic can be tested independently
- Configuration merging can be verified in isolation  
- Signature replacement can be validated with mock schemas
- Each endpoint handler can be tested separately
