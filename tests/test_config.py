import importlib
from pathlib import Path

import toolmux_app.config as config


_ENV_KEYS = [
    "TOOLMUX_ENV_FILE",
    "TOOLMUX_API_BASE_URL",
    "TOOLMUX_API_TOKEN",
    "TOOLMUX_API_PASSWORD",
    "TOOLMUX_ALLOW_OFFLINE_CACHE",
    "TOOLMUX_CATALOG_TIMEOUT",
    "TOOLMUX_CACHE_DIR",
]


def _clear_toolmux_env(monkeypatch):
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_dotenv_configures_local_api_and_token(tmp_path, monkeypatch):
    _clear_toolmux_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "TOOLMUX_API_BASE_URL=http://127.0.0.1:5050/api/v1\n"
        "TOOLMUX_API_TOKEN=local-secret\n"
        "TOOLMUX_ALLOW_OFFLINE_CACHE=1\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    reloaded = importlib.reload(config)

    assert reloaded.ENV_FILE == env_file
    assert reloaded.API_BASE_URL == "http://127.0.0.1:5050/api/v1"
    assert reloaded.CATALOG_URL == "http://127.0.0.1:5050/api/v1/catalog"
    assert reloaded.BUG_REPORT_URL == "http://127.0.0.1:5050/api/v1/reports/bugs"
    assert reloaded.API_TOKEN == "local-secret"
    assert reloaded.ALLOW_OFFLINE_CACHE is True


def test_shell_environment_has_precedence_over_dotenv(tmp_path, monkeypatch):
    _clear_toolmux_env(monkeypatch)
    (tmp_path / ".env").write_text(
        "TOOLMUX_API_BASE_URL=http://127.0.0.1:5000/api/v1\n"
        "TOOLMUX_API_TOKEN=file-token\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOOLMUX_API_BASE_URL", "http://10.0.2.2:9000/api/v1")
    monkeypatch.setenv("TOOLMUX_API_TOKEN", "shell-token")

    reloaded = importlib.reload(config)

    assert reloaded.API_BASE_URL == "http://10.0.2.2:9000/api/v1"
    assert reloaded.API_TOKEN == "shell-token"


def test_explicit_env_file_is_supported(tmp_path, monkeypatch):
    _clear_toolmux_env(monkeypatch)
    custom = tmp_path / "toolmux.env"
    custom.write_text(
        "TOOLMUX_API_BASE_URL=http://localhost:7000/api/v1\n"
        "TOOLMUX_API_TOKEN=custom-token\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TOOLMUX_ENV_FILE", str(custom))

    reloaded = importlib.reload(config)

    assert reloaded.ENV_FILE == custom
    assert reloaded.API_BASE_URL == "http://localhost:7000/api/v1"
    assert reloaded.API_TOKEN == "custom-token"


def test_legacy_api_password_remains_fallback(tmp_path, monkeypatch):
    _clear_toolmux_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TOOLMUX_API_PASSWORD", "legacy-secret")

    reloaded = importlib.reload(config)

    assert reloaded.API_TOKEN == "legacy-secret"
