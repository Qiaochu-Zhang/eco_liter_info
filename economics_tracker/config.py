from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JournalConfig:
    name: str
    homepage: str
    rss_url: str | None = None
    issn: str = ""  # used for Crossref journal search fallback


JOURNALS: tuple[JournalConfig, ...] = (
    JournalConfig(
        name="American Economic Review",
        homepage="https://www.aeaweb.org/journals/aer",
        rss_url="https://rsshub.app/aeaweb/aer",
        issn="0002-8282",
    ),
    JournalConfig(
        name="American Economic Journal: Economic Policy",
        homepage="https://www.aeaweb.org/journals/pol",
        rss_url="https://rsshub.app/aeaweb/pol",
        issn="1945-7731",
    ),
    JournalConfig(
        name="Econometrica",
        homepage="https://www.econometricsociety.org/publications/econometrica",
        rss_url="https://onlinelibrary.wiley.com/feed/14680262/most-recent",
        issn="0012-9682",
    ),
    JournalConfig(
        name="Journal of Political Economy",
        homepage="https://www.journals.uchicago.edu/toc/jpe/current",
        rss_url="https://www.journals.uchicago.edu/action/showFeed?type=etoc&feed=rss&jc=jpe",
        issn="0022-3808",
    ),
    JournalConfig(
        name="Review of Economic Studies",
        homepage="https://academic.oup.com/restud",
        rss_url="https://academic.oup.com/rss/site_5508/3369.xml",
        issn="0034-6527",
    ),
    JournalConfig(
        name="The Quarterly Journal of Economics",
        homepage="https://academic.oup.com/qje",
        rss_url="https://academic.oup.com/rss/site_5504/3365.xml",
        issn="0033-5533",
    ),
)

PRIORITY_JEL_PREFIXES = {"D", "E", "F", "O", "Q"}
DOWNWEIGHT_JEL_PREFIXES = {"I", "J", "M"}
REJECT_JEL_PREFIXES = {"A", "B", "C", "N"}

HIGH_VALUE_KEYWORDS = (
    "r&d",
    "automation",
    "general purpose technology",
    "gpt",
    "patent",
    "total factor productivity",
    "tfp",
    "endogenous growth",
    "carbon tax",
    "green transition",
    "renewable energy",
    "climate risk",
    "emissions trading",
    "stranded assets",
    "fiscal policy",
    "monetary policy",
    "monetary policy transmission",
    "industrial policy",
    "global value chains",
    "supply chain",
    "supply chain resilience",
)

WEAK_SIGNAL_KEYWORDS = (
    "innovation",
    "productivity",
    "energy",
    "climate",
    "trade",
    "development",
    "policy",
)

EXPORT_COLUMNS = (
    "journal",
    "title",
    "date",
    "authors",
    "url",
    "abstract",
    "doi",
    "jel_codes",
    "matched_keywords",
    "decision",
    "reason",
    "source",
)
