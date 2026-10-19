# Bing 站长工具周读数（整域 wenshucha.com，含 www / tob / mcp / sinoverdict）

> 由排程 `shenma-weekly-readout` 每周一**追加**（不许覆盖旧行）。日期列＝该周周一。Jack 2026-09-17 在 Chrome 用 Google 账号登录。
> 只列展现 ≥5 的词；平均排名是 Bing 自报，判首页以乾淨真搜为准。Bing 数据约滞后 2 天，「近7天」实际覆盖到读数日前两天。
> ⚠️ 09-14 那两行是 09-17 手动读的（近 7 天≈09-08~09-15），09-21 那两行是排程读的；09-21 排程曾把本文件当新文件覆盖，09-21 主 session 已从 git 合并回来。

| 日期 | 口径 | 点击 | 展现 | CTR | 备注 |
|---|---|---|---|---|---|
| 2026-09-14 | 近3月 | 330 | 5,300 | 6.18% | 首周基线，09-17 主 session 手动读。日展现从 6 月的 10 左右涨到 9 月中的 130-270。AI Performance 报表为空 |
| 2026-09-14 | 近7天 | 41 | 991 | 4.14% | 首周基线 |
| 2026-09-21 | 近3月 | 354 | 5.9K | 5.96% | 第二周（排程写成「首周基线」，已更正）。AI Performance（近3月）Total Citations 462，Avg. Cited Pages 2 |
| 2026-09-21 | 近7天 | 51 | 1.1K | 4.53% | 第二周。按天覆盖 09-14~09-19：点击 9/11/9/18/3/1，展现 271/222/226/193/88/127（09-18 起明显下滑） |
| 2026-10-12 | 近3月 | 466 | 11,870 | 3.93% | All；成熟07/12～10/10；AI引用686，非實驗page口徑 |
| 2026-10-12 | 近7天 | 55 | 3,198 | 1.72% | All；10/05～10六個成熟日，10/11未知；上週帳缺失 |

## 2026-10-19 週 · 正式讀數（部分完成）

- 動態瀏覽器清單兩次只提供Chrome extension，獨立SSH／Mac mini報表後最後重查仍無type=iab，記 iab_unavailable_route，不是Chrome BUSY、登入失效或平台空表。Bing依最新專用IAB規則，未改走Chrome、硬編碼id、改Cookie或建立重複頁。
- 本輪近3月／近7天整域總數、Web關鍵詞前10／Pages前10／AI引用均未新讀，無新CSV；無法報整域週比或新增優化詞。今早10:05:36 SGT由daily-seo-optimize核驗的既有真CSV保留：Web「裁判文书」→/cases，成熟2026-10-11～17，2482曝光／3點擊／CTR0.1208702659%／均位7.5028185737；這是既有query-page快照，不冒充本輪整域週報。
- 已執行unavailable --reason data_unavailable --sync-server，保留最新真值；本輪唯讀JSON核驗本機／既有server完全一致。原30D基準2988/9與14完整成熟post候選10/14～27保持，不判效果。
- Mac mini funnel唯讀成功：SGT昨日10/18完整日47進站訪次→12成功檢索→3展開正文；研究實收0、MCP實收0，聯絡點擊1不是提交，訪次不是人數。traffic helper依既定規則blocked_unverified，昨日兩站來源未知，未本機重跑長查詢；Bing worker只分析既有快照。Mac通知器loaded／LastExitStatus0不等於本輪新通知送達。
- 證據：`/Users/chenjiaxin/.codex/automations/10-40-bing/runs/2026-10-19`。本週未新增完成表格行，保留原合法補跑；title/description/H1未改。


## 2026-10-12 週 · 隱藏 IAB 補讀完成

- 3 M、7 D均明確點選並等loading結束。All近3月466點擊／11,870曝光／CTR3.93%，成熟日期07/12～10/10；All近7天55／3,198／1.72%，選取10/05～11但**實際只有10/05～10六個成熟日**，10/11未知不補0。上週10/05帳缺失，不能報週環比。
- 近7天Web裝置表：Desktop約3.1K曝光／50點擊／CTR1.60%／均位7.41；Mobile68／5／7.35%／5.47。是整域裝置，不代替同頁同詞的裝置交叉資料。Web and Chat總覽均位6.6，亦不是實驗page均位。
- 近7天曝光≥5只有9詞。候選：裁判文书約1.6K／7／均位6.49；类案检索14／3／5.64；司法裁判文书网11／0／9.55。K是平台約值，均位不是乾淨真搜首頁證明。
- AI Performance明確3 M載入：Total Citations686、Avg. Cited Pages2，引用不是進站或需求。
- 固定CTR實驗：30D→Web Keywords「裁判文书」→Served pages CSV，/cases仍**2988曝光／9點擊／CTR精算0.3012%／均位6.6948**；09/12～10/10成熟資料，與基準相同。query3232／10不能代替page，全部是改版前資料。
- Bing Index「Last crawl attempted Today at 09:00」未標時區；View Indexed page仍是舊title「类案检索 · 近 1.6 亿裁判文书全文检索 | 文书查」，未見新title。記not_yet_exposed；等待新版本重抓確認後取14個完整成熟日，延遲順延，10/13～26暫定窗不能直接當已曝光觀察窗。同頁同query逐日／裝置交叉未取得，unknown；已保存query逐日與page聚合CSV，兩者不互換。
- 昨日SGT10/11漏斗unmeasured，counts/rates=null；10/12首日partial截至取數，排除QA／自訪／已知爬蟲後進站→成功檢索→展開庫內正文→服務端實收需求均0、部分正文另列0。不能當歷史零轉化或優化效果；聯絡點擊不是提交，提交不是付費。
- 原traffic_report已讀：昨日www21PV／19獨立IP，tob31PV／28獨立IP，不是人數或歷史漏斗。Mac com.jack.mcp-apply-notify已載入、LastExitStatus=0；研究需求dry預檢待通知0。落庫QA沿用10/12已有隔離驗收，未重送假需求；沒有新實際通知可驗，SMTP accepted不當送達。
- title/description/H1沒有修改，未提交索引或改平台設定。本週10/12名譽權已1學術頁，下輪10/15，本任務沒有增空頁。上午未完成段保留歷史。
- 證據：`/Users/chenjiaxin/.codex/automations/10-40-bing/runs/2026-10-12/retry-1540/`；原traffic在上層traffic-retry.json。

### 近7天 Web 關鍵詞（曝光≥5）

| 詞／URL | 曝光 | 點擊 | CTR | 均位 |
|---|---|---|---|---|
| 裁判文书 | 1.6K | 7 | 0.44% | 6.49 |
| 文书查 | 15 | 3 | 20.00% | 3.93 |
| 类案检索 | 14 | 3 | 21.43% | 5.64 |
| 司法裁判文书网 | 11 | 0 | 0.00% | 9.55 |
| 文书网判决书 | 11 | 0 | 0.00% | 9.36 |
| 裁判文书万 | 7 | 0 | 0.00% | 7.71 |
| 裁判文书网 mcp, github | 6 | 0 | 0.00% | 6.33 |
| 裁判文书往 | 6 | 0 | 0.00% | 7.33 |
| 裁判文书我 | 5 | 0 | 0.00% | 5.60 |

### 近7天 Web 頁面前10

| 詞／URL | 曝光 | 點擊 | CTR | 均位 |
|---|---|---|---|---|
| https://tob.wenshucha.com/cases | 2.6K | 30 | 1.15% | 6.53 |
| https://www.wenshucha.com/data/ | 117 | 7 | 5.98% | 7.87 |
| https://www.wenshucha.com/case-search/ | 66 | 0 | 0.00% | 7.35 |
| https://www.wenshucha.com/ | 42 | 2 | 4.76% | 14.71 |
| https://mcp.wenshucha.com/ | 15 | 1 | 6.67% | 5.27 |
| https://www.wenshucha.com/blog/court-ai-trial-assistance-sentencing-document.html | 15 | 2 | 13.33% | 4.20 |
| https://www.wenshucha.com/data/labor-report/ | 6 | 0 | 0.00% | 4.33 |
| https://www.wenshucha.com/blog/evidence-list-proof-checklist-litigation.html | 4 | 0 | 0.00% | 6.50 |
| https://www.wenshucha.com/blog/similar-case-search-completeness-guide.html | 4 | 0 | 0.00% | 4.50 |
| https://www.wenshucha.com/blog/legal-data-platform-comparison-2026.html | 4 | 0 | 0.00% | 6.25 |


## 2026-10-12 週 · 正式讀數（未完成）

- 取得 browser-lane 锁后，Codex CUA 的 IAB 分页查询与明确 `visible:false` 的建页调用均返回 **Browser is not available: iab**，记 `background_unavailable / iab_unavailable`。没有进入 Bing 页面，不能判定会话失效；没有改走 Chrome 或抽 Cookie，锁已释放。
- 近 3 月／7 D 的点击、展现、CTR、关键词前 10、Pages 前 10、AI Performance 均**未读到**。2026-10-10 登录稽核的 24 点击／1.4K 展现不属于本轮读数，不回填。
- 2026-10-05 平台周账未完成，本轮无法比较上周，也无法提供新的展现 ≥5、平均排名 4–10 的优化词。
- 保留全部历史表格与明细；只新增本段缺项记录，未新增 `| 2026-10-12 |` 完成行，待隐藏 IAB 恢复后补读。证据：`/Users/chenjiaxin/.codex/automations/10-40-bing/runs/2026-10-12/run.json`。

## 2026-10-05 週 · 2026-10-08 正式補跑（部分完成）

- 批次：`20261008T031832Z / shenma-weekly-readout`。11:58（UTC+8）取得瀏覽器全域鎖後，核驗 Chrome 沒有 `bing.com/webmasters` 的既有分頁；依原任務停止 Bing 後台讀取，鎖已釋放，未另建分頁、修改設定或提交資料。
- 近 3 月／近 7 天的 Total Clicks、Total Impressions、CTR 均**未讀到**；關鍵詞前 10、Pages 前 10、AI Performance 亦未讀取。沒有使用歷史數字回填，不把缺資料寫成 0。
- 需要 Jack 在 Chrome 開啟一次 `https://www.bing.com/webmasters/searchperf?siteUrl=https://wenshucha.com/`；若提示登入，點 Sign in → Google。本次缺分頁，**尚未判定會話是否失效**。
- 2026-09-28 週帳缺失，最新既有紀錄仍是 09-21。本輪無新讀數，無法計算與上週比較，也無法提供符合展現 ≥5、排名 4–10 的新優化詞。
- 保留全部歷史表格與明細；本輪只在明細區最前面插入缺項記錄，**未新增 `| 2026-10-05 |` 的完成表格行**，避免原任務的週去重把後續補讀擋住。瀏覽器缺項證據見本批任務目錄 `browser-check.json`。

## 2026-09-21 近7天关键词（展现 ≥5，共 9 个；53 个词中其余均 <5）
| 关键词 | 展现 | 点击 | CTR | 平均排名 |
|---|---|---|---|---|
| 裁判文书 | 422 | 0 | 0.00% | 8.91 |
| 文书查 | 34 | 11 | 32.35% | 2.76 |
| https://www.wenshucha.com[reference:0]（AI 生成的串，非真人词） | 24 | 1 | 4.17% | 5.13 |
| 文书查 / sinoverdict mcp server | 12 | 0 | 0.00% | 7.17 |
| 裁判文书检索工具 免费 | 8 | 2 | 25.00% | 4.00 |
| 查文书api | 8 | 1 | 12.50% | 2.50 |
| 裁判文书-法律文书数据下载仓库 | 6 | 1 | 16.67% | 7.00 |
| 裁判文书数据 | 6 | 1 | 16.67% | 8.00 |
| 类案检索报告 | 5 | 0 | 0.00% | 7.60 |

## 2026-09-21 近7天页面（展现前 10）
| URL | 展现 | 点击 | 平均排名 |
|---|---|---|---|
| https://tob.wenshucha.com/cases | 622 | 8 | 7.75 |
| https://www.wenshucha.com/case-search/ | 78 | 1 | 6.60 |
| https://www.wenshucha.com/data/ | 63 | 9 | 8.62 |
| https://mcp.wenshucha.com/ | 27 | 7 | 3.70 |
| https://www.wenshucha.com/ | 14 | 6 | 4.00 |
| /blog/similar-case-search-report-writing-guide.html | 11 | 0 | 6.00 |
| /blog/court-ai-trial-assistance-sentencing-document.html | 11 | 3 | 4.73 |
| /blog/case-filing-cause-of-action-jurisdiction.html | 4 | 1 | 4.75 |
| /blog/law-firm-private-ai-deployment-guide.html | 4 | 3 | 1.00 |
| /blog/legal-brief-argument-similar-case-citation.html | 3 | 0 | 9.00 |

（近3月页面前几：tob/cases 2.0K/60 点击/7.16；www/data 404/40/6.54；www/case-search 401/13/6.83；mcp 296/85/3.40；blog/property-preservation 168/0/4.24）

### 2026-09-14 周 · 近 7 天关键词（展现 ≥5）
| 词 | 展现 | 点击 | CTR | 平均排名 |
|---|---|---|---|---|
| 裁判文书 | 371 | 0 | 0% | 9.03 |
| https://www.wenshucha.com[reference:0]（疑为 AI 对话引用串） | 24 | 1 | 4.17% | 5.13 |
| 文书查 / sinoverdict mcp server | 12 | 0 | 0% | 7.17 |
| 文书查ai | 8 | 1 | 12.5% | 3.25 |
| 裁判文书检索工具 免费 | 8 | 2 | 25% | 4.00 |
| 判决文书api | 8 | 1 | 12.5% | 3.25 |
| 裁判文书数据 | 6 | 1 | 16.67% | 8.00 |

### 2026-09-14 周 · 近 3 月页面前 10（按展现）
| 页面 | 展现 | 点击 | 平均排名 |
|---|---|---|---|
| https://tob.wenshucha.com/cases | 1,600 | 58 | 7.10 |
| https://www.wenshucha.com/data/ | 363 | 34 | 6.59 |
| https://www.wenshucha.com/case-search/ | 354 | 13 | 6.84 |
| https://mcp.wenshucha.com/ | 289 | 86 | 3.34 |
| https://www.wenshucha.com/blog/property-preservation-litigation-guide.html | 166 | 0 | 4.23 |
| https://www.wenshucha.com/ | 125 | 19 | 6.06 |
| https://wenshucha.com/blog/judgment-api-integration-python-nodejs.html | 66 | 14 | 4.20 |
| https://wenshucha.com/blog/court-ai-trial-assistance-sentencing-document.html | 47 | 5 | 4.89 |
| https://www.wenshucha.com/blog/law-firm-private-ai-deployment-guide.html | 45 | 12 | 3.78 |
| https://wenshucha.com/blog/court-similar-case-recommendation-system.html | 40 | 7 | 4.05 |

**读法**：「裁判文书」一周 371 次展现、排 9、零点击，是 Bing 上最大的一块空间；落地页多半是 tob `/cases`（近 3 月 1,600 展现、排 7.1）。挤进前 5 才会有点击。
