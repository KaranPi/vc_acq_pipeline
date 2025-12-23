import pytest

from acq_pipeline.modules.discovery.schema import Lead


def test_lead_roundtrip() -> None:
    lead = Lead(
        source="demo",
        source_url="https://example.com/source/demo",
        discovered_at="2024-01-01T00:00:00Z",
        company_name="DemoCo",
        website="https://democo.example.com",
        description="Test description.",
        signals={"signal": 1},
        raw={"raw_key": "raw_value"},
    )

    rebuilt = Lead.from_dict(lead.to_dict())

    assert rebuilt == lead


def test_lead_missing_required_fields() -> None:
    with pytest.raises(ValueError):
        Lead.from_dict({"source": "demo", "source_url": "https://example.com"})
