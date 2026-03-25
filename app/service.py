from __future__ import annotations

import logging
from pathlib import Path

import httpx

from .identifiers import detect_identifier_type
from .transform import (
    build_intermediate_xml,
    referenced_qids,
    transform_with_xslt,
    validate_output,
)
from .wikidata import UpstreamError, fetch_entities, fetch_entity, resolve_qid_from_ddb_id

log = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
XSLT_PATH = ROOT_DIR / "resources" / "transform.xslt"
XSD_PATH = ROOT_DIR / "resources" / "schemas" / "ddb-organization.xsd"


async def transform_identifier(identifier: str) -> bytes:
    identifier_type = detect_identifier_type(identifier)
    if identifier_type == "invalid":
        raise ValueError("Identifier must be a Q-ID or a valid DDB institution ID")

    async with httpx.AsyncClient() as client:
        if identifier_type == "qid":
            qid = identifier
            source_ddb_id = None
        else:
            source_ddb_id = identifier
            qid = await resolve_qid_from_ddb_id(client, identifier)
            if not qid:
                raise LookupError("No Wikidata item found for the given DDB institution ID")

        entity = await fetch_entity(client, qid)
        refs = referenced_qids(entity)
        related = await fetch_entities(client, refs)

    intermediate = build_intermediate_xml(qid, source_ddb_id, entity, related)
    xml_bytes = transform_with_xslt(intermediate, XSLT_PATH)
    errors = validate_output(xml_bytes, XSD_PATH)
    if errors:
        for msg in errors:
            log.warning("XSD validation warning for %s: %s", identifier, msg)
    return xml_bytes


__all__ = ["transform_identifier", "UpstreamError"]
