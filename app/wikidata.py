from __future__ import annotations
from typing import Any
import httpx
from .config import settings

WIKIDATA_SPARQL_URL = settings.wikidata_sparql_url
WIKIDATA_API_URL = settings.wikidata_api_url
USER_AGENT = settings.user_agent

class UpstreamError(Exception):
    pass


def _check_api_error(payload: dict[str, Any]) -> None:
    """Raise UpstreamError if Wikidata returned a JSON-level error (HTTP 200 but error key present)."""
    err = payload.get("error")
    if err:
        raise UpstreamError(f"Wikidata API error ({err.get('code', 'unknown')}): {err.get('info', '')}")


def _wikidata_headers(accept: str | None = None) -> dict[str, str]:
    headers: dict[str, str] = {"User-Agent": USER_AGENT}
    if accept:
        headers["Accept"] = accept

    token = settings.wikidata_access_token.strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def resolve_qid_from_ddb_id(client: httpx.AsyncClient, ddb_id: str) -> str | None:
    # SPARQL is the primary and mandatory path for DDB-ID -> QID resolution.
    query = """
    SELECT ?item WHERE {
      ?item wdt:P13081 ?ddbId .
      FILTER(STR(?ddbId) = STR(%(ddb_id)s))
    }
    LIMIT 1
    """
    params = {
        "query": query % {"ddb_id": f'"{ddb_id}"'},
        "format": "json",
    }
    headers = _wikidata_headers("application/sparql-results+json")
    resp = await client.get(WIKIDATA_SPARQL_URL, params=params, headers=headers, timeout=30.0)
    if resp.status_code >= 400:
        raise UpstreamError(f"SPARQL request failed with status {resp.status_code}")

    payload = resp.json()
    bindings = payload.get("results", {}).get("bindings", [])
    if not bindings:
        return None

    item_uri = bindings[0].get("item", {}).get("value", "")
    if "/entity/Q" not in item_uri:
        return None
    return item_uri.rsplit("/", 1)[-1]


async def fetch_entity(client: httpx.AsyncClient, qid: str) -> dict[str, Any]:
    headers = _wikidata_headers()
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": qid,
        "props": "labels|descriptions|claims|sitelinks|info",
        "languages": "de|en|fr|es",
    }
    resp = await client.get(WIKIDATA_API_URL, params=params, headers=headers, timeout=30.0)
    if resp.status_code >= 400:
        raise UpstreamError(f"Wikidata entity request failed with status {resp.status_code}")

    payload = resp.json()
    _check_api_error(payload)

    entity = payload.get("entities", {}).get(qid)
    if entity is None or "missing" in entity:
        raise LookupError(f"Wikidata item not found: {qid}")
    return entity


async def fetch_entities(client: httpx.AsyncClient, qids: list[str]) -> dict[str, Any]:
    if not qids:
        return {}

    headers = _wikidata_headers()
    params = {
        "action": "wbgetentities",
        "format": "json",
        "ids": "|".join(sorted(set(qids))),
        "props": "labels|claims",
        "languages": "de|en|fr|es",
    }
    resp = await client.get(WIKIDATA_API_URL, params=params, headers=headers, timeout=30.0)
    if resp.status_code >= 400:
        raise UpstreamError(f"wbgetentities failed with status {resp.status_code}")

    payload = resp.json()
    _check_api_error(payload)
    return payload.get("entities", {})
