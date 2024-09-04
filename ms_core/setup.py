import importlib
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise


def conf_db(app: FastAPI, db_url: str, model_paths: list[str] = None):
    """
    Generates a list of paths to the models, includes aerich, then registers Tortoise

    :param app: Instance of FastAPI class
    :param db_url: DB url
    :param model_paths: Paths to files, containing tortoise models
    :return:
    """

    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": model_paths} if model_paths else None,
        generate_schemas=True,
        add_exception_handlers=True,
    )


def include_routers(app: FastAPI, routers_path: Path):
    """
    A router must contain the *router* variable, which must be a fastapi.APIRouter subclass \n
    If router's name starts with "_" it won't be included

    :param app: Instance of FastAPI class
    :param routers_path: Path to the routers dir
    :return: None
    """
    if not routers_path.is_dir():
        raise ValueError("routers_path must be a dir")

    module_path = '.'.join(routers_path.parts)  # converts to dot notation (package.module.stuff)

    for module_name in os.listdir(routers_path):
        if module_name.startswith("_") or not module_name.endswith(".py"):
            continue

        module = importlib.import_module(f"{module_path}.{module_name.removesuffix('.py')}")

        app.include_router(module.router)


def conf_base_middlewares(app: FastAPI):
    origins = [
        # "http://localhost:5173",
        # "http://localhost:3000",
        "*"
    ]

    # noinspection PyTypeChecker
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_app(
    app: FastAPI,
    db_url: str,
    routers_path: Path,
    model_paths: list[str] = None
):
    """
    Prepares db, middlewares and includes routers

    :param app: Instance of FastAPI class
    :param db_url: DB url
    :param model_paths: Relative paths to files, containing tortoise models

    :param app: Instance of FastAPI class
    :param routers_path: Relative path to the routers dir
    :return: None
    """
    conf_db(app, db_url, model_paths)
    include_routers(app, routers_path)
    conf_base_middlewares(app)
