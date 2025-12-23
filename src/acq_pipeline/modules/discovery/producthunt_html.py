from __future__ import annotations  # no installation needed

from datetime import date, datetime, timezone  # no installation needed
from urllib.parse import urljoin, urlparse  # no installation needed

from bs4 import BeautifulSoup  # already in env; no new install

from ...config import ProjectConfig  # no installation needed
from .generic_html import fetch_html  # no installation needed
from .schema import Lead  # no installation needed
from .storage import write_leads  # no installation needed


def _utc_now_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


def _parse_int(text: str) -> int | None:
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None


def parse_producthunt_listing_html(
    html: str, base_url: str | None = None
) -> list[Lead]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.ph-card")
    discovered_at = _utc_now_z()
    leads: list[Lead] = []

    for idx, card in enumerate(cards, start=1):
        name_el = card.select_one(".ph-name")
        name = name_el.get_text(strip=True) if name_el else ""

        link_el = card.select_one("a.ph-link")
        href = ""
        if link_el:
            value = link_el.get("href")
            href = value.strip() if isinstance(value, str) else ""

        resolved_url = href
        if href and base_url:
            resolved_url = urljoin(base_url, href)

        tagline_el = card.select_one(".ph-tagline")
        tagline = tagline_el.get_text(strip=True) if tagline_el else ""

        upvotes_el = card.select_one(".ph-upvotes")
        upvotes = _parse_int(upvotes_el.get_text(strip=True)) if upvotes_el else None

        topics = [
            topic.get_text(strip=True)
            for topic in card.select(".ph-topics li")
            if topic.get_text(strip=True)
        ]

        website_el = card.select_one("a.ph-website")
        website = None
        if website_el:
            website_href = website_el.get("href")
            if isinstance(website_href, str) and website_href.strip():
                website = website_href.strip()

        if not (name or resolved_url or tagline):
            continue

        signals: dict[str, object] = {"rank": idx}
        if upvotes is not None:
            signals["upvotes"] = upvotes
        if topics:
            signals["topics"] = topics

        leads.append(
            Lead(
                source="producthunt_html",
                source_url=resolved_url or "",
                discovered_at=discovered_at,
                company_name=name or None,
                website=website,
                description=tagline or None,
                signals=signals,
                raw={
                    "name": name,
                    "url": href,
                    "resolved_url": resolved_url,
                    "tagline": tagline,
                    "upvotes": upvotes,
                    "topics": topics,
                    "website": website,
                },
            )
        )

    return leads


def run_producthunt_html(
    cfg: ProjectConfig,
    limit: int,
    run_date: date | None = None,
    seed_url: str | None = None,
) -> dict[str, object]:
    sources_cfg = cfg.sources.get("sources", cfg.sources)
    source_cfg = sources_cfg.get("producthunt_html")
    if not isinstance(source_cfg, dict):
        raise ValueError("Missing producthunt_html config.")

    seed_urls = source_cfg.get("seed_urls") or []
    if seed_url is None:
        if not seed_urls:
            raise ValueError("producthunt_html.seed_urls must include at least one URL.")
        seed_url = seed_urls[0]

    base_url = source_cfg.get("base_url")
    if base_url is None:
        base_url = seed_url if _is_http_url(seed_url) else None

    html = fetch_html(seed_url)
    leads = parse_producthunt_listing_html(html, base_url=base_url)
    if limit is not None and limit >= 0:
        leads = leads[:limit]

    output_path = write_leads(cfg, "producthunt_html", leads, run_date=run_date)
    return {
        "source": "producthunt_html",
        "url": seed_url,
        "count": len(leads),
        "output_path": str(output_path),
    }
