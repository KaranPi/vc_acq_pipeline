from __future__ import annotations  # no installation needed

from dataclasses import dataclass  # no installation needed
from pathlib import Path  # no installation needed
from typing import Any  # no installation needed

from dotenv import load_dotenv  # already in env — no new install
import yaml  # already in env — no new install


@dataclass(frozen=True)
class ProjectPaths:
    """Centralized project paths (repo-root-relative)."""

    repo_root: Path
    configs_dir: Path
    data_dir: Path
    outputs_dir: Path
    proof_dir: Path


@dataclass(frozen=True)
class ProjectConfig:
    """Loaded config bundle used by the CLI and modules."""

    paths: ProjectPaths
    settings: dict[str, Any]
    sources: dict[str, Any]


def _repo_root() -> Path:
    # src/acq_pipeline/config.py -> src/acq_pipeline -> src -> repo root
    return Path(__file__).resolve().parents[2]


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML must be a mapping at: {path}")
    return data


def load_config(
    settings_path: str | Path = "configs/settings.yaml",
    sources_path: str | Path = "configs/sources.yaml",
    env_path: str | Path = ".env",
) -> ProjectConfig:
    """
    Loads:
      - .env (optional): for secrets / cookies / proxy settings
      - configs/settings.yaml (optional): runtime switches + rate limits
      - configs/sources.yaml (optional): source definitions + toggles
    """
    root = _repo_root()

    # Load environment variables if present (never commit .env)
    env_file = root / env_path
    if env_file.exists():
        load_dotenv(dotenv_path=env_file)

    settings = _read_yaml(root / settings_path)
    sources = _read_yaml(root / sources_path)

    paths = ProjectPaths(
        repo_root=root,
        configs_dir=root / "configs",
        data_dir=root / "data",
        outputs_dir=root / "outputs",
        proof_dir=root / "proof_of_work",
    )

    return ProjectConfig(paths=paths, settings=settings, sources=sources)
