from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JournalConfig:
    name: str
    homepage: str
    rss_url: str | None = None


JOURNALS: tuple[JournalConfig, ...] = (
    JournalConfig(
        name="American Economic Review",
        homepage="https://www.aeaweb.org/journals/aer",
        rss_url="https://www.aeaweb.org/journals/aer/rss.xml",
    ),
    JournalConfig(
        name="American Economic Journal: Economic Policy",
        homepage="https://www.aeaweb.org/journals/pol",
        rss_url="https://www.aeaweb.org/journals/pol/rss.xml",
    ),
    JournalConfig(
        name="Econometrica",
        homepage="https://www.econometricsociety.org/publications/econometrica",
        rss_url=None,
    ),
    JournalConfig(
        name="Journal of Political Economy",
        homepage="https://www.journals.uchicago.edu/toc/jpe/current",
        rss_url="https://www.journals.uchicago.edu/action/showFeed?jc=jpe&type=etoc&feed=rss",
    ),
    JournalConfig(
        name="Review of Economic Studies",
        homepage="https://academic.oup.com/restud/issue/93/2",
        rss_url="https://academic.oup.com/rss/site_5332/3242.xml",
    ),
    JournalConfig(
        name="The Quarterly Journal of Economics",
        homepage="https://academic.oup.com/qje",
        rss_url="https://academic.oup.com/rss/site_5279.xml",
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
