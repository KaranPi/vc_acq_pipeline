import json
from pathlib import Path

from acq_pipeline.modules.discovery.producthunt_api import parse_producthunt_response


def test_parse_producthunt_response_fixture() -> None:
    data = json.loads(
        Path("tests/fixtures/producthunt_api/sample_response.json").read_text(
            encoding="utf-8"
        )
    )

    leads = parse_producthunt_response(data)

    assert len(leads) == 5
    for lead in leads:
        assert lead.company_name
        assert lead.description
        assert lead.source_url.startswith("https://www.producthunt.com/posts/")

    assert leads[0].signals.get("upvotes") == 120
    assert leads[0].source_url == "https://www.producthunt.com/posts/alpha"
    assert leads[0].signals.get("topics") == ["DevTools", "AI"]
