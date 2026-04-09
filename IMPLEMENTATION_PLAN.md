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

---

## 7. 开发日志

### 2026-04-09

#### RSS 配置更新（`config.py`）

更新6本期刊的 RSS 地址为可用端点，并补充 ISSN 字段：

| 期刊 | RSS | ISSN |
|------|-----|------|
| AER | https://rsshub.app/aeaweb/aer | 0002-8282 |
| AEJ: Economic Policy | https://rsshub.app/aeaweb/pol | 1945-7731 |
| Econometrica | https://onlinelibrary.wiley.com/feed/14680262/most-recent | 0012-9682 |
| JPE | https://www.journals.uchicago.edu/action/showFeed?type=etoc&feed=rss&jc=jpe | 0022-3808 |
| REStud | https://academic.oup.com/rss/site_5508/3369.xml | 0034-6527 |
| QJE | https://academic.oup.com/rss/site_5504/3365.xml | 0033-5533 |

#### Crossref 集成（`sources.py`）

**问题**：AER / AEJ:Policy 的 rsshub.app RSS 返回 403；JPE 的官方 RSS 返回 0 条；所有期刊 RSS 均不含作者信息；期刊文章页面全部返回 403，无法页面富化。

**方案**：使用 [Crossref API](https://api.crossref.org) 作为第三方数据源。

新增两个函数：

- `enrich_from_crossref(article)`：对 RSS 已抓到的文章，按 DOI 查 Crossref 补充作者、摘要、发表日期。
- `collect_from_crossref_journal(journal, from_date, until_date)`：当 RSS 不可用或返回空时，按 ISSN + 日期范围搜索 Crossref，作为 fallback 数据源。直接返回完整文章元数据（标题、作者、摘要、DOI、发表日期）。

同时在 `parse_rss_feed` 中新增 `_extract_doi_from_item()`，从 RSS 的 PRISM / DC 命名空间及 guid 字段中提取 DOI，供后续 Crossref 富化使用。

#### 采集策略更新（`sources.py` → `JournalSourceCollector`）

每本期刊的采集顺序：
1. 尝试 RSS
2. 若 RSS 为空或失败，且 `from_date` 已指定，则调用 `collect_from_crossref_journal` fallback
3. 对 RSS 来源的文章调用 `enrich_from_crossref` 补充字段；对 Crossref journal 来源跳过（已完整）
4. 尝试期刊页面富化（当前因 403 无效，保留作未来 fallback）

#### CLI 参数更新（`main.py` / `pipeline.py`）

新增 `--from-date YYYY-MM-DD` 和 `--until-date YYYY-MM-DD` 参数，传入 pipeline 控制 Crossref 搜索日期范围。日常运行示例：

```bash
python3 main.py --output output/2026-04-09.xlsx --from-date 2026-04-09 --until-date 2026-04-09
```

#### 导出格式（`config.py` / `exporter.py`）

恢复完整导出列（12列），Excel 双 sheet 结构不变：

- **selected** sheet：decision = `selected`
- **rejected** sheet：decision = `review` 或 `rejected`

#### 运行结果验证

用 `--from-date 2026-01-01 --until-date 2026-04-09` 测试，6本期刊全部有数据：

| Sheet | 文章数 | 有作者数 |
|-------|--------|----------|
| selected | 12 | 12 |
| rejected | 143 | 125 |

各期刊分布：AER 44、AEJ:Policy 12、Econometrica 14、JPE 50、REStud 20、QJE 15。

#### 已知限制

- JEL codes 全部为空：Crossref 对这些期刊不返回 JEL 分类，分类当前完全依赖关键词规则
- AER / AEJ:Policy 在 rsshub.app 可用时优先走 RSS，当前因 403 自动 fallback 到 Crossref
