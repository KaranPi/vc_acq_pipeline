import json
from datetime import date
from pathlib import Path

from acq_pipeline.config import ProjectConfig, ProjectPaths
from acq_pipeline.modules.discovery.schema import Lead
from acq_pipeline.modules.discovery.storage import write_leads


def _read_ndjson(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_write_leads_modes_and_overwrite(tmp_path: Path) -> None:
    cfg = ProjectConfig(
        paths=ProjectPaths(
            repo_root=tmp_path,
            configs_dir=tmp_path / "configs",
            data_dir=tmp_path / "data",
            outputs_dir=tmp_path / "outputs",
            proof_dir=tmp_path / "proof",
        ),
        settings={},
        sources={},
    )

    run_date = date(2025, 12, 23)
    leads_fixture = [
        Lead(
            source="producthunt_api",
            source_url="https://example.com/one",
            discovered_at="2025-12-23T00:00:00Z",
        )
    ]
    leads_live = [
        Lead(
            source="producthunt_api",
            source_url="https://example.com/two",
            discovered_at="2025-12-23T00:00:00Z",
        )
    ]

    fixture_path = write_leads(
        cfg,
        "producthunt_api",
        leads_fixture,
        run_date=run_date,
        mode="fixture",
        overwrite=True,
    )
    live_path = write_leads(
        cfg,
        "producthunt_api",
        leads_live,
        run_date=run_date,
        mode="live",
        overwrite=True,
    )

    assert fixture_path != live_path
    assert fixture_path.parts[-2] == "fixture"
    assert live_path.parts[-2] == "live"

    fixture_records = _read_ndjson(fixture_path)
    live_records = _read_ndjson(live_path)
    assert fixture_records[0]["source_url"] == "https://example.com/one"
    assert live_records[0]["source_url"] == "https://example.com/two"

    overwrite_path = write_leads(
        cfg,
        "producthunt_api",
        leads_live,
        run_date=run_date,
        mode="fixture",
        overwrite=True,
    )
    overwritten_records = _read_ndjson(overwrite_path)
    assert len(overwritten_records) == 1
    assert overwritten_records[0]["source_url"] == "https://example.com/two"
