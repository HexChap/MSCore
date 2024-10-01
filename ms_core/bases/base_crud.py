from multimethod import multimethod
from tortoise import Model as TortoiseModel
from tortoise.contrib.pydantic import PydanticModel
from tortoise.exceptions import DoesNotExist


class BaseCRUD[Model: TortoiseModel, Schema: PydanticModel]:
    """Base class that implements CRUD for the database using TortoiseORM.

    Attributes:
        model: Tortoise Model on which CRUD operations are applied.
        schema: PydanticModel generated from the Tortoise Model.
    """

    model: Model
    schema: Schema

    @classmethod
    async def create(cls, payload: PydanticModel, **kwargs) -> Schema:
        """Implements the create operation.

        Args:
            payload: The data to create the instance.
            **kwargs: Additional arguments for the creation process.

        Returns:
            The created instance as a PydanticModel.
        """
        instance = await cls.model.create(
            **payload.model_dump(exclude_none=True), **kwargs
        )

        return await cls.schema.from_tortoise_orm(instance)

    @classmethod
    async def get_or_create(cls, **kwargs) -> tuple[Schema, bool]:
        """Implements the get or create operation.

        If the item is not found, it will try to create it from the provided kwargs.

        Args:
            **kwargs: Arguments to search for and create the instance if not found.

        Returns:
            The found or created instance and a boolean indicating whether it was created.

        Raises:
            IntegrityError: If creation fails.
        """
        instance, status = await cls.model.get_or_create(**kwargs)

        return await cls.schema.from_tortoise_orm(instance), status

    @classmethod
    @multimethod
    async def get_by_id(cls, id_: int) -> Schema | None:
        """Fetches an item by its ID.

        Args:
            id_: The ID of the item.

        Returns:
            The corresponding PydanticModel or None if not found.
        """
        return await cls.get_by(id=id_)

    @classmethod
    async def get_by(cls, **kwargs) -> Schema | None:
        """Fetches an item based on the provided kwargs.

        Args:
            **kwargs: Criteria to search for the item.

        Returns:
            The corresponding PydanticModel or None if not found.
        """
        if not (instance := await cls.model.get_or_none(**kwargs)):
            return None

        return await cls.schema.from_tortoise_orm(instance)

    @classmethod
    @multimethod
    async def get_all(
            cls,
            prefetch: bool = False,
            limit: int = 50,
            offset: int = 0,
            **extra_filters
    ) -> list[Schema]:
        """Bulk fetches items from the database.

        Args:
            prefetch: Whether to prefetch related data. Defaults to False.
            limit: The number of items to fetch. Defaults to 50.
            offset: The offset from which to start fetching. Defaults to 0.
            **extra_filters: Additional filters to apply.

        Returns:
            A list of fetched PydanticModels. Empty list if no items are found.
        """
        query = cls.model.all().filter(**extra_filters).offset(offset).limit(limit)
        result = []

        for item in await query:
            if prefetch:
                result.append(await cls.schema.from_tortoise_orm(item))
            else:
                result.append(cls.schema.model_construct(**item.__dict__))

        return result

    @classmethod
    async def filter_by(cls, **kwargs) -> list[Schema] | None:
        """Exposes the filter method of Tortoise Model.

        Args:
            **kwargs: Criteria to filter the items.

        Returns:
            A list of matching items or None if not found.
        """
        try:
            return [
                await cls.schema.from_tortoise_orm(item)
                for item in await cls.model.filter(**kwargs)
            ]

        except DoesNotExist as _:
            return None

    @classmethod
    async def update_by(cls, payload: Schema | dict, **kwargs) -> Schema | None:
        """Implements the update operation.

        Args:
            payload: The data to update the instance.
            **kwargs: Criteria to find the item to be updated.

        Returns:
            The updated instance or None if not found.
        """
        if not (instance := await cls.model.get_or_none(**kwargs)):
            return None

        as_dict = (
            payload.items()
            if isinstance(payload, dict)
            else payload.model_dump().items()
        )

        await instance.update_from_dict(
            {key: value for key, value in as_dict if value is not None}
        ).save()
        return await cls.schema.from_tortoise_orm(instance)

    @classmethod
    async def delete_by(cls, **kwargs) -> bool:
        """Implements the delete operation.

        Deletes an item based on the provided kwargs.

        Args:
            **kwargs: Search parameters to find the item to delete.

        Returns:
            True if the item was successfully deleted, False otherwise.
        """
        if not (instance := await cls.model.get_or_none(**kwargs)):
            return False

        await instance.delete()
        return True
