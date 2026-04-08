# TASK.md

## 项目目标

开发一个运行在 EC2 上的自动化经济学期刊追踪系统，每天定时检查指定期刊的新文献，结合 RSS、第三方信息源（优先 RePEc / IDEAS）和期刊官网抓取元数据，对文献进行筛选，并最终输出为一个 Excel 文件。

系统目标不是只保留入选文献，而是同时保留：

1. 筛选后的高相关文献
2. 落选的其他文献

最终统一写入 **同一个 Excel 文件的两个 sheet** 中，方便后续人工复核。

---

## 追踪期刊

* American Economic Review (AER)
  https://www.aeaweb.org/journals/aer

* American Economic Journal: Economic Policy
  https://www.aeaweb.org/journals/pol

* Econometrica
  https://www.econometricsociety.org/publications/econometrica

* Journal of Political Economy (JPE)
  https://www.journals.uchicago.edu/toc/jpe/current

* Review of Economic Studies (REStud)
  https://academic.oup.com/restud/issue/93/2

* The Quarterly Journal of Economics (QJE)
  https://academic.oup.com/qje

---

## 数据源策略

采用多源混合方案，不依赖单一来源。

### 1. RSS（用于更新检测）

* 优先使用官方 RSS 或可用 RSS
* JPE 可作为重点 RSS 来源
* 其他没有稳定 RSS 的期刊，不强依赖 RSS

用途：

* 检测是否有新文章
* 尽量减少全站重复爬取

### 2. 第三方来源（优先 RePEc / IDEAS）

优先从第三方获取结构化信息：

目标字段：

* title
* authors
* date
* abstract
* doi
* url
* JEL codes（如果有）

用途：

* 作为主数据源
* 优先拿摘要、作者、日期等字段

### 3. 期刊官网（fallback）

如果第三方缺失字段，则回源期刊官网抓取。

重点补充：

* abstract
* authors
* published date
* JEL codes
* article link

---

## 筛选规则

### 一、期刊范围

仅处理上述 6 本期刊。

### 二、JEL 分类规则

#### 默认优先保留

* D — Microeconomics
* E — Macroeconomics
* F — International Economics
* O — Economic Development / Innovation / Growth
* Q — Energy / Environment / Climate

#### 默认降权，不直接删除

* I — Health / Education / Welfare
* J — Labor / Demographic Economics
* M — Business / Marketing / Accounting / Personnel

#### 默认排除

* A — General Economics and Teaching
* B — History of Economic Thought / Methodology / Heterodox
* C — Mathematical and Quantitative Methods
* N — Economic History

### 三、高价值关键词 override 规则

若标题或摘要中出现以下关键词，即使 JEL 属于默认排除类，也重新纳入候选或直接标记为高优先级：

#### 科技与创新

* R&D
* Automation
* General Purpose Technology
* GPT
* Patent
* Total Factor Productivity
* TFP
* Endogenous Growth

#### 能源与气候

* Carbon Tax
* Green Transition
* Renewable Energy
* Climate Risk
* Emissions Trading
* Stranded Assets

#### 宏观与政策

* Fiscal Policy
* Monetary Policy
* Monetary Policy Transmission
* Industrial Policy
* Global Value Chains
* Supply Chain
* Supply Chain Resilience

---

## 最终分类逻辑

每篇文章最终应被标记为以下三类之一：

* `selected`

  * 明显符合重点方向
  * JEL 在优先保留范围内，或命中高价值关键词

* `review`

  * 相关性一般，建议保留到落选页中供人工复核
  * JEL 降权类，或只有弱关键词命中

* `rejected`

  * 明显不相关
  * JEL 在排除类，且未命中高价值关键词

注意：

* 输出 Excel 时，`selected` 单独放一页
* `review` 和 `rejected` 一起放入 `rejected` 页，保留原因字段，方便人工看为什么落选或待复核

---

## Excel 输出要求

最终输出一个 Excel 文件，例如：

`economics_journals_daily.xlsx`

包含两个 sheet：

### Sheet 1: `selected`

存放筛选后的高相关文献

字段至少包括：

* journal
* title
* date
* authors
* url
* abstract
* doi
* jel_codes
* matched_keywords
* decision
* reason
* source

### Sheet 2: `rejected`

存放落选或待复核的其他文献

字段至少包括：

* journal
* title
* date
* authors
* url
* abstract
* doi
* jel_codes
* matched_keywords
* decision
* reason
* source

说明：

* `decision` 取值为 `review` 或 `rejected`
* `reason` 需要说明落选或待复核原因，例如：

  * excluded_jel
  * low_relevance
  * missing_jel_keyword_only
  * deprioritized_jel
  * weak_keyword_match

---

## 去重规则

多源数据合并时必须去重，优先级如下：

1. DOI
2. URL
3. title + journal

要求：

* 同一篇文章只能在最终结果中出现一次
* 不能同时出现在 `selected` 和 `rejected` 两页
* 合并时优先保留字段更完整的记录

---

## 每日运行要求

系统部署在 EC2 上，每天自动执行一次。

建议方式：

* cron
* 或 systemd timer

例如：

```bash
0 9 * * * /usr/bin/python3 /path/to/project/main.py
```

---

## 日志要求

每次运行需要输出日志，至少包括：

* run date
* source fetch status
* number of articles fetched
* number of articles selected
* number of articles rejected/review
* number of errors
* error details

建议输出到：

* `logs/YYYY-MM-DD.log`

---

## 项目目录建议

```text
project/
  main.py
  config.yaml
  journals/
    aer.py
    aej_policy.py
    econometrica.py
    jpe.py
    restud.py
    qje.py
  sources/
    rss_client.py
    repec_client.py
  filters/
    jel_filter.py
    keyword_filter.py
    decision_engine.py
  outputs/
    excel_writer.py
  logs/
  data/
```

---

## 核心模块要求

### 1. Source ingestion

实现多源抓取：

* RSS update detection
* RePEc / IDEAS metadata fetch
* journal fallback scrape

### 2. Parsing

统一解析出标准字段：

* journal
* title
* date
* authors
* abstract
* url
* doi
* jel_codes

### 3. Filtering

根据 JEL + keywords 生成：

* matched_keywords
* decision
* reason

### 4. Excel export

将结果写入同一个 Excel 文件中的两个 sheet：

* selected
* rejected

建议使用：

* pandas
* openpyxl

---

## 最小可行版本（MVP）

### Phase 1

先完成：

* JPE
* AER
* AEJ Policy

实现：

* 抓取基础元数据
* JEL + keyword 筛选
* 输出 Excel 两页

### Phase 2

加入：

* Econometrica
* REStud
* QJE

实现：

* fallback 抓取
* 去重增强
* 日志稳定化

### Phase 3

增强：

* 更稳的第三方源集成
* 缺失 JEL 的 fallback 处理
* 后续可接 LLM 做 relevance summary

---

## 缺失字段处理要求

### JEL 缺失

处理顺序：

1. 第三方源读取
2. 官网补抓
3. 若仍缺失，则根据关键词规则判定
4. 保留 `reason` 标记，例如 `missing_jel_keyword_only`

### Abstract 缺失

处理顺序：

1. 第三方源读取
2. 官网补抓
3. 若仍缺失，abstract 允许为空，但必须保留记录

### Date / Authors 缺失

允许为空，但优先通过官网补齐

---

## 验收标准

完成后必须满足：

1. 能在 EC2 上运行
2. 支持每日定时执行
3. 至少对目标期刊中的一部分成功抓取新文献
4. 能根据规则生成 `selected` / `review` / `rejected`
5. 最终生成一个 Excel 文件
6. Excel 中必须有两个 sheet：

   * `selected`
   * `rejected`
7. 两个 sheet 都包含：

   * 标题
   * 日期
   * 作者
   * 链接
   * 摘要
8. 日志可追踪错误和运行结果
9. 有基本去重能力
10. 不依赖单一数据源

---

## 开发原则

* 不要一开始追求所有期刊一次性全打通
* 先做可运行 MVP，再逐步扩展
* 优先保证：

  1. 抓到文献
  2. 输出 Excel
  3. 分类结果稳定
* 页面结构不同的期刊，parser 分开写，不要硬合并成一个 parser
* 第三方源不是完全可靠，必须保留官网 fallback

---

## 最终目标

形成一个可长期运行的、每天自动更新的经济学期刊追踪系统：

* 自动发现新文献
* 自动提取元数据
* 自动按规则筛选
* 自动生成 Excel
* 让人工只需要查看 `selected` 和 `rejected` 两页即可完成后续判断
