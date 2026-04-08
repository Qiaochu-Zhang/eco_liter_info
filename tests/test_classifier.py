from economics_tracker.classifier import classify_article
from economics_tracker.models import Article


def test_priority_jel_is_selected() -> None:
    article = Article(
        journal="Test Journal",
        title="Firm Dynamics",
        url="https://example.com/a",
        jel_codes=["D24"],
    )
    result = classify_article(article)
    assert result.decision == "selected"
    assert "priority JEL match" in result.reason


def test_high_value_keyword_overrides_rejected_jel() -> None:
    article = Article(
        journal="Test Journal",
        title="Carbon Tax and Welfare",
        url="https://example.com/b",
        jel_codes=["N10"],
        abstract="A model of carbon tax adoption.",
    )
    result = classify_article(article)
    assert result.decision == "selected"
    assert "carbon tax" in result.reason


def test_downweighted_jel_is_review() -> None:
    article = Article(
        journal="Test Journal",
        title="Education Policy and Outcomes",
        url="https://example.com/c",
        jel_codes=["I21"],
    )
    result = classify_article(article)
    assert result.decision == "review"


def test_rejected_when_no_signal() -> None:
    article = Article(
        journal="Test Journal",
        title="Archival Notes",
        url="https://example.com/d",
        jel_codes=["B00"],
    )
    result = classify_article(article)
    assert result.decision == "rejected"
