from __future__ import annotations  # no installation needed

import json  # no installation needed
import re  # no installation needed
from typing import Any  # no installation needed


def slugify(text: str) -> str:
    value = text.strip().lower()
    if not value:
        return ""
    value = value.replace("_", " ")
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s-]+", "-", value)
    return value.strip("-")


def infer_icp_and_use_cases(text: str) -> list[str]:
    value = text.lower()
    suggestions: list[str] = []

    if "workflow" in value:
        suggestions.append("Ops/operations teams")
    if "analytics" in value or "dashboard" in value:
        suggestions.append("Data/BI teams")
    if "billing" in value or "invoicing" in value:
        suggestions.append("Finance teams")
    if "crm" in value or "sales" in value:
        suggestions.append("Sales teams")
    if "compliance" in value:
        suggestions.append("Finance/ops/compliance teams")

    if not suggestions:
        base = text.strip() or "this solution"
        suggestions.append(f"Teams/SMBs needing {base}")

    return suggestions


def _format_list(values: list[str]) -> str:
    return ", ".join(values) if values else "None"


def render_dossier_md(rec: dict[str, Any]) -> str:
    company_name = rec.get("company_name") or "Unknown"
    description = rec.get("description") or ""
    source = rec.get("source") or "unknown"
    source_url = rec.get("source_url") or ""
    website = rec.get("website") or ""
    discovered_at = rec.get("discovered_at") or ""
    filter_score = rec.get("filter_score")
    filter_reasons = rec.get("filter_reasons") or []
    signals = rec.get("signals") or {}

    icp = infer_icp_and_use_cases(f"{company_name} {description}".strip())
    signals_text = json.dumps(signals, indent=2, sort_keys=True, ensure_ascii=True)
    reasons_text = _format_list(list(filter_reasons))

    return "\n".join(
        [
            f"# {company_name}",
            "",
            "## Snapshot",
            f"- Name: {company_name}",
            f"- Source: {source}",
            f"- Source URL: {source_url}",
            f"- Website: {website}",
            f"- Discovered At: {discovered_at}",
            "",
            "## What it appears to do",
            description or "No description available.",
            "",
            "## ICP & Use-cases",
            *[f"- {item}" for item in icp],
            "",
            "## Why interesting",
            f"- Filter Score: {filter_score}",
            f"- Filter Reasons: {reasons_text}",
            "- Signals:",
            "```json",
            signals_text,
            "```",
            "",
            "## Unknowns/Risks",
            "- [ ] Business model clarity",
            "- [ ] Competitive landscape",
            "- [ ] Data quality and freshness",
            "",
            "## Next diligence questions",
            "- [ ] Who is the ideal customer?",
            "- [ ] What pain does it solve today?",
            "- [ ] How do they acquire customers?",
            "",
        ]
    )
