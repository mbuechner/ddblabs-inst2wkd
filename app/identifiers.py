import re

QID_PATTERN = re.compile(r"^Q[0-9]+$")
DDB_ID_PATTERN = re.compile(
    r"^(?:[A-Z2-7]{8})*(?:[A-Z2-7]{2}={6}|[A-Z2-7]{4}={4}|[A-Z2-7]{5}={3}|[A-Z2-7]{7}=)?$"
)


def detect_identifier_type(identifier: str) -> str:
    if QID_PATTERN.fullmatch(identifier):
        return "qid"
    if DDB_ID_PATTERN.fullmatch(identifier):
        return "ddb_id"
    return "invalid"
