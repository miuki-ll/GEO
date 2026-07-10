"""Industry pack registry."""
from __future__ import annotations

from typing import Dict, Optional

from app.agents.industry.base import IndustryPack
from app.agents.industry.packs.beauty_local.pack import BeautyLocalPack

_REGISTRY: Dict[str, IndustryPack] = {
    BeautyLocalPack.code: BeautyLocalPack(),
}


def get_industry_pack(code: str) -> Optional[IndustryPack]:
    return _REGISTRY.get(code)


def list_industry_packs() -> list[dict]:
    return [{"code": p.code, "name": p.name} for p in _REGISTRY.values()]
