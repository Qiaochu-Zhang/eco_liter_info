from __future__ import annotations

from dataclasses import dataclass

from economics_tracker.config import (
    DOWNWEIGHT_JEL_PREFIXES,
    HIGH_VALUE_KEYWORDS,
    PRIORITY_JEL_PREFIXES,
    REJECT_JEL_PREFIXES,
    WEAK_SIGNAL_KEYWORDS,
)
from economics_tracker.models import Article


@dataclass(frozen=True)
class ClassificationResult:
    decision: str
    reason: str
    matched_keywords: list[str]


def _collect_matches(text: str, keywords: tuple[str, ...]) -> list[str]:
    haystack = text.lower()
    return [keyword for keyword in keywords if keyword in haystack]


def classify_article(article: Article) -> ClassificationResult:
    combined_text = " ".join(part for part in (article.title, article.abstract) if part).lower()
    high_value_matches = _collect_matches(combined_text, HIGH_VALUE_KEYWORDS)
    weak_matches = _collect_matches(combined_text, WEAK_SIGNAL_KEYWORDS)

    prefixes = {code.strip().upper()[:1] for code in article.jel_codes if code.strip()}

    if high_value_matches:
        return ClassificationResult(
            decision="selected",
            reason=f"high-value keyword override: {', '.join(high_value_matches)}",
            matched_keywords=high_value_matches,
        )

    if prefixes & PRIORITY_JEL_PREFIXES:
        kept = sorted(prefixes & PRIORITY_JEL_PREFIXES)
        return ClassificationResult(
            decision="selected",
            reason=f"priority JEL match: {', '.join(kept)}",
            matched_keywords=[],
        )

    if prefixes & DOWNWEIGHT_JEL_PREFIXES:
        downgraded = sorted(prefixes & DOWNWEIGHT_JEL_PREFIXES)
        reason = f"downweighted JEL match: {', '.join(downgraded)}"
        if weak_matches:
            reason += f"; weak keywords: {', '.join(weak_matches)}"
        return ClassificationResult(
            decision="review",
            reason=reason,
            matched_keywords=weak_matches,
        )

    if weak_matches:
        return ClassificationResult(
            decision="review",
            reason=f"weak keyword signal only: {', '.join(weak_matches)}",
            matched_keywords=weak_matches,
        )

    if prefixes & REJECT_JEL_PREFIXES:
        rejected = sorted(prefixes & REJECT_JEL_PREFIXES)
        return ClassificationResult(
            decision="rejected",
            reason=f"rejected JEL match without override: {', '.join(rejected)}",
            matched_keywords=[],
        )

    return ClassificationResult(
        decision="rejected",
        reason="no priority JEL or keyword signal",
        matched_keywords=[],
    )
