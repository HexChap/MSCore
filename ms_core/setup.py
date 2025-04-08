import importlib
import os
from pathlib import Path

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise


def conf_db(app: FastAPI, db_url: str, model_paths: list[str] = None) -> None:
    """
    Registers TortoiseORM with the FastAPI application.

    Args:
        app: An instance of the FastAPI class.
        db_url: The database URL to connect to.
        model_paths: A list of paths to modules containing Tortoise models. If not provided, defaults to None.

    Returns:
        None
    """
    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": model_paths} if model_paths else None,
        generate_schemas=True,
        add_exception_handlers=True,
    )


def include_routers(app: FastAPI, routers_path: Path) -> None:
    """
    Includes all routers in the specified directory into the FastAPI application.

    The router file must contain a variable named `router`, which should be an instance of `fastapi.APIRouter`.
    Files starting with an underscore ("_") or not ending with ".py" will be ignored.

    Args:
        app: An instance of the FastAPI class.
        routers_path: The path to the directory containing router files.

    Raises:
        ValueError: If `routers_path` is not a directory.

    Returns:
        None
    """
    if not routers_path.is_dir():
        raise ValueError("routers_path must be a directory")

    module_path = '.'.join(routers_path.parts)  # Convert to dot notation (package.module)

    for module_name in os.listdir(routers_path):
        if module_name.startswith("_") or not module_name.endswith(".py"):
            continue

        module = importlib.import_module(f"{module_path}.{module_name.removesuffix('.py')}")
        app.include_router(module.router)


def setup_app(
    app: FastAPI,
    db_url: str,
    routers_path: Path,
    model_paths: list[str] = None
) -> None:
    """
    Configures the FastAPI application with TortoiseORM and includes all routers from the specified directory.

    Args:
        app: An instance of the FastAPI class.
        db_url: The database URL to connect to.
        routers_path: The path to the directory containing router files.
        model_paths: A list of relative paths (dot notation) to modules containing Tortoise models. If not provided, defaults to None.

    Returns:
        None
    """
    conf_db(app, db_url, model_paths)
    include_routers(app, routers_path)
