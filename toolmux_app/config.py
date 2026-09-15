from pathlib import Path
import os

from dotenv import load_dotenv

VERSION = "0.2.0"
AUTHOR = "Olliv3r"
APP_NAME = "Toolmux"
TERMUX_DIR = Path("/data/data/com.termux/files")
TERMUX_HOME = TERMUX_DIR / "home"


def _load_environment() -> Path | None:
    """Load Toolmux configuration from .env without overriding shell variables.

    Lookup order:
    1. TOOLMUX_ENV_FILE, when explicitly set;
    2. .env in the current working directory;
    3. .env beside the project root (development checkout).

    Real environment variables always win over values from the file.
    """

    explicit = os.environ.get("TOOLMUX_ENV_FILE")
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    else:
        candidates.extend(
            [
                Path.cwd() / ".env",
                Path(__file__).resolve().parent.parent / ".env",
            ]
        )

    for candidate in candidates:
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            return candidate
    return None


_SHELL_API_TOKEN = os.environ.get("TOOLMUX_API_TOKEN")
_SHELL_API_PASSWORD = os.environ.get("TOOLMUX_API_PASSWORD")
ENV_FILE = _load_environment()

API_BASE_URL = os.environ.get(
    "TOOLMUX_API_BASE_URL", "https://toolmuxapp.pythonanywhere.com/api/v1"
).rstrip("/")
API_TOKEN = (
    _SHELL_API_TOKEN
    or _SHELL_API_PASSWORD
    or os.environ.get("TOOLMUX_API_TOKEN")
    or os.environ.get("TOOLMUX_API_PASSWORD", "")
)
API_PASSWORD = API_TOKEN  # backward-compatible internal alias
CATALOG_URL = f"{API_BASE_URL}/catalog"
BUG_REPORT_URL = f"{API_BASE_URL}/reports/bugs"
CATALOG_SCHEMA_VERSION = 2
CATALOG_CONTRACT_VERSION = "2.0"
CATALOG_TIMEOUT = float(os.environ.get("TOOLMUX_CATALOG_TIMEOUT", "4"))
ALLOW_OFFLINE_CACHE = os.environ.get("TOOLMUX_ALLOW_OFFLINE_CACHE", "0").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
CACHE_DIR = Path(os.environ.get("TOOLMUX_CACHE_DIR", Path.home() / ".cache" / "toolmux"))
CATALOG_CACHE_PATH = CACHE_DIR / "catalog.json"
CATALOG_ETAG_PATH = CACHE_DIR / "catalog.etag"
