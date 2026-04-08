# Economics Journal Tracker Implementation Plan

## 1. Scope

Build a daily pipeline for six economics journals that:

- checks for newly published articles from RSS where available
- enriches metadata from structured third-party sources first
- falls back to journal pages when fields are missing
- classifies every article into `selected`, `review`, or `rejected`
- writes one Excel file with two sheets: `selected` and `rejected`

## 2. Architecture

### 2.1 Pipeline stages

1. Source discovery
   - poll RSS feeds when configured
   - optionally seed direct journal landing pages
2. Metadata enrichment
   - use third-party providers first
   - backfill missing fields from journal pages
3. Normalization
   - map fields into a single article schema
   - deduplicate by DOI, then URL, then title-plus-journal
4. Classification
   - apply JEL preferences
   - apply keyword overrides
   - produce decision and reason
5. Export
   - write `selected` rows to sheet `selected`
   - write `review` and `rejected` rows to sheet `rejected`

### 2.2 Modules

- `economics_tracker/config.py`
  - journal list
  - JEL rule sets
  - keyword groups
- `economics_tracker/models.py`
  - normalized article dataclass
- `economics_tracker/classifier.py`
  - decision engine
- `economics_tracker/sources.py`
  - RSS fetcher
  - third-party provider interface
  - journal fallback fetcher
- `economics_tracker/exporter.py`
  - Excel writer
- `economics_tracker/pipeline.py`
  - orchestration
- `main.py`
  - CLI entrypoint

## 3. Source Strategy

### 3.1 RSS

Use RSS only as a lightweight change detector. If a journal has no stable RSS, the journal can still be included with a direct seed URL and fallback scraping path.

### 3.2 Third-party metadata

Abstract third-party providers behind a common interface. Initial implementation includes a provider scaffold for RePEc / IDEAS style search endpoints so later changes do not affect the pipeline contract.

### 3.3 Journal fallback

When the third-party source lacks abstract, authors, date, JEL, DOI, or canonical link, fetch the article page and recover fields from:

- meta tags
- JSON-LD
- visible abstract blocks

## 4. Classification Rules

- `selected`
  - JEL prefix in `D`, `E`, `F`, `O`, `Q`
  - or hits any high-value keyword override
- `review`
  - JEL prefix in `I`, `J`, `M`
  - or only weak partial keyword signals
- `rejected`
  - JEL prefix in `A`, `B`, `C`, `N` with no override
  - or no positive signals at all

The output stores both the final `decision` and a human-readable `reason`.

## 5. Deliverables

- implementation plan document
- runnable Python package
- CLI for daily execution
- Excel export
- unit tests for decision and export routing

## 6. Future Production Work

- persist seen article IDs between daily runs
- add rate limiting and retries per domain
- implement real RePEc / IDEAS extraction against stable endpoints
- add CloudWatch-friendly logging and cron / systemd integration on EC2
