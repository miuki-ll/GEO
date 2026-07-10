"""L3 IndustryPack — 垂域包接口（Industry Pack interface）。"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IndustryPack(ABC):
    code: str
    name: str

    @abstractmethod
    def forbidden_words(self) -> List[str]: ...

    @abstractmethod
    def channel_weights(self) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def default_persona(self) -> Dict[str, Any]: ...

    @abstractmethod
    def fact_templates(self) -> List[Dict[str, Any]]: ...

    @abstractmethod
    def scenario_templates(self) -> List[Dict[str, Any]]: ...

    def compliance_checklist(self) -> List[str]:
        return []

    def templates(self) -> Dict[str, Any]:
        return {
            "forbidden_words": self.forbidden_words(),
            "channel_weights": self.channel_weights(),
            "default_persona": self.default_persona(),
            "fact_templates": self.fact_templates(),
            "scenario_templates": self.scenario_templates(),
            "compliance_checklist": self.compliance_checklist(),
        }
