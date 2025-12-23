from __future__ import annotations  # no installation needed

import json  # no installation needed
import os  # no installation needed
import time  # no installation needed
from datetime import date, datetime, timezone  # no installation needed
from typing import Any  # no installation needed

import requests  # already in env; no new install
from tenacity import retry, stop_after_attempt, wait_fixed  # already in env

from ...config import ProjectConfig  # no installation needed
from .schema import Lead  # no installation needed
from .storage import write_leads  # no installation needed


def build_query(first: int) -> str:
    return (
        "query Posts("
        "$first: Int!, "
        "$after: String, "
        "$order: PostsOrder, "
        "$topic: String, "
        "$featured: Boolean, "
        "$postedBefore: DateTime, "
        "$postedAfter: DateTime"
        ") {"
        " posts("
        "first: $first, "
        "after: $after, "
        "order: $order, "
        "topic: $topic, "
        "featured: $featured, "
        "postedBefore: $postedBefore, "
        "postedAfter: $postedAfter"
        ") {"
        " edges {"
        " node {"
        " id"
        " slug"
        " name"
        " tagline"
        " description"
        " url"
        " votesCount"
        " commentsCount"
        " createdAt"
        " featuredAt"
        " website"
        " topics { edges { node { name slug } } }"
        " }"
        " }"
        " pageInfo { endCursor hasNextPage }"
        " }"
        "}"
    )


def _utc_now_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _extract_topics(node: dict[str, Any]) -> list[str]:
    topics = node.get("topics")
    if not isinstance(topics, dict):
        return []
    edges = topics.get("edges")
    if not isinstance(edges, list):
        return []
    names: list[str] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        topic_node = edge.get("node")
        if not isinstance(topic_node, dict):
            continue
        name = topic_node.get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return names


def _raise_for_graphql_errors(data: dict[str, Any]) -> None:
    errors = data.get("errors")
    if not errors:
        return
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            message = first.get("message") or "GraphQL error"
            path = first.get("path")
            if path:
                raise RuntimeError(f"{message} (path: {path})")
            raise RuntimeError(str(message))
    raise RuntimeError("GraphQL error")


def _extract_posts_edges(data: dict[str, Any]) -> list[dict[str, Any]]:
    posts = data.get("data", {}).get("posts", {})
    edges = posts.get("edges", [])
    if not isinstance(edges, list):
        return []
    return [edge for edge in edges if isinstance(edge, dict)]


def parse_producthunt_response(
    data: dict[str, Any], source: str = "producthunt_api"
) -> list[Lead]:
    if not isinstance(data, dict):
        raise ValueError("Response data must be a dict.")

    _raise_for_graphql_errors(data)
    edges = _extract_posts_edges(data)

    discovered_at = _utc_now_z()
    leads: list[Lead] = []

    for edge in edges:
        node = edge.get("node", {})
        if not isinstance(node, dict):
            continue

        name = node.get("name") or ""
        tagline = node.get("tagline") or node.get("description") or ""
        source_url = node.get("url") or ""
        website = node.get("website") or None

        signals: dict[str, object] = {}
        upvotes = node.get("votesCount")
        if upvotes is None:
            upvotes = node.get("upvotesCount")
        if isinstance(upvotes, int):
            signals["upvotes"] = upvotes
        comments = node.get("commentsCount")
        if isinstance(comments, int):
            signals["comments"] = comments

        topics = _extract_topics(node)
        if topics:
            signals["topics"] = topics

        leads.append(
            Lead(
                source=source,
                source_url=str(source_url) if source_url else "",
                discovered_at=discovered_at,
                company_name=str(name) if name else None,
                website=str(website) if website else None,
                description=str(tagline) if tagline else None,
                signals=signals,
                raw=node,
            )
        )

    return leads


def _live_scrape_settings(cfg: ProjectConfig) -> tuple[int, int, int]:
    if isinstance(cfg.settings, dict):
        settings = cfg.settings.get("live_scrape", {})
    else:
        settings = {}
    if not isinstance(settings, dict):
        settings = {}

    def _get_int(key: str, default: int) -> int:
        value = settings.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    timeout = _get_int("timeout_seconds", 30)
    sleep_seconds = _get_int("sleep_seconds", 2)
    max_retries = _get_int("max_retries", 3)
    if max_retries < 1:
        max_retries = 1
    return timeout, sleep_seconds, max_retries


def run_producthunt_fixture(
    cfg: ProjectConfig, limit: int, run_date: date
) -> dict[str, object]:
    sources_cfg = cfg.sources.get("sources", cfg.sources)
    source_cfg = sources_cfg.get("producthunt_api")
    if not isinstance(source_cfg, dict):
        raise ValueError("Missing producthunt_api config.")

    fixture_path = source_cfg.get("fixture_path")
    if not isinstance(fixture_path, str) or not fixture_path:
        raise ValueError("producthunt_api.fixture_path is required.")

    path = cfg.paths.repo_root / fixture_path
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    leads = parse_producthunt_response(data, source="producthunt_api")
    if limit is not None and limit >= 0:
        leads = leads[:limit]

    output_path = write_leads(cfg, "producthunt_api", leads, run_date=run_date)
    return {
        "source": "producthunt_api",
        "url_or_fixture": fixture_path,
        "count": len(leads),
        "output_path": str(output_path),
    }


def run_producthunt_live(
    cfg: ProjectConfig,
    limit: int,
    run_date: date,
    order: str = "RANKING",
    featured: bool = False,
    posted_after: str | None = None,
    posted_before: str | None = None,
) -> dict[str, object]:
    token = os.getenv("PRODUCTHUNT_DEV_TOKEN")
    if not token:
        raise ValueError("Set PRODUCTHUNT_DEV_TOKEN to use live Product Hunt API.")

    timeout, sleep_seconds, max_retries = _live_scrape_settings(cfg)
    headers = {"Authorization": f"Bearer {token}"}
    query = build_query(limit if limit > 0 else 20)

    @retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_fixed(sleep_seconds),
        reraise=True,
    )
    def _fetch(variables: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
        response = requests.post(
            "https://api.producthunt.com/v2/api/graphql",
            headers=headers,
            json={"query": query, "variables": variables},
            timeout=timeout,
        )
        if response.status_code == 429:
            reset = response.headers.get("X-Rate-Limit-Reset")
            try:
                sleep_for = int(reset) if reset is not None else sleep_seconds
            except ValueError:
                sleep_for = sleep_seconds
            sleep_for = max(1, min(sleep_for, 60))
            time.sleep(sleep_for)
            response.raise_for_status()
        response.raise_for_status()
        return response.json(), dict(response.headers)

    if limit <= 0:
        output_path = write_leads(cfg, "producthunt_api", [], run_date=run_date)
        return {
            "source": "producthunt_api",
            "url_or_fixture": "https://api.producthunt.com/v2/api/graphql",
            "count": 0,
            "output_path": str(output_path),
        }

    leads: list[Lead] = []
    remaining = limit
    after: str | None = None
    rate_limit: dict[str, str] = {}

    while remaining > 0:
        page_size = min(20, remaining)
        variables = {
            "first": page_size,
            "after": after,
            "order": order,
            "topic": None,
            "featured": featured,
            "postedBefore": posted_before,
            "postedAfter": posted_after,
        }
        data, response_headers = _fetch(variables)
        _raise_for_graphql_errors(data)

        for header in (
            "X-Rate-Limit-Limit",
            "X-Rate-Limit-Remaining",
            "X-Rate-Limit-Reset",
        ):
            value = response_headers.get(header)
            if value is not None:
                rate_limit[header] = value

        batch = parse_producthunt_response(data, source="producthunt_api")
        if not batch:
            break
        leads.extend(batch)
        remaining = limit - len(leads)

        posts = data.get("data", {}).get("posts", {})
        page_info = posts.get("pageInfo", {}) if isinstance(posts, dict) else {}
        has_next = bool(page_info.get("hasNextPage"))
        end_cursor = page_info.get("endCursor")
        if not has_next or not end_cursor:
            break
        after = str(end_cursor)

    output_path = write_leads(cfg, "producthunt_api", leads, run_date=run_date)
    payload: dict[str, object] = {
        "source": "producthunt_api",
        "url_or_fixture": "https://api.producthunt.com/v2/api/graphql",
        "count": len(leads),
        "output_path": str(output_path),
    }
    if rate_limit:
        payload["rate_limit"] = rate_limit
    return payload
