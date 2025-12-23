from __future__ import annotations  # no installation needed

import argparse  # no installation needed
import json  # no installation needed
import sys  # no installation needed
from datetime import date, datetime, timezone  # no installation needed
from typing import Any  # no installation needed

from .config import load_config  # no installation needed
from .modules.discovery.filter import load_ndjson, run_filter, score_record  # no installation needed
from .modules.discovery.generic_html import run_generic_html  # no installation needed
from .modules.discovery.merge import merge_sources  # no installation needed
from .modules.discovery.producthunt_html import run_producthunt_html  # no installation needed
from .modules.discovery.schema import Lead  # no installation needed
from .modules.discovery.storage import write_leads  # no installation needed


def _print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config()

    if args.dry:
        payload = {
            "mode": "dry-run",
            "repo_root": str(cfg.paths.repo_root),
            "configs_dir": str(cfg.paths.configs_dir),
            "data_dir": str(cfg.paths.data_dir),
            "outputs_dir": str(cfg.paths.outputs_dir),
            "proof_dir": str(cfg.paths.proof_dir),
            "settings_keys": sorted(list(cfg.settings.keys())),
            "sources_keys": sorted(list(cfg.sources.keys())),
        }
        _print(payload)
        return 0

    # Placeholder for actual pipeline execution.
    print("Run mode not implemented yet. Use --dry for now.")
    return 0


def _demo_leads(source: str, count: int) -> list[Lead]:
    discovered_at = datetime.now(timezone.utc).isoformat()
    leads: list[Lead] = []
    for idx in range(1, count + 1):
        leads.append(
            Lead(
                source=source,
                source_url=f"https://example.com/sources/{source}",
                discovered_at=discovered_at,
                company_name=f"Demo Company {idx}",
                website=f"https://example.com/companies/{idx}",
                description=f"Sample discovery lead {idx} from {source}.",
                signals={"rank": idx, "stage": "demo"},
                raw={"seed_index": idx},
            )
        )
    return leads


def cmd_discovery_scaffold(args: argparse.Namespace) -> int:
    cfg = load_config()
    leads = _demo_leads(args.source, args.n)
    output_path = write_leads(cfg, args.source, leads)
    _print({"output_path": str(output_path), "count": len(leads)})
    return 0


def cmd_discovery_fetch(args: argparse.Namespace) -> int:
    cfg = load_config()

    run_date = None
    if args.run_date:
        try:
            run_date = date.fromisoformat(args.run_date)
        except ValueError as exc:
            raise ValueError("run-date must be in YYYY-MM-DD format.") from exc

    if args.source == "generic_html":
        payload = run_generic_html(
            cfg, limit=args.limit, run_date=run_date, seed_url=args.url
        )
    elif args.source == "producthunt_html":
        payload = run_producthunt_html(
            cfg, limit=args.limit, run_date=run_date, seed_url=args.url
        )
    else:
        raise ValueError(f"Unsupported discovery source: {args.source}")
    _print(payload)
    return 0


def _parse_sources_arg(args: argparse.Namespace) -> list[str]:
    if args.sources:
        return [item.strip() for item in args.sources.split(",") if item.strip()]
    if args.source:
        return [item.strip() for item in args.source if item.strip()]
    return []


def cmd_discovery_merge(args: argparse.Namespace) -> int:
    cfg = load_config()
    try:
        run_date = date.fromisoformat(args.run_date)
    except ValueError as exc:
        raise ValueError("run-date must be in YYYY-MM-DD format.") from exc

    sources = _parse_sources_arg(args)
    if not sources:
        raise ValueError("At least one source must be provided.")

    payload = merge_sources(cfg, sources=sources, run_date=run_date)
    _print(payload)
    return 0


def cmd_discovery_filter(args: argparse.Namespace) -> int:
    cfg = load_config()
    try:
        run_date = date.fromisoformat(args.run_date)
    except ValueError as exc:
        raise ValueError("run-date must be in YYYY-MM-DD format.") from exc

    payload = run_filter(cfg, run_date=run_date, threshold=args.threshold)
    _print(payload)
    return 0


def cmd_discovery_score(args: argparse.Namespace) -> int:
    cfg = load_config()
    try:
        run_date = date.fromisoformat(args.run_date)
    except ValueError as exc:
        raise ValueError("run-date must be in YYYY-MM-DD format.") from exc

    run_date_str = run_date.isoformat()
    input_path = (
        cfg.paths.data_dir / "interim" / "merged" / run_date_str / "leads.ndjson"
    )
    if not input_path.exists():
        raise FileNotFoundError(f"Missing merged input: {input_path}")

    records = load_ndjson(input_path)
    payload = []
    for record in records:
        score_payload = score_record(record)
        payload.append(
            {
                "company_name": record.get("company_name"),
                "source": record.get("source"),
                "filter_score": score_payload["filter_score"],
                "filter_reasons": score_payload["filter_reasons"],
            }
        )

    _print(payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="acq_pipeline",
        description="B2B SaaS acquisition sourcing pipeline (phase-0 bootstrap).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the pipeline (use --dry for smoke test).")
    run.add_argument("--dry", action="store_true", help="Print loaded config and exit.")
    run.set_defaults(func=cmd_run)

    discovery = sub.add_parser("discovery", help="Discovery module commands.")
    discovery_sub = discovery.add_subparsers(dest="discovery_command", required=True)

    scaffold = discovery_sub.add_parser("scaffold", help="Write sample leads to NDJSON.")
    scaffold.add_argument("--source", required=True, help="Source identifier.")
    scaffold.add_argument("--n", type=int, default=1, help="Number of sample leads.")
    scaffold.set_defaults(func=cmd_discovery_scaffold)

    fetch = discovery_sub.add_parser(
        "fetch", help="Fetch leads from a generic HTML directory."
    )
    fetch.add_argument("--source", default="generic_html", help="Source identifier.")
    fetch.add_argument("--limit", type=int, default=25, help="Max leads to write.")
    fetch.add_argument("--run-date", help="Override run date (YYYY-MM-DD).")
    fetch.add_argument("--url", help="Override configured seed URL for this run.")
    fetch.set_defaults(func=cmd_discovery_fetch)

    merge = discovery_sub.add_parser("merge", help="Merge discovery leads by date.")
    merge.add_argument(
        "--sources",
        help="Comma-separated sources (e.g. generic_html,producthunt_html).",
    )
    merge.add_argument(
        "--source",
        action="append",
        help="Repeatable source option (alternative to --sources).",
    )
    merge.add_argument("--run-date", required=True, help="Run date (YYYY-MM-DD).")
    merge.set_defaults(func=cmd_discovery_merge)

    filter_cmd = discovery_sub.add_parser(
        "filter", help="Filter merged leads with keyword scoring."
    )
    filter_cmd.add_argument("--run-date", required=True, help="Run date (YYYY-MM-DD).")
    filter_cmd.add_argument(
        "--threshold", type=int, default=2, help="Minimum score to keep."
    )
    filter_cmd.set_defaults(func=cmd_discovery_filter)

    score_cmd = discovery_sub.add_parser(
        "score", help="Score merged leads without writing files."
    )
    score_cmd.add_argument("--run-date", required=True, help="Run date (YYYY-MM-DD).")
    score_cmd.set_defaults(func=cmd_discovery_score)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
