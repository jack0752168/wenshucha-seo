# SEO 长文主题池(30 题起步,持续补充)

## 选题原则

1. 每篇围绕 1 个**核心目标关键词** + 3-5 个**长尾衍生词**
2. 内链到 `#api-pricing` / `#workbench` / `#api` 等高商业意图锚点
3. 1500-3000 字,有数据/案例/可执行结论
4. 每篇必须有 1 张原创 SVG 配图(品牌色卡)

---

## 中文站(wenshucha.com)— 国内律师 / 法律 AI 团队

### 高商业意图(优先级 ⭐⭐⭐⭐⭐)

| # | 标题(初稿) | 核心关键词 | 长尾 |
|---|---|---|---|
| 1 | 1.5 亿裁判文书 API 选型指南:从北大法宝、无讼到文书查 | 裁判文书API | 法律数据API/类案检索API/Alpha案例库 |
| 2 | 律师工作台:让案件胜算从「凭感觉」到「数到小数点后一位」 | 律师工作台 | 案件胜率/赔偿金额预测/类案推荐 |
| 3 | MCP Server 接入 Claude / Cursor:法律 AI 工作流实战 | MCP裁判文书 | Claude MCP法律/法律AI工作流 |
| 4 | 类案检索:语义向量 vs 关键词,哪种更准? | 类案检索API | 语义检索/法律向量检索 |
| 5 | 全量裁判文书数据库选购清单:数据 + API + MCP 三种交付方式 | 裁判文书数据 | 全国裁判文书/数据合作/SaaS |

### 长尾流量(优先级 ⭐⭐⭐⭐)

| # | 标题(初稿) | 核心关键词 |
|---|---|---|
| 6 | 怎么批量下载裁判文书?三种合规方法对比 | 裁判文书批量下载 |
| 7 | 1985 年至今全国裁判文书数据规模拆解(刑事/民事/行政/执行/赔偿) | 全国裁判文书数据 |
| 8 | 司法大数据:可视化 5 大类裁判文书时空分布 | 司法大数据 |
| 9 | 法律科技创业第 0 步:数据底座怎么选 | 法律科技数据源 |
| 10 | 高校法学实证研究的数据接入指南 | 法学实证研究数据 |
| 11 | 政府司法决策辅助:类案 + 监督的数据合作模式 | 司法大数据 |
| 12 | 法律大模型微调数据集:从清洗到结构化字段 | 法律大模型数据 |
| 13 | 文书查 vs 北大法宝 vs 无讼:数据 / API / 价格三维对比 | 北大法宝 |
| 14 | 劳动争议判决金额量化:p25 / 中位 / p75 三档怎么算 | 劳动争议判决 |
| 15 | 海外律所做中国案件:为什么需要 SinoVerdict MCP | SinoVerdict |

### 工具型 / How-to(优先级 ⭐⭐⭐)

| # | 标题(初稿) | 核心关键词 |
|---|---|---|
| 16 | 5 分钟接入文书查 MCP:Claude Desktop 实战 | Claude Desktop配置 |
| 17 | Cursor 接 MCP:法律研究流程升级 | Cursor MCP |
| 18 | REST API 接入文书查:Python / Node.js 示例 | 裁判文书API接入 |
| 19 | 文书查 search_cases 工具完整字段说明 | search_cases |
| 20 | 文书查 quantify_outcome 工具:案件胜率 + 金额量化 | quantify_outcome |

---

## 英文站(sinoverdict.wenshucha.com)— 海外律所 / 跨境法务

| # | 标题(初稿) | 核心关键词 |
|---|---|---|
| 21 | The Chinese Case Law API Buyer's Guide for International Law Firms | Chinese case law API |
| 22 | MCP Server for Legal AI: Plugging China Case Law Into Claude | MCP server legal |
| 23 | Why English-Native Chinese Legal Research Was Impossible Until Now | Chinese legal research |
| 24 | Cross-Border Enforcement: Finding PRC Precedent on Foreign Arbitral Awards | China litigation database |
| 25 | China Anti-Monopoly Enforcement: A Case Law Dataset Walkthrough | China antitrust case law |
| 26 | Using SinoVerdict MCP from Claude Desktop: 5-Minute Setup | Claude MCP China |
| 27 | The 130M Judgments Problem: How We Structured PRC Court Data | Chinese court judgments |
| 28 | Lexis vs Wolters Kluwer China vs SinoVerdict: 2026 Comparison | LexisNexis China alternative |
| 29 | What 1985-2026 Chinese Case Law Tells Us About PRC IP Enforcement | China IP litigation |
| 30 | Building China-Practice AI Workflows: The Source Stack | legal AI China |

---

## 内容生产节奏

- **MVP 期(2026-06 ~ 2026-09)**:每周 1 篇,3 个月共 12 篇
- **加速期(2026-10 ~ 2027-03)**:每周 2 篇,6 个月共 48 篇,主题池补到 100
- **稳定期(2027-04 起)**:基于 GSC + 百度统计数据反推选题

## 每篇产出工作流

1. 从主题池选 1 题 → 写 outline → AI 写正文 → Jack review
2. SVG 配图(品牌色)
3. push wenshucha-site → Lighthouse cron 自动拉 → 5 分钟上线
4. IndexNow 推送 → Bing 1 小时收录 / 百度 1-3 天
5. 内链 + 公众号 / 知乎转发分发
