from __future__ import annotations  # no installation needed

import json  # no installation needed
from datetime import date  # no installation needed
from pathlib import Path  # no installation needed
from typing import Any  # no installation needed

from ...config import ProjectConfig  # no installation needed
from .filter_rules import score_text  # no installation needed


def load_ndjson(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"NDJSON record must be a dict: {path}")
            records.append(record)
    return records


def write_ndjson(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=True))
            f.write("\n")


def _text_for_record(record: dict[str, Any]) -> str:
    company_name = record.get("company_name") or ""
    description = record.get("description") or ""
    raw = record.get("raw") or {}
    return f"{company_name} {description} {raw}".lower()


def score_record(rec: dict[str, Any]) -> dict[str, object]:
    text = _text_for_record(rec)
    score, reasons = score_text(text)
    return {"filter_score": score, "filter_reasons": reasons}


def filter_records(
    records: list[dict], threshold: int = 2
) -> tuple[list[dict], list[dict]]:
    kept: list[dict] = []
    rejected: list[dict] = []
    for record in records:
        score_payload = score_record(record)
        record.update(score_payload)
        if score_payload["filter_score"] >= threshold:
            kept.append(record)
        else:
            rejected.append(record)
    return kept, rejected


def run_filter(cfg: ProjectConfig, run_date: date, threshold: int = 2) -> dict:
    run_date_str = run_date.isoformat()
    input_path = (
        cfg.paths.data_dir / "interim" / "merged" / run_date_str / "leads.ndjson"
    )
    if not input_path.exists():
        raise FileNotFoundError(f"Missing merged input: {input_path}")

    records = load_ndjson(input_path)
    kept, rejected = filter_records(records, threshold=threshold)

    candidates_path = (
        cfg.paths.data_dir
        / "processed"
        / "candidates"
        / run_date_str
        / "leads.ndjson"
    )
    rejected_path = (
        cfg.paths.data_dir
        / "processed"
        / "rejected"
        / run_date_str
        / "leads.ndjson"
    )
    write_ndjson(candidates_path, kept)
    write_ndjson(rejected_path, rejected)

    return {
        "input_count": len(records),
        "kept_count": len(kept),
        "rejected_count": len(rejected),
        "candidates_path": str(candidates_path),
        "rejected_path": str(rejected_path),
    }
