from copy import deepcopy
from typing import Any, ClassVar, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, create_model
from pydantic.fields import FieldInfo

Model = TypeVar("Model", bound=BaseModel)


def partial_model(
    model: Type[Model],
    model_name: str | None = None,
    *,
    without_fields: Optional[list[str]] = None,
) -> type[Model]:
    """A decorator that create a partial model.

    Args:
        model (Type[BaseModel]): BaseModel model.

    Returns:
        Type[BaseModel]: ModelBase partial model.
    """
    model = deepcopy(model)
    model_name = model_name if model_name else model.__name__ + "Partial"

    if without_fields is None:
        without_fields = []

    def make_field_optional(
        field: FieldInfo, default: Any = None, omit: bool = False
    ) -> tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = default
        new.annotation = Optional[field.annotation]
        # Wrap annotation in ClassVar if field in without_fields
        return ClassVar[new.annotation] if omit else new.annotation, new

    base_model = type(
        "BasePydanticModel",
        (model,),
        {
            "model_config": ConfigDict(title=model_name),
        },
    )

    return create_model(
        model_name,
        __base__=base_model,
        __module__=model.__module__,
        **{
            field_name: make_field_optional(
                field_info, omit=(field_name in without_fields)
            )
            for field_name, field_info in model.model_fields.items()
        },
    )
