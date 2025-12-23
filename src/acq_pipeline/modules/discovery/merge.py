from __future__ import annotations  # no installation needed

import json  # no installation needed
from datetime import date  # no installation needed
from pathlib import Path  # no installation needed
from urllib.parse import parse_qsl, urlencode, urlparse  # no installation needed

from ...config import ProjectConfig  # no installation needed


def read_ndjson(path: Path) -> list[dict]:
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


def normalize_url(s: str) -> str:
    value = s.strip().lower()
    if not value:
        return ""

    parsed = urlparse(value)
    if not parsed.scheme:
        parsed = urlparse(f"http://{value}")

    query_pairs = [
        (key, val)
        for key, val in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.startswith("utm_")
    ]
    query = urlencode(query_pairs)
    path = parsed.path.rstrip("/")
    base = f"{parsed.netloc}{path}"
    return f"{base}?{query}" if query else base


def dedup_key(rec: dict) -> str:
    website = rec.get("website")
    if isinstance(website, str) and website.strip():
        return normalize_url(website)

    source_url = rec.get("source_url")
    if isinstance(source_url, str) and source_url.strip():
        return normalize_url(source_url)

    company_name = rec.get("company_name")
    if isinstance(company_name, str) and company_name.strip():
        return company_name.strip().lower()

    return ""


def _write_ndjson(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=True))
            f.write("\n")


def merge_sources(cfg: ProjectConfig, sources: list[str], run_date: date) -> dict:
    run_date_str = run_date.isoformat()
    input_counts: dict[str, int] = {}
    deduped: dict[str, dict] = {}

    for source in sources:
        input_path = (
            cfg.paths.data_dir / "raw" / source / run_date_str / "leads.ndjson"
        )
        if not input_path.exists():
            raise FileNotFoundError(f"Missing input for source '{source}': {input_path}")

        records = read_ndjson(input_path)
        input_counts[source] = len(records)
        for record in records:
            key = dedup_key(record)
            if key in deduped:
                continue
            deduped[key] = record

    output_path = (
        cfg.paths.data_dir
        / "interim"
        / "merged"
        / run_date_str
        / "leads.ndjson"
    )
    output_records = list(deduped.values())
    _write_ndjson(output_path, output_records)

    total_in = sum(input_counts.values())
    output_count = len(output_records)
    return {
        "sources": sources,
        "input_counts": input_counts,
        "output_count": output_count,
        "deduped_count": max(total_in - output_count, 0),
        "output_path": str(output_path),
    }
