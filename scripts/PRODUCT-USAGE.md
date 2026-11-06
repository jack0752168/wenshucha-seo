# 內部產品使用看板

入口：本機 `reports/internal/product-usage/index.html`；雲端 `state/private/product-usage/index.html`。這是私有靜態檔，不部署到網站，不提供公網管理後台。

本機更新：`python3 scripts/product_usage_dashboard.py`。雲端每日 09:00 的既有 `daily_run.sh` 會更新私有檔案；`bash scripts/daily_run.sh --usage-dashboard-only` 只跑相同統計函式，不執行發布、推送、網站更新或通知。既有 Codex 每日任務產生本機副本，頻率及模型不變。

研究以 SQLite `mode=ro`、`query_only` 交易快照讀取有界資料，沒有模型呼叫或寫入客戶資料。帳號使用隨機原始 ID 的穩定雜湊代號；不輸出郵箱、原始 ID、問題、文書、密碼或 Key。保留測試域排除，資料庫未提供帳號級 self/bot 標記，所以無法宣稱其餘帳號均為真人。MCP 僅使用既有 CTA 及機構申請回執，原生 Key 用量、收款未接入時是 unknown。

今天／近7天／近30天以新加坡午夜起算；任務按發起日期及目前狀態分類，沒有完成時間的歷史不能改寫成當日完成事件。退回的是研究名額，非現金。7日跨日回訪只以成熟帳號計算；未成熟或無帳號不報0%留存。網站匿名訪次、含 QA 的方案／聯絡操作、人工授權和已核實收款分層，不當作完整跨站轉化率或 GEO 歸因。

每次產生唯一日期 JSON／CSV／Markdown 快照。部分來源失敗則該部分標 stale，保留最後成功時間與原窗口；從未成功則 unknown。舊快照不覆寫，`last-good.json` 只更新成功的部分。`--input` 是合成／離線回放，使用不同模式，不從正式快照補值；使用獨立輸出目錄。檔案600、目錄700。不得將這些資料複製到公開網站或日報 relay。

測試：`python3 -m unittest discover -s scripts -p test_product_usage.py -v`。合成資料僅在暫存目錄，從不建立正式客戶或模型研究。瀏覽器視覺驗收與程式測試分開記錄，受阻不等於通過。
