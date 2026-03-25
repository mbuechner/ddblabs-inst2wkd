from __future__ import annotations

import os
from importlib.metadata import version
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _pkg_version(name: str) -> str:
    try:
        return version(name)
    except Exception:
        return "unknown"


class Settings:
    def __init__(self) -> None:
        self.client_name = os.getenv("CLIENT_NAME", "ddblabs-inst2wd")
        self.client_version = os.getenv("CLIENT_VERSION", "0.1.0")
        self.contact_info = os.getenv("CLIENT_CONTACT", "contact:local-dev")

        self.wikidata_sparql_url = os.getenv("WIKIDATA_SPARQL_URL", "https://query.wikidata.org/sparql")
        self.wikidata_api_url = os.getenv("WIKIDATA_API_URL", "https://www.wikidata.org/w/api.php")
        self.wikidata_client_id = os.getenv("WIKIDATA_CLIENT_ID", "")
        self.wikidata_client_secret = os.getenv("WIKIDATA_CLIENT_SECRET", "")
        self.wikidata_access_token = os.getenv("WIKIDATA_ACCESS_TOKEN", "")

        self.ddb_api_url = os.getenv("DDB_API_URL", "https://api.deutsche-digitale-bibliothek.de/2")

    @property
    def user_agent(self) -> str:
        # Required format:
        # <client>/<version> (<contact>) <framework>/<version> [<library>/<version> ...]
        framework = f"FastAPI/{_pkg_version('fastapi')}"
        libraries = [
            f"httpx/{_pkg_version('httpx')}",
            f"lxml/{_pkg_version('lxml')}",
        ]
        return (
            f"{self.client_name}/{self.client_version} ({self.contact_info}) "
            f"{framework} {' '.join(libraries)}"
        )


settings = Settings()
