# Contributor Guide: Design of BaseCRUDRouter

This document explains the internal design and key decisions behind
the `BaseCRUDRouter` implementation.

## Goals

- Auto-generate standard CRUD endpoints with flexible configuration
- Minimal boilerplate for users
- Safe and type-correct endpoint signatures
- Selective endpoint inclusion/exclusion
- Customizable endpoint behavior without losing type safety
- Native FastAPI dependency injection support

## Key Design Points

### CRUD Instance Integration

This router relies on a `crud` object based on the `CRUD` class,
which provides methods like:

- `create`
- `get_all`
- `get_by_id`
- `update_by`
- `delete_by`

This separation enforces SRP (Single Responsibility Principle) and allows
easy swapping or customizing of storage logic. The router handles HTTP
concerns while the CRUD instance handles database operations.

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
    dependencies: list[Callable] | None = None
```

This provides fine-grained control over each endpoint's FastAPI route configuration,
including dependency injection support.

### Default Configuration System

The `_get_default_endpoint_config` method provides sensible defaults
for each endpoint type:

```python
configs = {
    DefaultEndpoint.CREATE: EndpointConfig(
        path="/",
        methods=["POST"],
        response_model=self.schema,
        summary="Create new item",
        description="Create a new item with the provided data",
    ),
    DefaultEndpoint.GET_ALL: EndpointConfig(
        path="/",
        methods=["GET"],
        response_model=GetAllResponse[self.schema],
        summary="Get all items",
        description="Retrieve all items with pagination support",
    ),
    # ... other endpoint configurations
}
```

Custom configurations merge with or override these defaults, allowing
users to customize only what they need while maintaining sensible defaults.

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
forcing inheritance or metaclass hacks. FastAPI receives properly
typed handler functions with actual Pydantic models instead of generics.

### Dependency Injection Architecture

Dependencies are handled through the `EndpointConfig.dependencies` field:

```python
dependencies: list[Callable] | None = None
```

The `to_route_kwargs()` method converts these callables to FastAPI dependencies:

```python
def to_route_kwargs(self) -> dict:
    config_dict = self.model_dump(exclude={"path"}, exclude_none=True)
    
    if self.dependencies:
        config_dict["dependencies"] = [Depends(dep) for dep in self.dependencies]
    
    return config_dict
```

This allows users to specify dependency functions as simple callables,
while the router handles the FastAPI `Depends()` wrapper internally.

### Generic Response Models

List responses use a generic wrapper model:

```python
class GetAllResponse[Schema: BaseModel](BaseModel):
    items: list[Schema]
    total: int
```

This provides standard pagination responses while retaining schema
typing and allowing proper OpenAPI documentation generation. The generic
syntax ensures type safety across different schema types.

### Endpoint Registration Flow

The endpoint building process follows this flow:

1. **Selection**: Determine which endpoints to include
   based on `include_endpoints` and `exclude_endpoints`
2. **Configuration**: For each selected endpoint,
   get its configuration (custom or default)
3. **Signature Update**: Replace generic type annotations with actual schemas
4. **Registration**: Register each endpoint with FastAPI using the resolved configuration

```python
def _build_endpoints(self, endpoints_to_include, endpoint_configs):
    endpoint_handlers = {
        DefaultEndpoint.CREATE: self._create,
        DefaultEndpoint.GET_ALL: self._get_all,
        DefaultEndpoint.GET_ITEM: self._get_item,
        DefaultEndpoint.UPDATE: self._update,
        DefaultEndpoint.DELETE: self._delete_item,
    }
    
    for endpoint_type in endpoints_to_include:
        handler = endpoint_handlers[endpoint_type]
        config = endpoint_configs.get(endpoint_type) or self._get_default_endpoint_config(endpoint_type)
        updated_handler = self._update_handler_signature(handler)
        self.add_api_route(path=config.path, endpoint=updated_handler, **config.to_route_kwargs())
```

### Handler Method Design

Each handler method is designed with specific concerns:

#### Input Validation
```python
async def _create(self, payload: SchemaCreate = Body()) -> Schema:
    return await self.crud.create(payload)
```

#### Query Parameters
```python
async def _get_all(
    self,
    prefetch: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> GetAllResponse[Schema]:
```

#### Path Parameters
```python
async def _get_item(self, item_id: int = Path()) -> Schema | None:
    return await self.crud.get_by_id(item_id)
```

Each handler delegates to the CRUD instance, maintaining separation of concerns.

### Type Safety Considerations

The router maintains type safety through several mechanisms:

1. **Generic type parameters**: `BaseCRUDRouter[Schema, SchemaCreate]`
   ensures compile-time type checking
2. **Dynamic signature replacement**: Runtime signature updates
   ensure FastAPI sees correct types
3. **Pydantic model validation**: All configurations use Pydantic
   models for runtime validation
4. **Generic response models**: `GetAllResponse[Schema]` maintains
   typing throughout the response chain

### Configuration Extensibility

The `EndpointConfig.to_route_kwargs()` method cleanly separates path from other
route configuration, making it easy to extend supported FastAPI route parameters
without breaking existing code:

```python
def to_route_kwargs(self) -> dict:
    config_dict = self.model_dump(exclude={"path"}, exclude_none=True)
    
    if self.dependencies:
        config_dict["dependencies"] = [Depends(dep) for dep in self.dependencies]
    
    return config_dict
```

New FastAPI route parameters can be added to `EndpointConfig` and will
automatically be passed through to `add_api_route`.

### Custom Endpoint Support

The `add_custom_endpoint` method follows the same signature replacement pattern:

```python
def add_custom_endpoint(self, handler: Callable, config: EndpointConfig):
    updated_handler = self._update_handler_signature(handler)
    self.add_api_route(
        path=config.path, endpoint=updated_handler, **config.to_route_kwargs()
    )
```

This ensures custom endpoints receive the same type safety and dependency
injection benefits as built-in CRUD endpoints.

## Performance Considerations

### Signature Replacement Optimization

Signature replacement only occurs when necessary:

```python
return (
    create_function(sig.replace(parameters=list(params.values())), handler)
    if is_replaced
    else handler
)
```

If no generic types need replacement, the original handler is used directly.

### CRUD Instance Reuse

The same CRUD instance is reused across all endpoint handlers, avoiding
unnecessary object creation and maintaining connection pooling benefits.

## Future Extensibility

The design supports future enhancements:

- **Custom endpoint handlers**: The infrastructure exists to add non-CRUD endpoints
- **Middleware integration**: Endpoint-specific middleware could be added to `EndpointConfig`
- **Response transformation**: Custom response models could be configured per endpoint
- **Authentication/authorization**: Permission-based endpoint filtering could be added
- **Bulk operations**: Batch create/update/delete endpoints could be added
- **Custom query parameters**: Additional filtering/sorting parameters could be supported

## Testing Considerations

The modular design enables focused testing:

- Endpoint selection logic can be tested independently
- Configuration merging can be verified in isolation  
- Signature replacement can be validated with mock schemas
- Each endpoint handler can be tested separately
- Dependency injection can be tested with mock dependencies

## Error Handling

The router relies on FastAPI's built-in error handling and HTTP exception
system. CRUD operations that return `None` are handled gracefully,
allowing the API to return appropriate 404 responses when items are not found.

## Security Considerations

Dependencies are applied per-endpoint, allowing fine-grained security controls:

- Public read endpoints (no dependencies)
- Authenticated operations (user token required)
- Admin-only operations (role-based access)
- Custom validation logic (per-operation checks)

The dependency system integrates with FastAPI's security utilities and
OpenAPI documentation generation.
