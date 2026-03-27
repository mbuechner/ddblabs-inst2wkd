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


def _all_claims(entity: dict[str, Any], pid: str) -> list[dict[str, Any]]:
    claims = entity.get("claims", {}).get(pid, [])
    return [claim for claim in claims if isinstance(claim, dict)]


def _snak_value(snak: dict[str, Any]) -> Any:
    datavalue = snak.get("datavalue")
    if isinstance(datavalue, dict):
        return datavalue.get("value")
    return None


def _first_qualifier_value(claim: dict[str, Any], pid: str) -> Any:
    qualifiers = claim.get("qualifiers", {})
    qualifier_snaks = qualifiers.get(pid, []) if isinstance(qualifiers, dict) else []
    for snak in qualifier_snaks:
        if isinstance(snak, dict):
            value = _snak_value(snak)
            if value is not None:
                return value
    return None


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


def _label_for_qid(related_entities: dict[str, Any], qid: str) -> str | None:
    related = related_entities.get(qid, {})
    labels = related.get("labels", {}) if isinstance(related, dict) else {}
    for lang in ("de", "en", "fr", "es"):
        label_obj = labels.get(lang)
        label = label_obj.get("value") if isinstance(label_obj, dict) else None
        if label:
            return str(label)
    return None


def _pick_sector(entity: dict[str, Any], related_entities: dict[str, Any]) -> str | None:
    for pid in ("P31", "P452"):
        for value in _all_claim_values(entity, pid):
            qid = _entity_id(value)
            if qid:
                label = _label_for_qid(related_entities, qid) or qid
                return f"{pid}: {label}"
    return None


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

    source_ddb_id = f"https://www.deutsche-digitale-bibliothek.de/organization/{source_ddb_id}" if source_ddb_id else None

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
    etree.SubElement(root, "wkdId").text =  f"https://www.wikidata.org/wiki/{qid}"

    org_parent = _entity_id(_first_claim_value(entity, "P749"))
    if org_parent:
        etree.SubElement(root, "orgParent").text = f"https://www.wikidata.org/wiki/{org_parent}"

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

    sector = _pick_sector(entity, related_entities)
    if sector:
        etree.SubElement(root, "sector").text = sector

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

    p159_claims = _all_claims(entity, "P159")
    addresses_el = etree.SubElement(root, "addresses")

    def _location_node(parent: etree._Element, tag: str, ref_qid: str | None) -> None:
        if not ref_qid:
            return
        loc = etree.SubElement(parent, tag)
        loc.set("uri", f"https://www.wikidata.org/entity/{ref_qid}")

        related = related_entities.get(ref_qid, {})
        labels = related.get("labels", {}) if isinstance(related, dict) else {}

        for input_lang, output_lang in LANG_MAP.items():
            lang_obj = labels.get(input_lang)
            label_value = lang_obj.get("value") if isinstance(lang_obj, dict) else None
            if label_value:
                node = etree.SubElement(loc, "label", lang=output_lang)
                node.text = str(label_value)

    def _build_address(
        street: str | None,
        house: str | None,
        postal: str | None,
        city_qid: str | None,
        state_qid: str | None,
        country_qid: str | None,
        coord_val: Any,
    ) -> None:
        address_el = etree.SubElement(addresses_el, "address")

        if street:
            etree.SubElement(address_el, "street").text = street

        if house:
            etree.SubElement(address_el, "houseIdentifier").text = house

        if postal:
            etree.SubElement(address_el, "postalCode").text = postal

        _location_node(address_el, "city", city_qid)
        if state_qid:
            _location_node(address_el, "state", state_qid)
        _location_node(address_el, "country", country_qid)

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
                (labels.get("de") or {}).get("value")
                or (labels.get("en") or {}).get("value")
                or (labels.get("fr") or {}).get("value")
                or (labels.get("es") or {}).get("value")
                or city_qid
            )

        loc_parts: list[str] = []
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

    if p159_claims:
        for claim in p159_claims:
            city_qid = _entity_id(_snak_value(claim.get("mainsnak", {})))
            street = _string_value(_first_qualifier_value(claim, "P6375"))
            house = _string_value(_first_qualifier_value(claim, "P670"))
            postal = _valid_postal_code(_string_value(_first_qualifier_value(claim, "P281")))
            state_qid = _entity_id(_first_qualifier_value(claim, "P131"))
            country_qid = _entity_id(_first_qualifier_value(claim, "P17"))
            coord_val = _first_qualifier_value(claim, "P625")
            _build_address(street, house, postal, city_qid, state_qid, country_qid, coord_val)
    else:
        # Backup path: legacy top-level properties when no P159 statement exists.
        street = _string_value(_first_claim_value(entity, "P6375"))
        house = _string_value(_first_claim_value(entity, "P670"))
        postal = _valid_postal_code(_string_value(_first_claim_value(entity, "P281")))
        city_qid = _entity_id(_first_claim_value(entity, "P131"))
        state_qid = _entity_id(_first_claim_value(entity, "P131"))
        country_qid = _entity_id(_first_claim_value(entity, "P17"))
        coord_val = _first_claim_value(entity, "P625")
        _build_address(street, house, postal, city_qid, state_qid, country_qid, coord_val)

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
    for pid in ["P159", "P131", "P17", "P749", "P31", "P452"]:
        for value in _all_claim_values(entity, pid):
            qid = _entity_id(value)
            if qid:
                refs.add(qid)

    for claim in _all_claims(entity, "P159"):
        for pid in ["P131", "P17"]:
            qid = _entity_id(_first_qualifier_value(claim, pid))
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
