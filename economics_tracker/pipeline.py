from __future__ import annotations

from pathlib import Path

from economics_tracker.classifier import classify_article
from economics_tracker.exporter import export_articles_to_excel
from economics_tracker.models import Article
from economics_tracker.sources import JournalSourceCollector


def dedupe_articles(articles: list[Article]) -> list[Article]:
    seen: set[tuple[str, str]] = set()
    unique: list[Article] = []
    for article in articles:
        key = article.dedupe_key()
        if key in seen:
            continue
        seen.add(key)
        unique.append(article)
    return unique


def apply_classification(articles: list[Article]) -> list[Article]:
    for article in articles:
        result = classify_article(article)
        article.decision = result.decision
        article.reason = result.reason
        article.matched_keywords = result.matched_keywords
    return articles


def run_pipeline(output_path: str | Path, from_date: str = "", until_date: str = "") -> Path:
    collector = JournalSourceCollector(from_date=from_date, until_date=until_date)
    articles = collector.collect()
    articles = dedupe_articles(articles)
    articles = apply_classification(articles)
    return export_articles_to_excel(articles, output_path)
