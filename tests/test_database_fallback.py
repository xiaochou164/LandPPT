import importlib
import sys
from contextlib import contextmanager

import pytest
from sqlalchemy.exc import OperationalError


DB_MODULE_NAME = "landppt.database.database"
MAIN_MODULE_NAME = "landppt.main"
CONFIG_MODULE_NAME = "landppt.core.config"
LEGACY_POSTGRES_URL = "postgresql://landppt:***@postgres:5432/landppt"


def _reload_database_module(monkeypatch, database_url=None):
    if database_url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", database_url)
    sys.modules.pop(CONFIG_MODULE_NAME, None)
    sys.modules.pop(DB_MODULE_NAME, None)
    return importlib.import_module(DB_MODULE_NAME)


def _reload_config_module(monkeypatch, database_url=None):
    if database_url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", database_url)
    sys.modules.pop(CONFIG_MODULE_NAME, None)
    return importlib.import_module(CONFIG_MODULE_NAME)


def test_database_module_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    from landppt.core.config import AppConfig

    config = AppConfig()
    assert config.database_url == "sqlite:///./landppt.db"


def test_app_config_prefers_exported_database_url_over_dotenv(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".env").write_text("DATABASE_URL=sqlite:///./landppt.db\n", encoding="utf-8")

    monkeypatch.chdir(repo_root)

    config_module = _reload_config_module(
        monkeypatch,
        database_url="postgresql://landppt:***@postgres:5432/landppt",
    )

    assert config_module.AppConfig().database_url == "postgresql://landppt:***@postgres:5432/landppt"


def test_app_config_uses_dotenv_database_url_when_env_is_unset(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".env").write_text("DATABASE_URL=postgresql://dev:***@localhost:5432/landppt\n", encoding="utf-8")

    monkeypatch.chdir(repo_root)

    config_module = _reload_config_module(monkeypatch)

    assert config_module.AppConfig().database_url == "postgresql://dev:***@localhost:5432/landppt"


def test_should_fallback_for_legacy_postgres_connectivity_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    module = _reload_database_module(monkeypatch)

    err = OperationalError(
        "SELECT 1",
        {},
        Exception('could not translate host name "postgres" to address: Name or service not known'),
    )

    assert module._should_fallback_to_sqlite(err, LEGACY_POSTGRES_URL) is True


def test_should_not_fallback_for_explicit_custom_postgres_connectivity_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    module = _reload_database_module(monkeypatch)
    custom_url = "postgresql://landppt:landppt@db.internal:5432/landppt"

    err = OperationalError(
        "SELECT 1",
        {},
        Exception("connection refused"),
    )

    assert module._should_fallback_to_sqlite(err, custom_url) is False


@pytest.mark.asyncio
async def test_startup_initialization_runs_in_order(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    sys.modules.pop(CONFIG_MODULE_NAME, None)
    sys.modules.pop(DB_MODULE_NAME, None)
    sys.modules.pop(MAIN_MODULE_NAME, None)
    import landppt.main as main_module

    calls = []

    async def fake_run_startup_initialization():
        calls.append("run_startup_initialization")
        return True

    monkeypatch.setattr(main_module, "run_startup_initialization", fake_run_startup_initialization)

    await main_module.startup_event()

    assert calls == ["run_startup_initialization"]
