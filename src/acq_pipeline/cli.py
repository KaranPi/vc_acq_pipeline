from __future__ import annotations  # no installation needed

import argparse  # no installation needed
import json  # no installation needed
import sys  # no installation needed
from datetime import date, datetime, timezone  # no installation needed
from typing import Any  # no installation needed

from .config import load_config  # no installation needed
from .modules.discovery.generic_html import run_generic_html  # no installation needed
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
    if args.source != "generic_html":
        raise ValueError("Only the generic_html source is supported right now.")

    run_date = None
    if args.run_date:
        try:
            run_date = date.fromisoformat(args.run_date)
        except ValueError as exc:
            raise ValueError("run-date must be in YYYY-MM-DD format.") from exc

    payload = run_generic_html(
        cfg, limit=args.limit, run_date=run_date, seed_url=args.url
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

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
