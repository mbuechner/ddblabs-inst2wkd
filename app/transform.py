from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lxml import etree

LANG_MAP = {
    "de": "deu",
    "en": "eng",
    "fr": "fra",
    "es": "spa",
}

SECTOR_MAP = {
    "Q33506": ("http://ddb.vocnet.org/sparte/sparte003", "http://ddb.vocnet.org/sparte/sparte010"),  # museum
    "Q7075": ("http://ddb.vocnet.org/sparte/sparte001", "http://ddb.vocnet.org/sparte/sparte009"),  # library
    "Q856584": ("http://ddb.vocnet.org/sparte/sparte002", "http://ddb.vocnet.org/sparte/sparte011"),  # archive
}
DEFAULT_SECTOR = "http://ddb.vocnet.org/sparte/sparte003"


def _first_claim_value(entity: dict[str, Any], pid: str) -> Any:
    claims = entity.get("claims", {}).get(pid, [])
    for claim in claims:
        mainsnak = claim.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue")
        if datavalue:
            return datavalue.get("value")
    return None


def _all_claim_values(entity: dict[str, Any], pid: str) -> list[Any]:
    values: list[Any] = []
    claims = entity.get("claims", {}).get(pid, [])
    for claim in claims:
        mainsnak = claim.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue")
        if datavalue:
            values.append(datavalue.get("value"))
    return values


def _entity_id(value: Any) -> str | None:
    if isinstance(value, dict) and value.get("entity-type") == "item":
        number = value.get("numeric-id")
        if number is not None:
            return f"Q{number}"
    return None


def _string_value(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, dict):
        if "text" in value:
            text = str(value["text"]).strip()
            return text or None
    return None


def _lang_texts(entity_map: dict[str, Any], key: str) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for input_lang, output_lang in LANG_MAP.items():
        data = entity_map.get(key, {}).get(input_lang)
        if not data:
            continue
        value = data.get("value", "").strip()
        if value:
            result.append((output_lang, value))
    return result


def _parse_modified(entity: dict[str, Any]) -> str:
    modified = entity.get("modified")
    if isinstance(modified, str) and modified:
        return modified
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _pick_sector(entity: dict[str, Any]) -> tuple[str, str | None]:
    p31_values = _all_claim_values(entity, "P31")
    for value in p31_values:
        qid = _entity_id(value)
        if qid and qid in SECTOR_MAP:
            return SECTOR_MAP[qid]
    p452_values = _all_claim_values(entity, "P452")
    for value in p452_values:
        qid = _entity_id(value)
        if qid and qid in SECTOR_MAP:
            return SECTOR_MAP[qid]
    return (DEFAULT_SECTOR, None)


def _social_url(username_or_url: str | None, base_url: str) -> str | None:
    if not username_or_url:
        return None
    value = username_or_url.strip()
    if not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return f"{base_url}{value}"


def _valid_postal_code(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    import re
    return text if re.fullmatch(r"([A-Z]\-)?[0-9]{4,5}", text) else None


def _commons_logo_url(filename: str) -> str:
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename.strip().replace(' ', '_')}"


def build_intermediate_xml(
    qid: str,
    source_ddb_id: str | None,
    entity: dict[str, Any],
    related_entities: dict[str, Any],
) -> etree._Element:
    root = etree.Element("intermediate")

    created = _parse_modified(entity)
    modified = _parse_modified(entity)

    identifier = source_ddb_id or qid
    etree.SubElement(root, "created").text = created
    etree.SubElement(root, "creatorId").text = "admin"
    etree.SubElement(root, "modified").text = modified
    etree.SubElement(root, "modifierId").text = "0"
    etree.SubElement(root, "status").text = "approved"
    etree.SubElement(root, "recordType").text = "ddb-institution"
    etree.SubElement(root, "id").text = identifier
    etree.SubElement(root, "wkdId").text = qid

    org_parent = _entity_id(_first_claim_value(entity, "P749"))
    if org_parent:
        etree.SubElement(root, "orgParent").text = org_parent

    pid_value = _string_value(_first_claim_value(entity, "P791"))
    if pid_value:
        if pid_value.startswith("http://") or pid_value.startswith("https://"):
            etree.SubElement(root, "pid").text = pid_value
        else:
            etree.SubElement(root, "pid").text = f"http://ld.zdb-services.de/resource/organisations/{pid_value}"

    gnd_value = _string_value(_first_claim_value(entity, "P227"))
    if gnd_value:
        if gnd_value.startswith("http://") or gnd_value.startswith("https://"):
            etree.SubElement(root, "authorityId").text = gnd_value
        else:
            etree.SubElement(root, "authorityId").text = f"http://d-nb.info/gnd/{gnd_value}"

    display_names_el = etree.SubElement(root, "displayNames")
    names = _lang_texts(entity, "labels")
    if not names:
        names = [("eng", qid)]
    for lang, value in names:
        item = etree.SubElement(display_names_el, "displayName", lang=lang)
        item.text = value

    abbr_el = etree.SubElement(root, "abbreviations")
    seen_langs: set[str] = set()
    for raw in _all_claim_values(entity, "P1813"):
        if isinstance(raw, dict):
            lang = raw.get("language")
            text = str(raw.get("text", "")).strip()
            mapped_lang = LANG_MAP.get(lang)
            if mapped_lang and text and mapped_lang not in seen_langs:
                item = etree.SubElement(abbr_el, "abbreviation", lang=mapped_lang)
                item.text = text
                seen_langs.add(mapped_lang)

    sector, subsector = _pick_sector(entity)
    etree.SubElement(root, "sector").text = sector
    if subsector:
        etree.SubElement(root, "subsector").text = subsector

    descriptions_el = etree.SubElement(root, "descriptions")
    for lang, value in _lang_texts(entity, "descriptions"):
        item = etree.SubElement(descriptions_el, "description", lang=lang)
        item.text = value

    owner_val = _string_value(_first_claim_value(entity, "P127")) or _string_value(_first_claim_value(entity, "P137")) or _string_value(_first_claim_value(entity, "P859"))
    if owner_val:
        etree.SubElement(root, "fundingAgency").text = owner_val

    legal_val = _string_value(_first_claim_value(entity, "P1454"))
    if legal_val:
        etree.SubElement(root, "legalStatus").text = legal_val

    address_el = etree.SubElement(root, "address")
    street = _string_value(_first_claim_value(entity, "P6375"))
    if street:
        etree.SubElement(address_el, "street").text = street

    house = _string_value(_first_claim_value(entity, "P670"))
    if house:
        etree.SubElement(address_el, "houseIdentifier").text = house

    postal = _valid_postal_code(_string_value(_first_claim_value(entity, "P281")))
    if postal:
        etree.SubElement(address_el, "postalCode").text = postal

    city_qid = _entity_id(_first_claim_value(entity, "P159")) or _entity_id(_first_claim_value(entity, "P131"))
    state_qid = _entity_id(_first_claim_value(entity, "P131"))
    country_qid = _entity_id(_first_claim_value(entity, "P17"))

    def _location_node(parent: etree._Element, tag: str, ref_qid: str | None, fallback_label: str) -> None:
        loc = etree.SubElement(parent, tag)
        uri = f"https://www.wikidata.org/entity/{ref_qid}" if ref_qid else f"https://www.wikidata.org/entity/{qid}"
        loc.set("uri", uri)

        related = related_entities.get(ref_qid or "", {})
        labels = related.get("labels", {}) if isinstance(related, dict) else {}
        de_label = labels.get("de", {}).get("value") if isinstance(labels.get("de"), dict) else None
        en_label = labels.get("en", {}).get("value") if isinstance(labels.get("en"), dict) else None

        if de_label:
            node = etree.SubElement(loc, "label", lang="deu")
            node.text = str(de_label)
        if en_label:
            node = etree.SubElement(loc, "label", lang="eng")
            node.text = str(en_label)
        if not de_label and not en_label:
            node = etree.SubElement(loc, "label", lang="eng")
            node.text = fallback_label

    _location_node(address_el, "city", city_qid, "Unknown city")
    if state_qid:
        _location_node(address_el, "state", state_qid, "Unknown state")
    _location_node(address_el, "country", country_qid, "Unknown country")

    coord_val = _first_claim_value(entity, "P625")
    if isinstance(coord_val, dict):
        lat = float(coord_val.get("latitude", 0.0) or 0.0)
        lon = float(coord_val.get("longitude", 0.0) or 0.0)
        if lat != 0.0 or lon != 0.0:
            coordinates_el = etree.SubElement(address_el, "coordinates")
            etree.SubElement(coordinates_el, "latitude").text = str(lat)
            etree.SubElement(coordinates_el, "longitude").text = str(lon)

    city_label = None
    if city_qid:
        related_city = related_entities.get(city_qid, {})
        labels = related_city.get("labels", {}) if isinstance(related_city, dict) else {}
        city_label = (
            labels.get("de", {}).get("value")
            or labels.get("en", {}).get("value")
            or city_qid
        )
    loc_parts = []
    if street:
        loc_parts.append(street)
    if postal and city_label:
        loc_parts.append(f"{postal} {city_label}")
    elif city_label:
        loc_parts.append(city_label)
    elif postal:
        loc_parts.append(postal)
    if loc_parts:
        etree.SubElement(address_el, "locationDisplayName").text = ", ".join(loc_parts)

    email = _string_value(_first_claim_value(entity, "P968"))
    if email:
        etree.SubElement(root, "email").text = email

    url = _string_value(_first_claim_value(entity, "P856"))
    if url:
        etree.SubElement(root, "url").text = url

    logo = _string_value(_first_claim_value(entity, "P154"))
    if logo:
        etree.SubElement(root, "logo").text = _commons_logo_url(logo)

    tel = _string_value(_first_claim_value(entity, "P1329"))
    if tel:
        etree.SubElement(root, "telephone").text = tel

    fax = _string_value(_first_claim_value(entity, "P2900"))
    if fax:
        etree.SubElement(root, "fax").text = fax

    facebook = _social_url(_string_value(_first_claim_value(entity, "P2013")), "https://www.facebook.com/")
    if facebook:
        etree.SubElement(root, "facebook").text = facebook

    twitter = _social_url(_string_value(_first_claim_value(entity, "P2002")), "https://twitter.com/")
    if twitter:
        etree.SubElement(root, "twitter").text = twitter

    instagram = _social_url(_string_value(_first_claim_value(entity, "P2003")), "https://www.instagram.com/")
    if instagram:
        etree.SubElement(root, "instagram").text = instagram

    return root


def referenced_qids(entity: dict[str, Any]) -> list[str]:
    refs: set[str] = set()
    for pid in ["P159", "P131", "P17", "P749"]:
        for value in _all_claim_values(entity, pid):
            qid = _entity_id(value)
            if qid:
                refs.add(qid)
    return sorted(refs)


def transform_with_xslt(intermediate_xml: etree._Element, xslt_path: Path) -> bytes:
    xslt_doc = etree.parse(str(xslt_path))
    transform = etree.XSLT(xslt_doc)
    source = etree.ElementTree(intermediate_xml)
    result = transform(source)
    return etree.tostring(result, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def validate_output(xml_bytes: bytes, xsd_path: Path) -> list[str]:
    """Validate xml_bytes against the XSD. Returns a list of validation error messages (empty = valid)."""
    xml_doc = etree.fromstring(xml_bytes)
    xsd_doc = etree.parse(str(xsd_path))
    schema = etree.XMLSchema(xsd_doc)
    schema.validate(xml_doc)
    return [str(e.message) for e in schema.error_log]
