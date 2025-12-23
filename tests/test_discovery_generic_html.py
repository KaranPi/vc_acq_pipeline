from pathlib import Path

from acq_pipeline.modules.discovery.generic_html import fetch_html, parse_directory_html


def test_parse_directory_html_fixture() -> None:
    html = Path("tests/fixtures/generic_html/sample_directory.html").read_text(
        encoding="utf-8"
    )
    selectors = {
        "card": "div.card",
        "name": ".name",
        "url": "a::attr(href)",
        "description": ".desc",
    }

    leads = parse_directory_html(
        html,
        source="generic_html",
        base_url="https://example.com/directory/",
        selectors=selectors,
    )

    assert len(leads) == 5
    for lead in leads:
        assert lead.company_name
        assert lead.source == "generic_html"
        assert lead.website
        assert lead.source_url

    assert leads[0].website == "https://example.com/company-1"


def test_fetch_html_local_file() -> None:
    html = fetch_html("tests/fixtures/generic_html/sample_directory.html")
    assert "Alpha Corp" in html
