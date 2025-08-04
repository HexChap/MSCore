from typing import Any, Type, TypeVar, overload
from tortoise.contrib.pydantic import PydanticModel

from ms_core.bases import CRUD, I18nModel

M = TypeVar("M", bound=I18nModel)
S = TypeVar("S", bound=PydanticModel)


class I18nCRUD(CRUD[M, S]):
    """
    Adds language-based overloads on get_by_id(...) and get_all(...).
    """

    @staticmethod
    def _with_lang(filters: dict[str, Any], lang: str | None) -> dict[str, Any]:
        return {**filters, **({"tuple_lang": lang} if lang else {})}

    @overload
    async def get_by_id(self, id_: int) -> S | None: ...

    @overload
    async def get_by_id(self, id_: int, *, lang: str) -> S | None: ...

    async def get_by_id(self, id_: int, *, lang: str | None = None) -> S | None:
        inst = await self._model.get_or_none(**self._with_lang({"id": id_}, lang))
        return await self._schema.from_tortoise_orm(inst) if inst else None

    @overload
    async def get_all(
        self,
        prefetch: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[S]: ...

    @overload
    async def get_all(
        self,
        prefetch: bool = False,
        limit: int = 50,
        offset: int = 0,
        *,
        lang: str,
        **extra_filters,
    ) -> list[S]: ...

    async def get_all(
        self,
        prefetch: bool = False,
        limit: int = 50,
        offset: int = 0,
        *,
        lang: str | None = None,
        **extra_filters,
    ) -> list[S]:
        return await super().get_all(
            prefetch=prefetch,
            limit=limit,
            offset=offset,
            **self._with_lang(extra_filters, lang),
        )


def i18n_crud_for(model: Type[M], schema: Type[S]) -> CRUD[M, S]:
    """Factory function returning a CRUD instance with type‑safe async/multi‑dispatch methods."""
    return I18nCRUD(model, schema)
