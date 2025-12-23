from __future__ import annotations  # no installation needed

import json  # no installation needed
from datetime import date, datetime  # no installation needed
from pathlib import Path  # no installation needed

from ...config import ProjectConfig  # no installation needed
from .schema import Lead  # no installation needed


def _run_date_str(run_date: date | str) -> str:
    if isinstance(run_date, datetime):
        return run_date.date().isoformat()
    if isinstance(run_date, date):
        return run_date.isoformat()
    if isinstance(run_date, str):
        return run_date
    raise ValueError("run_date must be a date or ISO string.")


def get_run_dir(
    cfg: ProjectConfig, source: str, run_date: date | str, mode: str | None = None
) -> Path:
    run_date_str = _run_date_str(run_date)
    base = cfg.paths.data_dir / "raw" / source / run_date_str
    if mode:
        return base / mode
    return base


def append_ndjson(path: Path, record_dict: dict[str, object]) -> None:
    if not isinstance(record_dict, dict):
        raise ValueError("record_dict must be a dict.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record_dict, ensure_ascii=True))
        f.write("\n")


def write_leads(
    cfg: ProjectConfig,
    source: str,
    leads: list[Lead],
    run_date: date | str | None = None,
    mode: str | None = None,
    overwrite: bool = False,
) -> Path:
    if run_date is None:
        run_date = date.today()
    run_dir = get_run_dir(cfg, source, run_date, mode=mode)
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "leads.ndjson"

    if overwrite and path.exists():
        path.unlink()

    if not leads:
        path.touch(exist_ok=True)
        return path

    for lead in leads:
        append_ndjson(path, lead.to_dict())

    return path
