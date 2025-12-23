from __future__ import annotations  # no installation needed

from dataclasses import dataclass, field  # no installation needed
from typing import Optional  # no installation needed


@dataclass
class Lead:
    source: str
    source_url: str
    discovered_at: str
    company_name: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    signals: dict[str, object] = field(default_factory=dict)
    raw: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "source_url": self.source_url,
            "discovered_at": self.discovered_at,
            "company_name": self.company_name,
            "website": self.website,
            "description": self.description,
            "signals": dict(self.signals),
            "raw": dict(self.raw),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Lead":
        if not isinstance(data, dict):
            raise ValueError("Lead data must be a dict.")

        required_fields = ("source", "source_url", "discovered_at")
        for key in required_fields:
            if key not in data:
                raise ValueError(f"Missing required field: {key}")
            if not isinstance(data.get(key), str):
                raise ValueError(f"Field '{key}' must be a string.")

        def _optional_str(key: str) -> Optional[str]:
            value = data.get(key)
            if value is None:
                return None
            if not isinstance(value, str):
                raise ValueError(f"Field '{key}' must be a string or None.")
            return value

        signals = data.get("signals", {})
        raw = data.get("raw", {})
        if signals is None:
            signals = {}
        if raw is None:
            raw = {}
        if not isinstance(signals, dict):
            raise ValueError("Field 'signals' must be a dict.")
        if not isinstance(raw, dict):
            raise ValueError("Field 'raw' must be a dict.")

        return cls(
            source=data["source"],
            source_url=data["source_url"],
            discovered_at=data["discovered_at"],
            company_name=_optional_str("company_name"),
            website=_optional_str("website"),
            description=_optional_str("description"),
            signals=dict(signals),
            raw=dict(raw),
        )
