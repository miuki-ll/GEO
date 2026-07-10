"""Beauty local IndustryPack implementation."""
from __future__ import annotations

from typing import Any, Dict, List

from app.agents.industry.base import IndustryPack
from app.agents.industry.packs.beauty_local import templates as tpl


class BeautyLocalPack(IndustryPack):
    code = "beauty_local"
    name = "生美本地 · 皮肤管理"

    def forbidden_words(self) -> List[str]:
        return list(tpl.BEAUTY_LOCAL_FORBIDDEN_WORDS)

    def channel_weights(self) -> List[Dict[str, Any]]:
        return list(tpl.BEAUTY_LOCAL_CHANNEL_WEIGHTS)

    def default_persona(self) -> Dict[str, Any]:
        return dict(tpl.BEAUTY_LOCAL_DEFAULT_PERSONA)

    def fact_templates(self) -> List[Dict[str, Any]]:
        return list(tpl.BEAUTY_LOCAL_FACT_TEMPLATES)

    def scenario_templates(self) -> List[Dict[str, Any]]:
        return list(tpl.BEAUTY_LOCAL_SCENARIO_TEMPLATES)

    def compliance_checklist(self) -> List[str]:
        return list(tpl.BEAUTY_LOCAL_COMPLIANCE_CHECKLIST)
