from acq_pipeline.modules.dossier.render import render_dossier_md, slugify


def test_slugify() -> None:
    slug = slugify("Acme Dashboards_Pro")
    assert slug == "acme-dashboards-pro"
    assert " " not in slug


def test_render_dossier_md_headers() -> None:
    record = {
        "company_name": "Acme",
        "description": "B2B SaaS analytics dashboard.",
        "source": "generic_html",
        "source_url": "https://example.com/acme",
        "discovered_at": "2025-12-23T00:00:00Z",
        "filter_score": 4,
        "filter_reasons": ["+saas", "+dashboard"],
        "signals": {"rank": 1},
    }

    md = render_dossier_md(record)

    assert "## Snapshot" in md
    assert "## Next diligence questions" in md
