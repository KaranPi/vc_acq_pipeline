from pathlib import Path

from acq_pipeline.modules.discovery.producthunt_html import (
    parse_producthunt_listing_html,
)


def test_parse_producthunt_listing_html_fixture() -> None:
    html = Path("tests/fixtures/producthunt_html/sample_listing.html").read_text(
        encoding="utf-8"
    )
    base_url = "https://www.producthunt.com/"
    leads = parse_producthunt_listing_html(html, base_url=base_url)

    assert len(leads) == 5
    for lead in leads:
        assert lead.company_name
        assert lead.description
        assert lead.source_url.startswith(base_url)
        assert isinstance(lead.signals.get("upvotes"), int)

    assert leads[0].signals.get("topics") == ["DevTools", "AI"]
