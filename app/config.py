import os

from dotenv import load_dotenv

load_dotenv()


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def mongodb_uri() -> str:
    return os.getenv("MONGODB_URI", "").strip()


def mongodb_db() -> str:
    return os.getenv("MONGODB_DB", "astra_charms")


def astra_api_key() -> str:
    return os.getenv("ASTRA_API_KEY", "").strip()


def astra_base_url() -> str:
    return os.getenv("ASTRA_BASE_URL", "").strip().rstrip("/")


def astra_model() -> str:
    return os.getenv("ASTRA_MODEL", "astra-6")


def voyage_api_key() -> str:
    return os.getenv("VOYAGE_API_KEY", "").strip()


def voyage_model() -> str:
    return os.getenv("VOYAGE_MODEL", "voyage-3")


def mock_llm() -> bool:
    return _flag("MOCK_LLM", "true")


def export_dir() -> str:
    return os.getenv("EXPORT_DIR", "exports")
