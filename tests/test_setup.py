# tests/test_app_setup.py

import sys
import importlib
import os
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

import ms_core as ms_module
from ms_core import conf_db, include_routers, setup_app


class DummyApp(FastAPI):
    pass


def test_conf_db_calls_register_tortoise(monkeypatch):
    calls = {}

    def fake_register_tortoise(
        app, db_url, modules, generate_schemas, add_exception_handlers
    ):
        calls["app"] = app
        calls["db_url"] = db_url
        calls["modules"] = modules
        calls["generate_schemas"] = generate_schemas
        calls["add_exception_handlers"] = add_exception_handlers

    # Patch the symbol *inside* ms_core where conf_db imported it
    mod = importlib.import_module(conf_db.__module__)
    monkeypatch.setattr(mod, "register_tortoise", fake_register_tortoise)

    app = DummyApp()
    conf_db(app, db_url="sqlite://:memory:", model_paths=["models.foo"])

    assert calls["app"] is app
    assert calls["db_url"] == "sqlite://:memory:"
    assert calls["modules"] == {"models": ["models.foo"]}
    assert calls["generate_schemas"] is True
    assert calls["add_exception_handlers"] is True


def test_include_routers_non_directory(tmp_path):
    app = DummyApp()
    not_a_dir = tmp_path / "nope"
    with pytest.raises(ValueError):
        include_routers(app, not_a_dir)


def test_include_routers_loads_only_py_routers(tmp_path, monkeypatch):
    # Create a temporary project structure under tmp_path
    project_dir = tmp_path / "proj"
    routers_dir = project_dir / "routers"
    routers_dir.mkdir(parents=True)
    # __init__.py files to make it a package
    (project_dir / "__init__.py").write_text("")
    (routers_dir / "__init__.py").write_text("")

    # valid router
    (routers_dir / "valid.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/ping')\n"
        "def ping(): return {'pong': True}\n"
    )
    # ignored
    (routers_dir / "_hidden.py").write_text("router = None")
    (routers_dir / "README.md").write_text("")

    # Change cwd to tmp_path so Path.parts are relative
    monkeypatch.chdir(tmp_path)
    sys.path.insert(0, str(tmp_path))
    try:
        app = DummyApp()
        include_routers(app, Path("proj") / "routers")

        paths = {route.path for route in app.router.routes}  # type: ignore
        assert "/ping" in paths
        assert all(not p.startswith("/_hidden") for p in paths)
    finally:
        sys.path.pop(0)


def test_setup_app_combines_conf_and_include_and_returns_config(monkeypatch, tmp_path):
    # Dynamically patch conf_db, include_routers, and generate_config in the same module as setup_app
    setup_mod = importlib.import_module(setup_app.__module__)
    called = {}

    def fake_conf_db(app, db_url, model_paths=None):
        called["conf_db"] = (app, db_url, model_paths)

    def fake_include_routers(app, routers_path):
        called["include_routers"] = (app, routers_path)

    def fake_generate_config(db_url, app_modules):
        return {"db_url": db_url, "app_modules": app_modules}

    monkeypatch.setattr(setup_mod, "conf_db", fake_conf_db)
    monkeypatch.setattr(setup_mod, "include_routers", fake_include_routers)
    monkeypatch.setattr(setup_mod, "generate_config", fake_generate_config)

    app = DummyApp()
    db_url = "sqlite://:memory:"
    routers_path = tmp_path / "routers"
    routers_path.mkdir()

    result = setup_app(app, db_url, routers_path, model_paths=["models.test"])

    assert called["conf_db"] == (app, db_url, ["models.test"])
    assert called["include_routers"] == (app, routers_path)
    assert result == {
        "db_url": db_url,
        "app_modules": {"models": ["models.test"]},
    }
