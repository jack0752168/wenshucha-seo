# wenshucha-seo · 文書查/SinoVerdict SEO 自動化體系

跟 `wenshucha-monitor`(健康監控)同源不重疊,專門做 SEO 自動化工作。

跑在 Jack 已付費的 Lighthouse 上(0 額外費用),每 15 分鐘從 GitHub raw 拉同步 + 按時跑任務。

## 三個站點

| 域名 | 部署 | 受眾 |
|---|---|---|
| https://wenshucha.com | Lighthouse + 宝塔(廣州) | 國內律師/政府/高校 |
| https://sinoverdict.wenshucha.com | Vercel(全球 CDN) | 海外律所 |
| https://mcp.wenshucha.com | Vercel(中文 cn.html) | 海外華人開發者 |

## 目錄

```
wenshucha-seo/
├── config.yml              # 站點 + 待推 URL + sitemap 路徑
├── scripts/
│   ├── push_indexnow.py    # IndexNow → Bing/Yandex(免 token,自動)
│   ├── push_baidu.py       # 百度主動推送(需 Jack 註冊站長平台拿 token,stub)
│   ├── push_google.py      # Google Indexing API(需 service account,stub)
│   ├── ssl_monitor.py      # 每日 SSL 到期檢查 < 30 天告警
│   ├── check_indexed.py    # 每週 site: 查詢看收錄量
│   ├── generate_weekly_report.py  # 週報 → 微信
│   ├── daily_run.sh        # 每日 09:00 編排
│   └── weekly_run.sh       # 每週一 10:00 編排
├── content/
│   ├── topic_pool.md       # SEO 長文主題池(30 題起步)
│   └── plan.md             # 內容生產節奏 / 關鍵詞地圖
├── reports/weekly/         # 歷史週報歸檔
├── public/                 # IndexNow key 等需放到站點根目錄的檔
└── logs/                   # cron 跑日誌
```

## Lighthouse cron 部署

```cron
# wenshucha-seo 自動拉 GitHub 同步(每 15 分钟)
*/15 * * * * cd /opt/wenshucha-seo && git pull origin main --quiet

# 每日 09:00:IndexNow 推送 + SSL 監控
0 9 * * * cd /opt/wenshucha-seo && bash scripts/daily_run.sh >> logs/daily.log 2>&1

# 每週一 10:00:收錄量檢查 + 週報生成 + 微信推送
0 10 * * 1 cd /opt/wenshucha-seo && bash scripts/weekly_run.sh >> logs/weekly.log 2>&1
```

## 三個 Tier

- **Tier 1(已實現,完全免費)**:IndexNow / SSL 監控 / 主題池
- **Tier 2(需要 Jack 一次性配合)**:5 家站長平台註冊 → 拿 token → 回填 → 啟用百度/Google 推送
- **Tier 3(內容自動化)**:每週 AI 寫 1-2 篇 SEO 長文,push wenshucha-site 自動上線
