import json
from datetime import date
from pathlib import Path

from acq_pipeline.config import ProjectConfig, ProjectPaths
from acq_pipeline.modules.discovery.merge import merge_sources, read_ndjson


def _write_ndjson(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=True))
            f.write("\n")


def test_merge_sources_dedup(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    cfg = ProjectConfig(
        paths=ProjectPaths(
            repo_root=tmp_path,
            configs_dir=tmp_path / "configs",
            data_dir=data_dir,
            outputs_dir=tmp_path / "outputs",
            proof_dir=tmp_path / "proof",
        ),
        settings={},
        sources={},
    )

    run_date = date(2025, 12, 23)
    run_date_str = run_date.isoformat()

    source_a = data_dir / "raw" / "generic_html" / run_date_str / "leads.ndjson"
    source_b = data_dir / "raw" / "producthunt_html" / run_date_str / "leads.ndjson"

    _write_ndjson(
        source_a,
        [
            {
                "website": "https://Example.com/Path/?utm_source=newsletter",
                "company_name": "Alpha",
            },
            {"source_url": "https://other.com/foo", "company_name": "Beta"},
        ],
    )
    _write_ndjson(
        source_b,
        [
            {"source_url": "http://example.com/path", "company_name": "Alpha Duplicate"},
            {"company_name": "Gamma"},
        ],
    )

    summary = merge_sources(
        cfg, sources=["generic_html", "producthunt_html"], run_date=run_date
    )

    assert summary["input_counts"] == {"generic_html": 2, "producthunt_html": 2}
    assert summary["output_count"] == 3
    assert summary["deduped_count"] == 1

    expected_output = (
        data_dir
        / "interim"
        / "merged"
        / run_date_str
        / "leads.ndjson"
    )
    assert summary["output_path"] == str(expected_output)

    output_records = read_ndjson(expected_output)
    assert len(output_records) == 3
