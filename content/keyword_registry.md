# 关键词资产库

> 自动生成 2026-07-22 · `python3 scripts/kw_registry.py`
> 依据白杨方法论的「长尾关键词记录单」。最小字段=关键词+对应URL,
> 用途:写文时调用做内链锚文本 / 避免重复做词 / 把工作变成有明确待办。

**88 个页面 · 608 个去重词 · 42 个词冲突**

## 一、按白杨五类词分布

| 类型 | 词数 | 搜索意图 | 该做成什么页 | 转化价值 |
|---|---|---|---|---|
| **品牌词** | 5 | 已认定你,只找入口 | 首页 / 品牌介绍 / 联系方式 | ★★★★★（量最小） |
| **产品词** | 54 | 知道要什么,没认准谁家 | 产品详情 / 案例 / 价格说明 | ★★★★ |
| **痛点词** | 46 | 找解决方案,可能还不知道有你 | 干货长文 + 咨询入口 | ★★★★ |
| **场景词** | 23 | 特定情境下的临时需求 | 场景专题 / 时令推荐 | ★★ |
| **长尾词** | 344 | 已经很具体,目的性强 | 问答型 / 对比评测 / 长尾专题 | ★★★（总量大） |
| **核心词** | 136 | 宽泛,竞争最激烈 | 栏目页 | ★★ |

> ⚠️ 分类由规则自动判定,边界词可能归错。**用来看结构比例,别当精确统计。**

## 二、词冲突（白杨硬约束：不同栏目的长尾词不得交叉重叠）

**42 个词被多个页面同时抢**——站内自己打架，会互相稀释排名。

| 关键词 | 抢的页面数 | 页面 |
|---|---|---|
| 裁判文书数据库 | 4 | /blog/judgment-corpus-private-deployment-architecture.html<br/>/case-search/<br/>/data/<br/>/ |
| 司法机关数据中台 | 3 | /blog/court-ai-procurement-checklist.html<br/>/blog/judicial-data-platform-construction.html<br/>/blog/judicial-data-platform-security-compliance.html |
| 等保三级 法律 AI | 3 | /blog/court-ai-procurement-checklist.html<br/>/blog/law-firm-on-prem-llm-gpu-guide.html<br/>/blog/law-firm-private-ai-deployment-guide.html |
| 司法大数据 | 3 | /blog/<br/>/data/<br/>/ |
| 裁判文书 API | 3 | /blog/<br/>/blog/judgment-api-integration-python-nodejs.html<br/>/blog/legal-empirical-research-data-access.html |
| 1.6 亿裁判文书 | 3 | /blog/judgment-corpus-private-deployment-architecture.html<br/>/data/<br/>/ |
| 类案检索 | 3 | /blog/lawyer-workbench-case-win-rate.html<br/>/case-search/<br/>/ |
| 数字法治政府方案 | 2 | /blog/court-ai-procurement-checklist.html<br/>/blog/judicial-data-platform-construction.html |
| 类案推送系统 | 2 | /blog/court-ai-procurement-checklist.html<br/>/blog/court-similar-case-recommendation-system.html |
| 法院 AI 智能审判辅助 | 2 | /blog/court-ai-procurement-checklist.html<br/>/blog/court-ai-trial-assistance-sentencing-document.html |
| 信创 法律 AI | 2 | /blog/court-ai-procurement-checklist.html<br/>/blog/xinchuang-domestic-stack-legal-ai-deployment.html |
| 法官办案辅助系统 | 2 | /blog/court-ai-trial-assistance-sentencing-document.html<br/>/blog/court-similar-case-recommendation-system.html |
| 律所私有 AI 部署 | 2 | /blog/<br/>/blog/law-firm-private-ai-deployment-guide.html |
| 法律科技 | 2 | /blog/<br/>/blog/lawyer-workbench-case-win-rate.html |
| 裁判文书 API 接入 | 2 | /blog/judgment-api-integration-python-nodejs.html<br/>/blog/wenshucha-mcp-claude-desktop-setup.html |
| 类案检索 API | 2 | /blog/judgment-api-integration-python-nodejs.html<br/>/blog/similar-case-retrieval-semantic-vs-keyword.html |
| 裁判文书全文检索 | 2 | /blog/judgment-corpus-private-deployment-architecture.html<br/>/case-search/ |
| 等保三级数据中台 | 2 | /blog/judicial-data-platform-construction.html<br/>/blog/judicial-data-platform-security-compliance.html |
| 政法数据安全 | 2 | /blog/judicial-data-platform-security-compliance.html<br/>/blog/legal-ai-data-security-audit-mlps-evaluation.html |
| 律所 AI 采购 | 2 | /blog/law-firm-ai-procurement-pitfalls.html<br/>/blog/law-firm-private-ai-deployment-guide.html |
| 法律 AI 选型 | 2 | /blog/law-firm-ai-procurement-pitfalls.html<br/>/blog/legal-data-platform-comparison-2026.html |
| 法律大模型采购 | 2 | /blog/law-firm-ai-procurement-pitfalls.html<br/>/buyers-guide/ |
| 法律 LLM 内网部署 | 2 | /blog/law-firm-llm-finetune-case-archive.html<br/>/blog/law-firm-on-prem-llm-gpu-guide.html |
| 法律大模型微调 | 2 | /blog/law-firm-llm-finetune-case-archive.html<br/>/blog/legal-ai-rag-vs-finetune-technical-route.html |
| 律所内网大模型 | 2 | /blog/law-firm-on-prem-llm-gpu-guide.html<br/>/blog/law-firm-private-ai-deployment-guide.html |

**处理原则**：一词一页。留意图最匹配的那个页保住这个词，其余页把该词从 keywords 里删掉，
改用各自的差异化长尾词。

## 三、抓取状态（nginx 一手数据）

_本机拿不到 nginx 日志（不是站点服务器）。在腾讯云上跑本脚本可得。_

## 四、全量台账（关键词 → URL）

| 页面 | 标题 | 关键词 |
|---|---|---|
| `/blog/court-ai-procurement-checklist.html` | 地方法院信息中心 AI 系统采购清单:智慧法院选型与避坑(2026)丨 文书 | 法院信息中心 AI、智慧法院建设、数字法治政府方案、法院 AI 系统采购、类案推送系统、司法机关数据中台、政府司法 AI 解决方案、法院 AI 智能审判辅助… |
| `/blog/court-ai-trial-assistance-sentencing-document.html` | 法院 AI 智能审判辅助怎么落地:量刑参考 + 文书辅助生成实战(2026) | 法院 AI 智能审判辅助、量刑参考系统、智能量刑辅助、文书辅助生成、法官办案辅助系统、审判辅助系统、类案量刑、智慧法院审判辅助… |
| `/blog/court-similar-case-recommendation-system.html` | 法院类案推送系统怎么建:从数据底座到模型到法官界面(2026)丨 文书查 | 类案推送系统、法院类案检索系统、类案同判、智慧法院类案推送、法院类案智能推送、类案检索语义模型、法官办案辅助系统、强制类案检索… |
| `/blog/` | 洞察 · 法律 AI / 司法数据干货 丨 文书查 | 法律 AI、律所私有 AI 部署、司法大数据、裁判文书 API、法律科技、文书查洞察 |
| `/blog/judgment-api-integration-python-nodejs.html` | 裁判文书 API 接入实战:Python / Node.js 代码示例(20 | 裁判文书 API 接入、裁判文书 API、法律数据 API、案例检索 API、Python 接入裁判文书、Node.js 法律 API、法律 AI 数据接口、类案检索 API… |
| `/blog/judgment-corpus-private-deployment-architecture.html` | 1.6 亿裁判文书私有库:本地化部署的数据架构(2026)丨 文书查 | 裁判文书数据私有部署、裁判文书数据库、1.6 亿裁判文书、裁判文书私有库、法律数据本地化部署、裁判文书全文检索、裁判文书向量检索、法律 RAG 数据底座… |
| `/blog/judicial-data-platform-construction.html` | 数字法治政府:司法数据中台建设方案(2026)——架构、等保三级与数据治理  | 数字法治政府方案、司法数据中台、司法机关数据中台、政法数据中台、政法委大数据、司法大数据平台、政法跨部门数据共享、等保三级数据中台… |
| `/blog/judicial-data-platform-security-compliance.html` | 司法机关数据中台等保三级合规架构(2026)——定级备案、安全建设与测评清单 | 等保三级数据中台、司法机关数据中台、司法数据中台等保三级、等保三级合规架构、政法专网等保、政法数据安全、数据分类分级 司法、司法数据安全审计… |
| `/blog/law-firm-ai-adoption-user-enablement.html` | 律所买了 AI 却没人用:法律 AI 落地后的培训、adoption 与用户 | 法律AI培训、律所AI adoption、法律AI用户运营、律师AI使用率、法律AI落地推广、律所AI用不起来、法律AI落地、律师工作台推广… |
| `/blog/law-firm-ai-procurement-pitfalls.html` | 律所采购 AI 系统的 5 个坑:SaaS / 数据 / 模型 / 工具链  | 律所 AI 采购、律所法律 AI 采购、法律 AI 选型、律所 AI 系统采购、律所私有化部署采购、法律大模型采购、律所 AI 供应商、法律 AI 避坑… |
| `/blog/law-firm-ai-roi-calculation.html` | 律所 AI 投资回报测算:从 IT 预算到合伙人时薪,这笔账怎么算(2026 | 律所私有 AI ROI、律所 AI 投资回报、法律 AI 成本测算、律所私有化部署成本、律师工时节省、律所 AI 采购预算、法律 AI 回本周期、律所 AI 投入产出 |
| `/blog/law-firm-data-compliance-confidentiality.html` | 律所私有化部署如何满足客户保密义务:数据合规落地指南(2026)丨 文书查 | 律所数据合规、律所保密义务、客户保密义务 AI、律所私有化部署合规、律师执业保密、法律 AI 数据出域、律所等保三级、律所数据安全法合规… |
| `/blog/law-firm-llm-finetune-case-archive.html` | 法律大模型微调:用本所历史卷宗叠加,效果到底有没有(2026)丨 文书查 | 法律 LLM 内网部署、法律大模型微调、律所卷宗微调、法律大模型 LoRA、律所私有大模型、指令微调 法律、法律 RAG vs 微调、本所历史卷宗 |
| `/blog/law-firm-on-prem-llm-gpu-guide.html` | 律所内网大模型部署实战:GPU 选型、数据合规、用户权限怎么落地(2026) | 律所内网 AI、律所内网大模型、法律 LLM 内网部署、律所 GPU 选型、法律大模型私有部署、律所信息化、等保三级 法律 AI、法律 AI 权限分级… |
| `/blog/law-firm-private-ai-deployment-guide.html` | 律所 AI 私有化部署完全指南:数据+模型+合规+采购清单(2026)丨 文 | 律所私有 AI 部署、法律 AI 私有化、律所内网大模型、司法数据本地化、律所信息化、法律大模型私有部署、律所 AI 采购、等保三级 法律 AI… |
| `/blog/law-firm-rag-knowledge-base.html` | 律所知识库怎么建:卷宗/合同/类案三库一体的 RAG 落地实战(2026)丨 | 律所知识库、律所 RAG、律所知识管理、法律 RAG 落地、律所知识库建设、卷宗知识库、律所内部检索、律所大模型知识库… |
| `/blog/lawyer-workbench-case-win-rate.html` | 律师工作台:把案件胜算从「凭感觉」做到「有区间、有依据」(2026 实战)丨 | 律师工作台、案件胜算预测、胜诉率预测、赔偿区间测算、类案检索、法律 AI 工作台、案件研判系统、律所办案系统… |
| `/blog/legal-ai-acceptance-testing-evaluation.html` | 法律大模型怎么验收:效果测评方法与验收指标实战(2026)丨 文书查 | 法律 AI 验收、法律大模型测评、法律 AI 效果评测、法律 AI 验收标准、法律大模型评测方法、法律 AI 引用错误率、法律 AI POC、司法 AI 验收方案… |
| `/blog/legal-ai-capacity-planning-scaling.html` | 律所私有化法律 AI 的算力容量规划与扩容实战:多少 GPU 够用、什么时候 | 律所AI算力规划、私有化法律AI GPU数量、法律大模型并发容量、律所AI扩容、私有化AI容量评估、法律AI推理并发、GPU显存规划、KV cache 显存估算… |
| `/blog/legal-ai-continuous-operation-iteration.html` | 法律 AI 上线只是开始:数据回流、持续运营与模型迭代实战(2026)丨 文 | 法律AI持续运营、法律AI数据回流、法律大模型迭代、法律AI运维、法律AIbadcase治理、法律AI效果监控、法律AI持续优化、法律AI上线后运营… |
| `/blog/legal-ai-cutover-data-migration.html` | 律所私有化法律 AI 的上线切换与数据迁移实战:从旧系统平滑割接到新平台(2 | 法律AI上线切换、律所系统数据迁移、私有化AI割接、法律AI灰度上线、卷宗数据迁移、律所知识库迁移、法律AI并行运行、旧案例库迁移… |
| `/blog/legal-ai-data-security-audit-mlps-evaluation.html` | 法律 AI 私有化数据安全审计与等保测评实战:政法机关与大所怎么过审(202 | 法律AI数据安全审计、私有化AI等保测评、法律AI等保三级、政法数据安全、法律AI安全评估、私有化部署安全审计、法律AI等保过审、AI提示注入… |
| `/blog/legal-ai-hallucination-citation-verification.html` | 法律 AI 幻觉怎么治:裁判文书引证核验落地指南(2026)丨 文书查 | 法律 AI 幻觉、法律大模型 幻觉、裁判文书引证核验、法律 AI 引用核查、法律大模型 编造案例、法律 AI 可信、RAG 法律、类案检索 引用… |
| `/blog/legal-ai-inference-performance-gpu-utilization.html` | 律所私有化法律 AI 的推理性能优化与 GPU 利用率:并发、吞吐、显存与成 | 法律AI推理性能、私有化大模型GPU利用率、法律AI并发吞吐、vLLM 私有化部署、显存优化、KV cache、量化推理、法律AI响应延迟… |
| `/blog/legal-ai-model-version-management-upgrade.html` | 律所私有化法律 AI 的模型版本管理与升级实战:从换基座到不炸线上(2026 | 法律AI模型版本管理、私有化大模型升级、律所AI模型迭代、法律大模型灰度发布、模型回滚、法律AI效果回归测试、私有化模型基座更换、prompt与模型版本对齐… |
| `/blog/legal-ai-multi-tenant-permission-isolation.html` | 律所私有化法律 AI 的多租户与权限隔离架构:利益冲突墙 / 案件组 / 部 | 法律AI权限隔离、律所利益冲突墙、法律AI多租户、私有化AI权限控制、律所信息隔离墙、法律AI数据权限、政法AI部门隔离、法律AI访问控制… |
| `/blog/legal-ai-open-source-base-model-selection.html` | 律所私有化法律 AI 该选哪个大模型底座:DeepSeek / Qwen / | 法律AI大模型选型、律所私有化大模型、法律大模型底座、DeepSeek律所、Qwen法律AI、GLM法律、开源大模型选型、私有化部署大模型… |
| `/blog/legal-ai-private-deployment-disaster-recovery-ha.html` | 法律 AI 私有化灾备与高可用架构实战:政法机关与大所怎么保证不宕机(202 | 法律AI灾备、私有化AI高可用、法律AI高可用架构、政法AI容灾、法律AI RTO RPO、私有化部署容灾、法律AI不宕机、GPU高可用… |
| `/blog/legal-ai-private-deployment-monitoring-alerting.html` | 私有化法律 AI 上线后怎么运维:监控、告警与故障响应体系实战(2026)丨 | 私有化AI运维、法律AI监控告警、法律AI运维体系、私有化部署监控、法律AI故障响应、法律大模型运维、政法信息中心运维、法律AI SLA |
| `/blog/legal-ai-private-deployment-tco-three-year.html` | 法律 AI 私有化三年总拥有成本(TCO)测算:从 GPU 到运维的完整账本 | 法律AI TCO、私有化AI总拥有成本、律所AI三年成本、法律大模型部署成本、私有化AI预算测算、法律AI硬件成本、法律AI运维成本、私有化AI报价 |
| `/blog/legal-ai-rag-vs-finetune-technical-route.html` | RAG 还是微调?律所法律 AI 的技术路线怎么选(2026 决策指南)丨  | 法律AI RAG还是微调、律所大模型技术路线、法律大模型检索增强、RAG vs 微调、法律AI技术选型、律所AI检索增强、法律大模型微调、法律AI落地路线… |
| `/blog/legal-ai-startup-data-foundation.html` | 法律 AI 创业团队怎么选数据底座:自建爬库还是接授权库?(2026 创业  | 法律科技数据源、法律 AI 数据底座、法律大模型训练数据、裁判文书数据 API、法律 AI 创业、自建爬库 vs 授权库、法律 RAG 数据、法律科技选型… |
| `/blog/legal-ai-tender-technical-specifications.html` | 法律 AI 招投标技术参数怎么写:采购需求书实战模板(2026)丨 文书查 | 法律 AI 招投标、法律 AI 采购技术参数、法律大模型 招标参数、法院 AI 采购需求书、政府采购 法律 AI、法律 AI 技术规格书、法律 AI 招标文件、AI 采购参数怎么写… |
| `/blog/legal-ai-vector-database-retrieval-engine-selection.html` | 律所私有化法律 AI 的向量库与检索引擎怎么选:Milvus / Qdran | 法律AI向量库选型、私有化向量数据库、法律AI检索引擎、Milvus法律、Qdrant私有化、pgvector、Elasticsearch法律检索、混合检索… |
| `/blog/legal-ai-vendor-due-diligence.html` | 法律 AI 供应商怎么评估:私有化选型的厂商尽职调查清单(2026)丨 文书 | 法律AI供应商评估、法律AI厂商尽调、私有化AI供应商选择、法律AI供应商资质、法律科技供应商评估、法律AI厂商尽职调查、法律AI选型、法律AI数据来源合法性 |
| `/blog/legal-data-classification-grading.html` | 法律数据怎么分类分级:律所与政法机关 AI 落地前必做的合规底座(2026) | 法律数据分类分级、数据分类分级、司法数据分类分级、数据分级保护、法律AI数据合规、政法数据分类、数据安全法分类分级、律所数据分级… |
| `/blog/legal-data-platform-comparison-2026.html` | 文书查 vs 北大法宝 vs 无讼 vs Alpha:法律 AI 数据底座选 | 北大法宝替代、法律科技数据源、法律 AI 数据底座、法律数据库对比、北大法宝 无讼 对比、Alpha 案例库、裁判文书数据库选型、法律 AI 选型… |
| `/blog/legal-empirical-research-data-access.html` | 法学实证研究怎么拿到能用的裁判文书数据?(2026 高校研究者数据接入指南) | 法学实证研究数据、裁判文书数据集、实证法学、司法大数据研究、裁判文书 API、法律实证研究方法、量刑实证研究、法律文本计量… |
| `/blog/procuratorate-ai-case-pushing-indictment.html` | 检察院 AI 系统怎么落地:类案推送 + 起诉书辅助 + 量刑建议实战(20 | 检察院 AI 系统、检察 AI、智慧检务、类案推送 检察院、起诉书辅助生成、量刑建议辅助、认罪认罚量刑建议、检察智能辅助办案… |
| `/blog/similar-case-retrieval-semantic-vs-keyword.html` | 类案检索 API:语义向量 vs 关键词,到底哪种更准?(2026 法律 A | 类案检索 API、类案检索系统、语义检索 法律、向量检索 裁判文书、法律语义搜索、BM25 关键词检索、混合检索 RAG、法律 embedding… |
| `/blog/wenshucha-mcp-claude-desktop-setup.html` | 5 分钟把文书查接入 Claude Desktop:用 MCP 让 AI 直 | 文书查 MCP、Claude Desktop 法律、裁判文书 MCP、法律 MCP server、Claude 接入裁判文书、类案检索 MCP、法律 AI MCP、Cursor 法律… |
| `/blog/xinchuang-domestic-stack-legal-ai-deployment.html` | 信创环境下的法律 AI 私有化部署:国产 CPU / 操作系统 / 数据库  | 信创 法律 AI、法律 AI 国产化、信创适配、法律大模型 信创、麒麟操作系统 法律 AI、鲲鹏 飞腾 大模型、昇腾 法律大模型、达梦数据库 裁判文书… |
| `/buyers-guide/` | 文书查怎么收费_私有化部署要求_法律AI选型该问什么 - 采购决策指南 | 文书查怎么收费、裁判文书数据采购、法律AI私有化部署要求、法律AI选型、类案检索系统采购、法律大模型采购、司法数据采购、律所AI采购 |
| `/case-search/` | 裁判文书智能检索系统_类案检索_1.6 亿判决库多维筛选 - 文书查 | 裁判文书检索、类案检索、类案检索系统、判决书查询、裁判文书数据库、裁判文书全文检索、案例检索工具、法律检索系统… |
| `/data/` | 裁判文书数据_1.6 亿全量裁判文书数据库_API/MCP数据接口 - 文书 | 裁判文书数据、裁判文书数据库、裁判文书API、裁判文书数据接口、裁判文书全量数据、中国裁判文书网数据、1.6 亿裁判文书、裁判文书MCP… |
| `/data/labor-report/` | 全国劳动争议赔偿数据报告_80,000份判决实证_赔偿金额中位数15,200 | 劳动争议赔偿数据、劳动仲裁赔偿标准、经济补偿金数据、违法解除赔偿金、裁员赔偿多少钱、劳动争议判决统计、司法大数据报告、劳动争议大数据 |
| `/data/labor/beijing.html` | 北京劳动争议赔偿金额数据:3273份获赔判决的金额分布 丨 文书查 | 北京劳动争议赔偿、北京劳动仲裁赔偿标准、北京违法解除赔偿金、北京劳动争议赔偿多少钱、北京劳动争议判决数据 |
| `/data/labor/changchun.html` | 长春劳动争议赔偿金额数据:750份获赔判决的金额分布 丨 文书查 | 长春劳动争议赔偿、长春劳动仲裁赔偿标准、长春违法解除赔偿金、长春劳动争议赔偿多少钱、长春劳动争议判决数据 |
| `/data/labor/changsha.html` | 长沙劳动争议赔偿金额数据:1799份获赔判决的金额分布 丨 文书查 | 长沙劳动争议赔偿、长沙劳动仲裁赔偿标准、长沙违法解除赔偿金、长沙劳动争议赔偿多少钱、长沙劳动争议判决数据 |
| `/data/labor/chengdu.html` | 成都劳动争议赔偿金额数据:1187份获赔判决的金额分布 丨 文书查 | 成都劳动争议赔偿、成都劳动仲裁赔偿标准、成都违法解除赔偿金、成都劳动争议赔偿多少钱、成都劳动争议判决数据 |
| `/data/labor/chongqing.html` | 重庆劳动争议赔偿金额数据:3685份获赔判决的金额分布 丨 文书查 | 重庆劳动争议赔偿、重庆劳动仲裁赔偿标准、重庆违法解除赔偿金、重庆劳动争议赔偿多少钱、重庆劳动争议判决数据 |
| `/data/labor/dalian.html` | 大连劳动争议赔偿金额数据:771份获赔判决的金额分布 丨 文书查 | 大连劳动争议赔偿、大连劳动仲裁赔偿标准、大连违法解除赔偿金、大连劳动争议赔偿多少钱、大连劳动争议判决数据 |
| `/data/labor/dongguan.html` | 东莞劳动争议赔偿金额数据:855份获赔判决的金额分布 丨 文书查 | 东莞劳动争议赔偿、东莞劳动仲裁赔偿标准、东莞违法解除赔偿金、东莞劳动争议赔偿多少钱、东莞劳动争议判决数据 |
| `/data/labor/foshan.html` | 佛山劳动争议赔偿金额数据:564份获赔判决的金额分布 丨 文书查 | 佛山劳动争议赔偿、佛山劳动仲裁赔偿标准、佛山违法解除赔偿金、佛山劳动争议赔偿多少钱、佛山劳动争议判决数据 |
| `/data/labor/guangzhou.html` | 广州劳动争议赔偿金额数据:768份获赔判决的金额分布 丨 文书查 | 广州劳动争议赔偿、广州劳动仲裁赔偿标准、广州违法解除赔偿金、广州劳动争议赔偿多少钱、广州劳动争议判决数据 |
| `/data/labor/haerbin.html` | 哈尔滨劳动争议赔偿金额数据:308份获赔判决的金额分布 丨 文书查 | 哈尔滨劳动争议赔偿、哈尔滨劳动仲裁赔偿标准、哈尔滨违法解除赔偿金、哈尔滨劳动争议赔偿多少钱、哈尔滨劳动争议判决数据 |
| `/data/labor/haikou.html` | 海口劳动争议赔偿金额数据:546份获赔判决的金额分布 丨 文书查 | 海口劳动争议赔偿、海口劳动仲裁赔偿标准、海口违法解除赔偿金、海口劳动争议赔偿多少钱、海口劳动争议判决数据 |
| `/data/labor/hangzhou.html` | 杭州劳动争议赔偿金额数据:1385份获赔判决的金额分布 丨 文书查 | 杭州劳动争议赔偿、杭州劳动仲裁赔偿标准、杭州违法解除赔偿金、杭州劳动争议赔偿多少钱、杭州劳动争议判决数据 |
| `/data/labor/hefei.html` | 合肥劳动争议赔偿金额数据:885份获赔判决的金额分布 丨 文书查 | 合肥劳动争议赔偿、合肥劳动仲裁赔偿标准、合肥违法解除赔偿金、合肥劳动争议赔偿多少钱、合肥劳动争议判决数据 |
| `/data/labor/jiaozuo.html` | 焦作劳动争议赔偿金额数据:317份获赔判决的金额分布 丨 文书查 | 焦作劳动争议赔偿、焦作劳动仲裁赔偿标准、焦作违法解除赔偿金、焦作劳动争议赔偿多少钱、焦作劳动争议判决数据 |
| `/data/labor/jinan.html` | 济南劳动争议赔偿金额数据:661份获赔判决的金额分布 丨 文书查 | 济南劳动争议赔偿、济南劳动仲裁赔偿标准、济南违法解除赔偿金、济南劳动争议赔偿多少钱、济南劳动争议判决数据 |
| `/data/labor/jiutai.html` | 九台劳动争议赔偿金额数据:284份获赔判决的金额分布 丨 文书查 | 九台劳动争议赔偿、九台劳动仲裁赔偿标准、九台违法解除赔偿金、九台劳动争议赔偿多少钱、九台劳动争议判决数据 |
| `/data/labor/kunming.html` | 昆明劳动争议赔偿金额数据:572份获赔判决的金额分布 丨 文书查 | 昆明劳动争议赔偿、昆明劳动仲裁赔偿标准、昆明违法解除赔偿金、昆明劳动争议赔偿多少钱、昆明劳动争议判决数据 |
| `/data/labor/kunshan.html` | 昆山劳动争议赔偿金额数据:315份获赔判决的金额分布 丨 文书查 | 昆山劳动争议赔偿、昆山劳动仲裁赔偿标准、昆山违法解除赔偿金、昆山劳动争议赔偿多少钱、昆山劳动争议判决数据 |
| `/data/labor/liuzhou.html` | 柳州劳动争议赔偿金额数据:359份获赔判决的金额分布 丨 文书查 | 柳州劳动争议赔偿、柳州劳动仲裁赔偿标准、柳州违法解除赔偿金、柳州劳动争议赔偿多少钱、柳州劳动争议判决数据 |
| `/data/labor/luoyang.html` | 洛阳劳动争议赔偿金额数据:363份获赔判决的金额分布 丨 文书查 | 洛阳劳动争议赔偿、洛阳劳动仲裁赔偿标准、洛阳违法解除赔偿金、洛阳劳动争议赔偿多少钱、洛阳劳动争议判决数据 |
| `/data/labor/nanchang.html` | 南昌劳动争议赔偿金额数据:380份获赔判决的金额分布 丨 文书查 | 南昌劳动争议赔偿、南昌劳动仲裁赔偿标准、南昌违法解除赔偿金、南昌劳动争议赔偿多少钱、南昌劳动争议判决数据 |
| `/data/labor/nanjing.html` | 南京劳动争议赔偿金额数据:1095份获赔判决的金额分布 丨 文书查 | 南京劳动争议赔偿、南京劳动仲裁赔偿标准、南京违法解除赔偿金、南京劳动争议赔偿多少钱、南京劳动争议判决数据 |
| `/data/labor/nanning.html` | 南宁劳动争议赔偿金额数据:549份获赔判决的金额分布 丨 文书查 | 南宁劳动争议赔偿、南宁劳动仲裁赔偿标准、南宁违法解除赔偿金、南宁劳动争议赔偿多少钱、南宁劳动争议判决数据 |
| `/data/labor/ningbo.html` | 宁波劳动争议赔偿金额数据:595份获赔判决的金额分布 丨 文书查 | 宁波劳动争议赔偿、宁波劳动仲裁赔偿标准、宁波违法解除赔偿金、宁波劳动争议赔偿多少钱、宁波劳动争议判决数据 |
| `/data/labor/qingdao.html` | 青岛劳动争议赔偿金额数据:971份获赔判决的金额分布 丨 文书查 | 青岛劳动争议赔偿、青岛劳动仲裁赔偿标准、青岛违法解除赔偿金、青岛劳动争议赔偿多少钱、青岛劳动争议判决数据 |
| `/data/labor/shanghai.html` | 上海劳动争议赔偿金额数据:4480份获赔判决的金额分布 丨 文书查 | 上海劳动争议赔偿、上海劳动仲裁赔偿标准、上海违法解除赔偿金、上海劳动争议赔偿多少钱、上海劳动争议判决数据 |
| `/data/labor/shaoxing.html` | 绍兴劳动争议赔偿金额数据:542份获赔判决的金额分布 丨 文书查 | 绍兴劳动争议赔偿、绍兴劳动仲裁赔偿标准、绍兴违法解除赔偿金、绍兴劳动争议赔偿多少钱、绍兴劳动争议判决数据 |
| `/data/labor/shenyang.html` | 沈阳劳动争议赔偿金额数据:1982份获赔判决的金额分布 丨 文书查 | 沈阳劳动争议赔偿、沈阳劳动仲裁赔偿标准、沈阳违法解除赔偿金、沈阳劳动争议赔偿多少钱、沈阳劳动争议判决数据 |
| `/data/labor/shenzhen.html` | 深圳劳动争议赔偿金额数据:1311份获赔判决的金额分布 丨 文书查 | 深圳劳动争议赔偿、深圳劳动仲裁赔偿标准、深圳违法解除赔偿金、深圳劳动争议赔偿多少钱、深圳劳动争议判决数据 |
| `/data/labor/suzhou.html` | 苏州劳动争议赔偿金额数据:554份获赔判决的金额分布 丨 文书查 | 苏州劳动争议赔偿、苏州劳动仲裁赔偿标准、苏州违法解除赔偿金、苏州劳动争议赔偿多少钱、苏州劳动争议判决数据 |
| `/data/labor/tangshan.html` | 唐山劳动争议赔偿金额数据:323份获赔判决的金额分布 丨 文书查 | 唐山劳动争议赔偿、唐山劳动仲裁赔偿标准、唐山违法解除赔偿金、唐山劳动争议赔偿多少钱、唐山劳动争议判决数据 |
| `/data/labor/tianjin.html` | 天津劳动争议赔偿金额数据:2325份获赔判决的金额分布 丨 文书查 | 天津劳动争议赔偿、天津劳动仲裁赔偿标准、天津违法解除赔偿金、天津劳动争议赔偿多少钱、天津劳动争议判决数据 |
| `/data/labor/wenzhou.html` | 温州劳动争议赔偿金额数据:357份获赔判决的金额分布 丨 文书查 | 温州劳动争议赔偿、温州劳动仲裁赔偿标准、温州违法解除赔偿金、温州劳动争议赔偿多少钱、温州劳动争议判决数据 |
| `/data/labor/wuhan.html` | 武汉劳动争议赔偿金额数据:2245份获赔判决的金额分布 丨 文书查 | 武汉劳动争议赔偿、武汉劳动仲裁赔偿标准、武汉违法解除赔偿金、武汉劳动争议赔偿多少钱、武汉劳动争议判决数据 |
| `/data/labor/xiamen.html` | 厦门劳动争议赔偿金额数据:704份获赔判决的金额分布 丨 文书查 | 厦门劳动争议赔偿、厦门劳动仲裁赔偿标准、厦门违法解除赔偿金、厦门劳动争议赔偿多少钱、厦门劳动争议判决数据 |
| `/data/labor/xian.html` | 西安劳动争议赔偿金额数据:1799份获赔判决的金额分布 丨 文书查 | 西安劳动争议赔偿、西安劳动仲裁赔偿标准、西安违法解除赔偿金、西安劳动争议赔偿多少钱、西安劳动争议判决数据 |
| `/data/labor/xinjiangwulumuqi.html` | 新疆乌鲁木齐劳动争议赔偿金额数据:639份获赔判决的金额分布 丨 文书查 | 新疆乌鲁木齐劳动争议赔偿、新疆乌鲁木齐劳动仲裁赔偿标准、新疆乌鲁木齐违法解除赔偿金、新疆乌鲁木齐劳动争议赔偿多少钱、新疆乌鲁木齐劳动争议判决数据 |
| `/data/labor/yantai.html` | 烟台劳动争议赔偿金额数据:302份获赔判决的金额分布 丨 文书查 | 烟台劳动争议赔偿、烟台劳动仲裁赔偿标准、烟台违法解除赔偿金、烟台劳动争议赔偿多少钱、烟台劳动争议判决数据 |
| `/data/labor/zhengzhou.html` | 郑州劳动争议赔偿金额数据:862份获赔判决的金额分布 丨 文书查 | 郑州劳动争议赔偿、郑州劳动仲裁赔偿标准、郑州违法解除赔偿金、郑州劳动争议赔偿多少钱、郑州劳动争议判决数据 |
| `/data/labor/zhongshan.html` | 中山劳动争议赔偿金额数据:284份获赔判决的金额分布 丨 文书查 | 中山劳动争议赔偿、中山劳动仲裁赔偿标准、中山违法解除赔偿金、中山劳动争议赔偿多少钱、中山劳动争议判决数据 |
| `/` | 文书查 - 裁判文书智能检索 + AI 法律助手 丨 1.6 亿判决库免费试 | 裁判文书检索、类案检索、裁判文书数据库、判决书查询、法律AI助手、AI法律问答、AI合同审查、AI文书起草… |
| `/legal-ai/` | AI法律助手_法律问答/文书起草/合同审查/智能阅卷_每天免费8次 - 文书 | AI法律助手、法律AI、AI法律问答、AI合同审查、合同审查AI、AI文书起草、起诉状生成、智能阅卷… |
