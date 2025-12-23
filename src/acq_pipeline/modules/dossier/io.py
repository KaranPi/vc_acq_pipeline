from __future__ import annotations  # no installation needed

import json  # no installation needed
from datetime import date  # no installation needed
from pathlib import Path  # no installation needed

from ...config import ProjectConfig  # no installation needed
from .render import render_dossier_md, slugify  # no installation needed


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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_dossiers(cfg: ProjectConfig, run_date: date, limit: int = 10) -> dict:
    run_date_str = run_date.isoformat()
    input_path = (
        cfg.paths.data_dir
        / "processed"
        / "candidates"
        / run_date_str
        / "leads.ndjson"
    )
    if not input_path.exists():
        raise FileNotFoundError(f"Missing candidates input: {input_path}")

    records = load_ndjson(input_path)
    output_dir = cfg.paths.outputs_dir / "dossiers" / run_date_str
    output_dir.mkdir(parents=True, exist_ok=True)

    if limit is None or limit < 0:
        limit_count = len(records)
    else:
        limit_count = min(limit, len(records))
    written = 0
    index: list[dict[str, object]] = []

    for record in records[:limit_count]:
        company_name = record.get("company_name") or "unknown"
        source = record.get("source") or "unknown"
        slug = f"{slugify(str(company_name))}-{source}"
        output_path = output_dir / f"{slug}.md"
        content = render_dossier_md(record)
        write_text(output_path, content)
        written += 1
        index.append(
            {
                "slug": slug,
                "company_name": company_name,
                "source": source,
                "path": str(output_path),
                "filter_score": record.get("filter_score"),
            }
        )

    index_path = output_dir / "_index.json"
    index_payload = json.dumps(index, indent=2, sort_keys=True, ensure_ascii=True)
    write_text(index_path, index_payload)

    return {
        "run_date": run_date_str,
        "input_count": len(records),
        "written_count": written,
        "output_dir": str(output_dir),
        "index_path": str(index_path),
    }
