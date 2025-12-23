from __future__ import annotations  # no installation needed


POSITIVE_KEYWORDS: dict[str, int] = {
    "saas": 3,
    "b2b": 3,
    "api": 2,
    "automation": 2,
    "workflow": 2,
    "dashboard": 1,
    "integrations": 2,
    "crm": 2,
    "billing": 2,
    "invoicing": 2,
    "analytics": 2,
    "compliance": 2,
    "infrastructure": 1,
    "devops": 2,
    "platform": 1,
    "enterprise": 2,
    "teams": 1,
    "operations": 1,
    "ops": 1,
    "back office": 1,
    "backoffice": 1,
}

NEGATIVE_KEYWORDS: dict[str, int] = {
    "dating": -3,
    "game": -3,
    "games": -3,
    "fitness": -2,
    "social": -2,
    "consumer": -2,
    "shopping": -2,
    "fashion": -2,
    "travel": -2,
    "food": -2,
}


def score_text(text: str) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    for keyword, points in POSITIVE_KEYWORDS.items():
        if keyword in text:
            score += points
            reasons.append(f"+{keyword}")
    for keyword, points in NEGATIVE_KEYWORDS.items():
        if keyword in text:
            score += points
            reasons.append(f"-{keyword}")
    return score, reasons
