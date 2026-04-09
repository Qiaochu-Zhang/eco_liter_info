from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser

from economics_tracker.config import JOURNALS, JournalConfig
from economics_tracker.models import Article


DEFAULT_TIMEOUT = 20
DEFAULT_USER_AGENT = "economics-journal-tracker/0.1"


def fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.json_ld: list[str] = []
        self._in_script = False
        self._script_type = ""
        self._script_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if tag == "meta":
            key = attrs_map.get("property") or attrs_map.get("name")
            value = attrs_map.get("content")
            if key and value and key not in self.meta:
                self.meta[key.lower()] = value.strip()
        if tag == "script":
            script_type = (attrs_map.get("type") or "").lower()
            if script_type == "application/ld+json":
                self._in_script = True
                self._script_type = script_type
                self._script_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_script and self._script_type == "application/ld+json":
            self._script_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._in_script:
            payload = "".join(self._script_parts).strip()
            if payload:
                self.json_ld.append(payload)
            self._in_script = False
            self._script_type = ""
            self._script_parts = []


def parse_rss_feed(xml_text: str, journal_name: str) -> list[Article]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    articles: list[Article] = []
    for item in items:
        title = _find_text(item, ("title", "{http://www.w3.org/2005/Atom}title"))
        link = _find_link(item)
        date = _find_text(
            item,
            (
                "pubDate",
                "dc:date",
                "{http://purl.org/dc/elements/1.1/}date",
                "{http://www.w3.org/2005/Atom}updated",
                "{http://www.w3.org/2005/Atom}published",
            ),
        )
        summary = _find_text(item, ("description", "summary", "{http://www.w3.org/2005/Atom}summary"))
        authors = _split_authors(
            _find_text(
                item,
                ("author", "dc:creator", "{http://purl.org/dc/elements/1.1/}creator"),
            )
        )
        doi = _extract_doi_from_item(item)
        if title and link:
            articles.append(
                Article(
                    journal=journal_name,
                    title=clean_html(title),
                    url=link.strip(),
                    date=date.strip(),
                    authors=authors,
                    abstract=clean_html(summary),
                    doi=doi,
                    source="rss",
                )
            )
    return articles


def _extract_doi_from_item(item: ET.Element) -> str:
    """Extract DOI from common RSS namespaces."""
    doi = _find_text(
        item,
        (
            "{http://prismstandard.org/namespaces/basic/2.0/}doi",
            "{http://purl.org/dc/elements/1.1/}identifier",
            "doi",
        ),
    )
    if doi:
        return _normalize_doi(doi)
    # fallback: parse from guid if it looks like a DOI URL
    guid = _find_text(item, ("guid",))
    if guid and "doi.org" in guid:
        return _normalize_doi(guid)
    return ""


def _find_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for name in names:
        child = node.find(name)
        if child is not None and child.text:
            return child.text.strip()
    return ""


def _find_link(node: ET.Element) -> str:
    direct = _find_text(node, ("link",))
    if direct:
        return direct
    for child in node.findall("{http://www.w3.org/2005/Atom}link"):
        href = child.attrib.get("href")
        if href:
            return href.strip()
    return ""


def _split_authors(raw: str) -> list[str]:
    if not raw:
        return []
    normalized = raw.replace(" and ", ";")
    return [segment.strip() for segment in normalized.split(";") if segment.strip()]


def clean_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def enrich_from_journal_page(article: Article) -> Article:
    if not article.url:
        return article
    try:
        html = fetch_url(article.url)
    except (urllib.error.URLError, TimeoutError, ValueError):
        return article

    parser = _MetaParser()
    parser.feed(html)
    json_ld_records = _parse_json_ld(parser.json_ld)

    if not article.abstract:
        article.abstract = (
            parser.meta.get("citation_abstract")
            or parser.meta.get("description")
            or _extract_json_ld_value(json_ld_records, "description")
            or article.abstract
        )

    if not article.doi:
        article.doi = (
            parser.meta.get("citation_doi")
            or _extract_json_ld_value(json_ld_records, "identifier")
            or article.doi
        )
        article.doi = _normalize_doi(article.doi)

    if not article.date:
        article.date = (
            parser.meta.get("citation_publication_date")
            or parser.meta.get("article:published_time")
            or _extract_json_ld_value(json_ld_records, "datePublished")
            or article.date
        )

    if not article.authors:
        meta_authors = [
            value
            for key, value in parser.meta.items()
            if key == "citation_author" and value.strip()
        ]
        if meta_authors:
            article.authors = meta_authors
        else:
            json_authors = _extract_json_ld_authors(json_ld_records)
            if json_authors:
                article.authors = json_authors

    if not article.jel_codes:
        article.jel_codes = _extract_jel_codes(html)

    if article.source:
        article.source += "+journal"
    else:
        article.source = "journal"
    article.abstract = clean_html(article.abstract)
    return article


def _parse_json_ld(payloads: list[str]) -> list[dict]:
    parsed: list[dict] = []
    for payload in payloads:
        try:
            raw = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(raw, list):
            parsed.extend(item for item in raw if isinstance(item, dict))
        elif isinstance(raw, dict):
            parsed.append(raw)
    return parsed


def _extract_json_ld_value(records: list[dict], key: str) -> str:
    for record in records:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_json_ld_authors(records: list[dict]) -> list[str]:
    for record in records:
        author = record.get("author")
        if isinstance(author, list):
            names = []
            for item in author:
                if isinstance(item, dict) and item.get("name"):
                    names.append(str(item["name"]).strip())
                elif isinstance(item, str):
                    names.append(item.strip())
            if names:
                return names
        if isinstance(author, dict) and author.get("name"):
            return [str(author["name"]).strip()]
        if isinstance(author, str) and author.strip():
            return [author.strip()]
    return []


def _normalize_doi(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"^https?://(dx\.)?doi\.org/", "", cleaned, flags=re.IGNORECASE)
    return cleaned


CROSSREF_API = "https://api.crossref.org/works/{doi}"
CROSSREF_JOURNAL_API = "https://api.crossref.org/journals/{issn}/works"
CROSSREF_USER_AGENT = "economics-journal-tracker/0.1 (mailto:tracker@example.com)"


def enrich_from_crossref(article: Article) -> Article:
    """Fetch structured metadata from Crossref by DOI."""
    if not article.doi:
        return article
    url = CROSSREF_API.format(doi=urllib.parse.quote(article.doi, safe="/:"))
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": CROSSREF_USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace")).get("message", {})
    except Exception:
        return article

    if not article.authors:
        raw_authors = data.get("author", [])
        article.authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in raw_authors
            if a.get("family")
        ]

    if not article.abstract:
        article.abstract = clean_html(data.get("abstract", ""))

    if not article.date:
        date_parts = (
            data.get("published", {}).get("date-parts")
            or data.get("published-print", {}).get("date-parts")
            or data.get("published-online", {}).get("date-parts")
            or [[]]
        )
        if date_parts and date_parts[0]:
            article.date = "-".join(str(p) for p in date_parts[0])

    if not article.jel_codes:
        subjects = data.get("subject", [])
        jel = [s.strip() for s in subjects if re.match(r"^[A-Z]\d{1,2}$", s.strip())]
        if jel:
            article.jel_codes = jel

    article.source = (article.source + "+crossref").lstrip("+")
    return article


def collect_from_crossref_journal(
    journal: JournalConfig,
    from_date: str,
    until_date: str,
) -> list[Article]:
    """Search Crossref for articles in a journal by ISSN and date range."""
    if not journal.issn:
        return []
    params = urllib.parse.urlencode({
        "filter": f"from-pub-date:{from_date},until-pub-date:{until_date}",
        "rows": 50,
        "sort": "published",
        "order": "desc",
        "select": "DOI,title,author,abstract,published,published-online,published-print,URL,subject,type",
    })
    url = CROSSREF_JOURNAL_API.format(issn=journal.issn) + "?" + params
    try:
        request = urllib.request.Request(url, headers={"User-Agent": CROSSREF_USER_AGENT})
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as resp:
            items = json.loads(resp.read().decode("utf-8", errors="replace")).get("message", {}).get("items", [])
    except Exception:
        return []

    articles: list[Article] = []
    for item in items:
        # skip non-article types (e.g. book-review, editorial)
        if item.get("type") not in ("journal-article", None):
            continue
        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""
        if not title:
            continue
        doi = item.get("DOI", "")
        art_url = item.get("URL", "") or (f"https://doi.org/{doi}" if doi else "")
        raw_authors = item.get("author", [])
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in raw_authors
            if a.get("family")
        ]
        date_parts = (
            item.get("published", {}).get("date-parts")
            or item.get("published-print", {}).get("date-parts")
            or item.get("published-online", {}).get("date-parts")
            or [[]]
        )
        date = "-".join(str(p) for p in date_parts[0]) if date_parts and date_parts[0] else ""
        abstract = clean_html(item.get("abstract", ""))
        subjects = item.get("subject", [])
        jel = [s.strip() for s in subjects if re.match(r"^[A-Z]\d{1,2}$", s.strip())]
        articles.append(Article(
            journal=journal.name,
            title=clean_html(title),
            url=art_url,
            date=date,
            authors=authors,
            abstract=abstract,
            doi=doi,
            jel_codes=jel,
            source="crossref-journal",
        ))
    return articles


def _extract_jel_codes(html: str) -> list[str]:
    matches = re.findall(r"\b([A-Z][0-9]{1,2})\b", html)
    unique: list[str] = []
    for code in matches:
        if code not in unique:
            unique.append(code)
    return unique


@dataclass
class RepecIdeasProvider:
    """Scaffold provider for future structured metadata enrichment."""

    enabled: bool = False

    def enrich(self, article: Article) -> Article:
        # Real endpoint logic should be added here once stable sources are confirmed.
        return article


class JournalSourceCollector:
    def __init__(self, provider: RepecIdeasProvider | None = None) -> None:
        self.provider = provider or RepecIdeasProvider()

    def collect(self) -> list[Article]:
        articles: list[Article] = []
        for journal in JOURNALS:
            articles.extend(self._collect_for_journal(journal))
        return articles

    def _collect_for_journal(self, journal: JournalConfig) -> list[Article]:
        seeded: list[Article] = []

        # 1. Try RSS — collect everything the feed currently contains
        if journal.rss_url:
            try:
                feed = fetch_url(journal.rss_url)
            except (urllib.error.URLError, TimeoutError, ValueError):
                feed = ""
            if feed:
                seeded.extend(parse_rss_feed(feed, journal.name))

        # 2. Crossref fallback when RSS unavailable or empty:
        #    only keep articles whose issue was published in the current month
        if not seeded and journal.issn:
            import datetime
            today = datetime.date.today()
            from_date = today.strftime("%Y-%m-01")
            until_date = today.strftime("%Y-%m-%d")
            candidates = collect_from_crossref_journal(journal, from_date, until_date)
            current_ym = (today.year, today.month)
            for art in candidates:
                if _article_issue_month(art) == current_ym:
                    seeded.append(art)

        # 3. Enrich each article: Crossref by DOI → journal page
        for article in seeded:
            self.provider.enrich(article)
            if article.source != "crossref-journal":
                enrich_from_crossref(article)
            enrich_from_journal_page(article)

        return seeded


def _article_issue_month(article: Article) -> tuple[int, int] | None:
    """Parse (year, month) from article.date; return None if unparseable."""
    import datetime
    raw = (article.date or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            d = datetime.datetime.strptime(raw[:len(fmt) + 2], fmt)
            return (d.year, d.month)
        except ValueError:
            continue
    # try partial "YYYY-M" or "YYYY"
    parts = raw.split("-")
    try:
        if len(parts) >= 2:
            return (int(parts[0]), int(parts[1]))
        if len(parts) == 1 and parts[0].isdigit():
            return (int(parts[0]), 1)
    except ValueError:
        pass
    return None
