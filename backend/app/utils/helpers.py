import json
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_uuid(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex}"


def now_utc() -> datetime:
    return datetime.utcnow()


def safe_json_loads(s: Optional[str], default=None) -> Any:
    if not s:
        return default
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any) -> str:
    def default_serializer(o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        if isinstance(o, set):
            return list(o)
        if hasattr(o, "__dict__"):
            return o.__dict__
        return str(o)

    return json.dumps(obj, ensure_ascii=False, default=default_serializer)


def truncate(text: str, max_len: int = 200, suffix: str = "...") -> str:
    if not text or len(text) <= max_len:
        return text or ""
    return text[: max_len - len(suffix)] + suffix


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return email
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        return name[0] + "***@" + domain
    return name[:2] + "***" + name[-1:] + "@" + domain


def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def parse_list_from_str(s: Optional[str]) -> List[Any]:
    if not s:
        return []
    return safe_json_loads(s, [])


def ensure_json_list(value: Any) -> List[Any]:
    """Normalize ORM JSON / legacy string JSON to list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return parse_list_from_str(value)
    return list(value) if value else []


def ensure_json_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        loaded = safe_json_loads(value, {})
        return loaded if isinstance(loaded, dict) else {}
    return {}


def to_list_str(items: List[Any]) -> str:
    return safe_json_dumps(items)


def hash_password(raw: str) -> str:
    return pwd_context.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd_context.verify(raw, hashed)
