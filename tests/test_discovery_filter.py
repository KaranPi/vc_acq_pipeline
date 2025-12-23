from acq_pipeline.modules.discovery.filter import filter_records, score_record


def test_filter_records_scoring() -> None:
    records = [
        {
            "company_name": "Acme SaaS",
            "description": "B2B automation platform with API access.",
            "raw": {"notes": "enterprise workflow"},
        },
        {
            "company_name": "LoveMatch",
            "description": "A social dating app for consumers.",
            "raw": {"category": "dating"},
        },
    ]

    kept, rejected = filter_records(records, threshold=2)

    assert len(kept) == 1
    assert len(rejected) == 1

    kept_record = kept[0]
    rejected_record = rejected[0]

    assert kept_record["filter_score"] >= 2
    assert kept_record["filter_reasons"]

    assert rejected_record["filter_score"] < 2
    assert rejected_record["filter_reasons"]


def test_score_record_keywords() -> None:
    record = {
        "company_name": "Acme",
        "description": "saas api automation dashboard",
        "raw": {},
    }

    scored = score_record(record)

    assert scored["filter_score"] >= 2
    assert scored["filter_reasons"]
