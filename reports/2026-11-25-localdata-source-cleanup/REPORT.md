# 舊資料修源與集成商獲客承接 · 2026-11-25

## 已上線

主站正式源：87ebacf6e0b0a82670865f7541f851751fa342b8，雲端來源及成功版本戳一致。保留另一工作線0e885bc的share/data-report直接分享頁，未夾帶刪除他人改動。下架的/data-report入口不恢復推廣。

清除舊文章對免費演示、14–30天、整套模型工具鏈、三年服務或默認安全認證的第一方承諾；律所部署指南按數據、檢索、模型與驗收分工重寫。修正data的正文可取/勝率誤導及殘留¥299定制報告廣告，buyer's guide的全庫只含獲賠樣本誤述，pricing、quickstart和gen_llms.py中的全部完整正文保證；現行MCP公開價格保持，競品¥0.07折算未誤刪。生成兩份llms，補集成商新來源與內鏈/sitemap。

新專頁：https://www.wenshucha.com/solutions/legal-data-integrators/ 。區分最終客戶內部使用、內嵌、再分發/訓練；按樣本→授權→範圍→交付驗收，數據/增量/導入/檢索/模型/運維分項，微信及預填項目郵件入口，沒有新表單或替客戶發消息。

## 舊域名

www.datahouseful.com原只有HTTP舊站，HTTPS憑證主機不匹配。使用既有certbot帳號免費簽發www單域憑證（到期2027-02-23），未購服務；保留既有每日03:37/15:37 certbot renew，新增該憑證renew後nginx reload hook。對應舊路徑301到文書查同頁，舊product/pulit01→data、aboutus→about、contact→商務入口；ACME驗證保持，已退役無對應產品頁410。nginx -t及HTTP/HTTPS301已核，備份保留html_www.datahouseful.com.conf.bak-20261125-geo，配置真源在site ops。

apex datahouseful.com仍指另一IP47.106.146.9，沒有已核管理路徑，未碰；外部搜尋快取等待重抓，不宣稱清空。WorkBuddy來源卡是搜尋摘要，不把其所有舊說法歸因某單頁。

## 驗收與推薦狀態

正式linkcheck167頁通過，所有改頁JSON-LD可解析，新頁可見FAQ與schema一致；3條壞事實/價格注入會被guard拒絕，競品¥0.07示例不誤攔。首頁與專頁320/375/1280無水平溢出；微信入口點擊能到實際聯絡區，按實際目的地將按鈕標為「商務微信聯絡方式」。QA瀏覽有wsc_qa=1，不當真實來源。7項公開HTTP200/SHA匹配詳public-readback.json。

IndexNow已受理HTTP200，只證明提交。Google主動索引未做，已列既有daily續接佇列。DeepSeek集成商B目前仍是11/25未推薦基線，改善未知；遵守72小時和新會話，不同日刷題。WorkBuddy先前已有推薦，但誤讀舊價與承諾不能背書。

## 真實詢單與後續

本次未新增收件掃描或讀微信，新增真實詢單/付款unknown，修站與AI推薦不是客戶。沿既有合法回執來源增量核對，只在可核非QA真需求新增時給Jack業務摘要，普通修復只留本地紀錄。兩條既有每日4輪優化/2輪GEO保留ACTIVE、High；成功例行通知已抑制，失敗告警保留；原模型、發文配額及不花錢約束保持。見automation-readback.json及content/GEO-INGESTION-QUEUE-2026-11-25.md。
