from __future__ import annotations  # no installation needed

import argparse  # no installation needed
import json  # no installation needed
import sys  # no installation needed
from typing import Any  # no installation needed

from .config import load_config  # no installation needed


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


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="acq_pipeline",
        description="B2B SaaS acquisition sourcing pipeline (phase-0 bootstrap).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the pipeline (use --dry for smoke test).")
    run.add_argument("--dry", action="store_true", help="Print loaded config and exit.")
    run.set_defaults(func=cmd_run)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
