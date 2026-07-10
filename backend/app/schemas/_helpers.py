"""Pydantic 与 ORM 边界共用工具。"""
from typing import Any


def orm_to_metadata_dict(data: Any) -> Any:
  if isinstance(data, dict):
    return data
  d = {}
  if hasattr(data, "__dict__"):
    d = dict(data.__dict__)
    d.pop("_sa_instance_state", None)
  if hasattr(data, "metadata_"):
    d["metadata"] = data.metadata_ or {}
  return d
