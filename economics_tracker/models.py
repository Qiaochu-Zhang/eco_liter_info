from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Article:
    journal: str
    title: str
    url: str
    date: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    doi: str = ""
    jel_codes: list[str] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    decision: str = ""
    reason: str = ""
    source: str = ""

    def dedupe_key(self) -> tuple[str, str]:
        if self.doi:
            return ("doi", self.doi.strip().lower())
        if self.url:
            return ("url", self.url.strip().lower())
        return ("title", f"{self.journal.strip().lower()}::{self.title.strip().lower()}")

    def to_row(self) -> dict[str, str]:
        return {
            "journal": self.journal,
            "title": self.title,
            "date": self.date,
            "authors": "; ".join(self.authors),
            "url": self.url,
            "abstract": self.abstract,
            "doi": self.doi,
            "jel_codes": "; ".join(self.jel_codes),
            "matched_keywords": "; ".join(self.matched_keywords),
            "decision": self.decision,
            "reason": self.reason,
            "source": self.source,
        }
