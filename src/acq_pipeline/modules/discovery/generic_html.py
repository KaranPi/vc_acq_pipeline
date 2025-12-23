from __future__ import annotations  # no installation needed

from datetime import date, datetime, timezone  # no installation needed
from pathlib import Path  # no installation needed
from urllib.parse import unquote, urljoin, urlparse  # no installation needed

import requests  # already in env; no new install
from bs4 import BeautifulSoup  # already in env; no new install

from ...config import ProjectConfig  # no installation needed
from .schema import Lead  # no installation needed
from .storage import write_leads  # no installation needed


def _read_local_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _file_url_to_path(url: str) -> Path:
    parsed = urlparse(url)
    path = unquote(parsed.path or "")
    if parsed.netloc and parsed.netloc.lower() != "localhost":
        return Path(f"//{parsed.netloc}{path}")
    if path.startswith("/") and len(path) >= 3 and path[2] == ":":
        return Path(path.lstrip("/"))
    return Path(path)


def _is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


def fetch_html(url: str, timeout: int = 30) -> str:
    if url.startswith("file://"):
        path = _file_url_to_path(url)
        if path.exists():
            return _read_local_file(path)
        raise FileNotFoundError(f"Local file not found: {path}")

    if "://" not in url:
        path = Path(url)
        if path.exists():
            return _read_local_file(path)

    headers = {"User-Agent": "acq-pipeline/0.1 (+https://example.com)"}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def _utc_now_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _split_selector(selector: str) -> tuple[str, str | None]:
    marker = "::attr("
    if marker in selector and selector.endswith(")"):
        css, attr_part = selector.split(marker, 1)
        attr = attr_part[:-1]
        return css, attr
    return selector, None


def _extract_value(card: object, selector: str) -> str:
    css_selector, attr = _split_selector(selector)
    element = card.select_one(css_selector) if css_selector else None
    if element is None:
        return ""
    if attr:
        value = element.get(attr)
        return value.strip() if isinstance(value, str) else ""
    return element.get_text(strip=True)


def parse_directory_html(
    html: str,
    source: str,
    base_url: str | None,
    selectors: dict,
) -> list[Lead]:
    if not isinstance(selectors, dict):
        raise ValueError("selectors must be a dict.")

    required_keys = ("card", "name", "url", "description")
    for key in required_keys:
        if key not in selectors:
            raise ValueError(f"Missing selector: {key}")

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(str(selectors["card"]))
    discovered_at = _utc_now_z()
    leads: list[Lead] = []

    for card in cards:
        name = _extract_value(card, str(selectors["name"]))
        url = _extract_value(card, str(selectors["url"]))
        desc = _extract_value(card, str(selectors["description"]))

        resolved_url = url
        if url and base_url:
            resolved_url = urljoin(base_url, url)

        if not (name or resolved_url or desc):
            continue

        leads.append(
            Lead(
                source=source,
                source_url=resolved_url or "",
                discovered_at=discovered_at,
                company_name=name or None,
                website=resolved_url or None,
                description=desc or None,
                signals={},
                raw={
                    "name": name,
                    "url": url,
                    "description": desc,
                    "resolved_url": resolved_url,
                },
            )
        )

    return leads


def run_generic_html(
    cfg: ProjectConfig,
    limit: int,
    run_date: date | None = None,
    seed_url: str | None = None,
) -> dict[str, object]:
    sources_cfg = cfg.sources.get("sources", cfg.sources)
    source_cfg = sources_cfg.get("generic_html")
    if not isinstance(source_cfg, dict):
        raise ValueError("Missing generic_html config.")

    seed_urls = source_cfg.get("seed_urls") or []
    if seed_url is None:
        if not seed_urls:
            raise ValueError("generic_html.seed_urls must include at least one URL.")
        seed_url = seed_urls[0]

    selectors = source_cfg.get("selectors") or {}
    base_url = source_cfg.get("base_url")
    if base_url is None:
        base_url = seed_url if _is_http_url(seed_url) else None

    html = fetch_html(seed_url)
    leads = parse_directory_html(
        html, source="generic_html", base_url=base_url, selectors=selectors
    )
    if limit is not None and limit >= 0:
        leads = leads[:limit]

    output_path = write_leads(cfg, "generic_html", leads, run_date=run_date)
    return {
        "source": "generic_html",
        "url": seed_url,
        "count": len(leads),
        "output_path": str(output_path),
    }
