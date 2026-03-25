from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from lxml import etree

from .config import settings
from .identifiers import detect_identifier_type
from .service import UpstreamError, transform_identifier

app = FastAPI(title="Wikidata to DDB Organization XML", version="0.1.0")
ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "static"


def _normalize_xml_bytes(xml_bytes: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_bytes, parser=parser)

    # Canonicalize first to normalize namespace/attribute representation.
    canonical = etree.tostring(root, method="c14n", with_comments=False)

    # Reparse and pretty-print for readable, stable diff output.
    canonical_root = etree.fromstring(canonical, parser=parser)
    return etree.tostring(canonical_root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/organization/{identifier}")
async def get_organization(identifier: str) -> Response:
    try:
        xml_bytes = await transform_identifier(identifier)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc

    normalized = _normalize_xml_bytes(xml_bytes)
    return Response(content=normalized, media_type="application/xml")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/source/{identifier}")
async def get_source(identifier: str) -> Response:
    if detect_identifier_type(identifier) != "ddb_id":
        raise HTTPException(status_code=400, detail="Identifier is not a valid DDB institution ID")

    url = f"{settings.ddb_api_url.rstrip('/')}/items/{identifier}/source/record"
    headers = {"Accept": "application/xml", "User-Agent": settings.user_agent}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers, timeout=30.0)
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=502, detail=f"DDB API request failed: {exc}") from exc

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="No DDB source record found for this ID")
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"DDB API error {resp.status_code}: {resp.text[:300]}")

    try:
        normalized = _normalize_xml_bytes(resp.content)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"DDB API returned non-normalizable XML: {exc}") from exc

    return Response(content=normalized, media_type="application/xml")
