# Wikidata -> DDB Organization XML Service

Minimaler Webservice mit FastAPI, der einen Identifier annimmt, den passenden Wikidata-Datensatz lädt und als XML im Format von `resources/schemas/ddb-organization.xsd` zurückgibt.

## Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Docker

Image bauen:

```bash
docker build -t ddblabs-inst2wd:latest .
```

Container starten:

```bash
docker run --rm -p 8080:8080 --env-file .env ddblabs-inst2wd:latest
```

## OpenShift (non-root)

- Das Image startet als non-root User (`USER 1001`).
- Dateirechte sind OpenShift-kompatibel gesetzt (`chgrp 0` und `chmod g=u`), damit auch ein arbiträrer UID-Kontext mit Root-Gruppe lesen/ausführen kann.
- Der Service lauscht auf `0.0.0.0:${PORT}` (Standard `8080`).

## Environment

```bash
# Required User-Agent components
CLIENT_NAME=ddblabs-inst2wd
CLIENT_VERSION=0.1.0
CLIENT_CONTACT=you@example.org

# Wikidata endpoints
WIKIDATA_SPARQL_URL=https://query.wikidata.org/sparql
WIKIDATA_API_URL=https://www.wikidata.org/w/api.php
```

Der ausgehende `User-Agent` wird im Format gebaut:

`<client>/<version> (<contact information>) <library/framework>/<version> [<library>/<version> ...]`

Beispiel:

`ddblabs-inst2wd/0.1.0 (you@example.org) FastAPI/0.116.1 httpx/0.28.1 lxml/6.0.1`

## Endpoint

`GET /organization/{identifier}`

Identifier-Varianten:
- Q-ID: `Q[0-9]+`
- DDB institution ID: `^(?:[A-Z2-7]{8})*(?:[A-Z2-7]{2}={6}|[A-Z2-7]{4}={4}|[A-Z2-7]{5}={3}|[A-Z2-7]{7}=)?$`

Beispiel:

```bash
curl http://127.0.0.1:8000/organization/Q42
```

Antwort: `application/xml`

## Verhalten

- `recordType` wird im MVP immer auf `ddb-institution` gesetzt.
- Bei fehlenden Pflichtdaten wird Best-Effort mit Fallbackwerten genutzt.
- Ausgabe wird gegen `resources/schemas/ddb-organization.xsd` validiert.
- Die Aufloesung von DDB-ID nach Q-ID nutzt priorisiert den SPARQL-Endpunkt (`P13081`).
