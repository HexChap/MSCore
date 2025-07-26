import os
from pathlib import Path

import uvicorn as uvicorn
from fastapi import FastAPI

from ms_core import setup_app

root = Path(__file__).parent.parent / "tests"

application = FastAPI(
    title="TemplateMicroservice",
)

models = ["aerich.models"]
for app_dir in os.listdir(root / "models"):
    if not app_dir.startswith("_"):
        models.append(f"tests.models.{app_dir.removesuffix('.py')}")

tortoise_conf = setup_app(
    application,
    "asyncpg://postgres:postgres@localhost:54320/mscore_test",
    Path("tests") / "routers",
    models,
)


if __name__ == "__main__":
    uvicorn.run("test:application", port=8000, reload=True)
