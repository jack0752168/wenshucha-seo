# 已關閉群入口與手機同步驗收 · 2026-11-25

## 根因與改動

客戶回報屬實：主站/pricing/仍有群QR、拉群fallback和加入送一年，tob的UpgradeCard、QuotaPaywallCard、AI頁隱藏展開卡、正文提示、quota/purchase回傳與無效邀請說明也殘留群引導。此前僅清主站其他產品入口，未掃完互動/錯誤分支。

主站047e757已正式部署與版本戳核對；tob源dd0faaf、BUILD_ID yngbCJO1jY8fyNaR0SINh已本地正式build，在同機3037暫存啟動驗收後切換production。沿既有Linux runtime及env；production env逐byte一致，原客戶權限、配額、有效內測Cookie與付款鏈路不改。共用BusinessContact取代三處群碼；API只回聯絡方式，wechatQr=null。原/root與/www已備份，可回退到/www/wwwroot/peilema.before-no-group-20261125。

舊主站/img/neice-qr.jpg與tob/neice-qr.jpg皆410。tob的location片段必放在/www/server/panel/vhost/rewrite/wsc-retired-group.conf，由HTTP/HTTPS server個別include；不要放nginx/*.conf頂層，那裡會被全域glob include而報location不合法。live vhost備份peilema_next.conf.bak-20261125-no-group；真源片段在site ops/nginx/retired-group.conf。nginx -t通過、服務active，臨時驗證服務已停止。舊runtime備份及舊hash static保留，避免在途客戶chunk失效。

## 驗證

主站167頁linkcheck通過；型別、變更檔eslint和正式build通過。新增實際點擊展開聯絡的兩項UI回歸測試+AI quota既有20項=22/22；另shared-quota舊套件18/20，兩項原先已與HEAD不符（今日體驗文案與NEICE cap字串），未擅改計量或舊測試來刷綠。

公開定價與AI HTTP200、兩群碼410、purchase只回聯絡200且不建立訂單。定價公開SHA吻合。瀏覽器QA實走檢索一次→正文頁→聯絡卡展開→主站business-wechat，320/375/1280都無橫向溢出、無群文案或群圖；AI正常頁同尺寸通過，不為觸發用量牆消耗付費AI。隱藏quota分支由UI測試覆蓋，不宣稱實際耗盡生產額度。

## 長期規則

Jack明確要求每次網站變更手機同步。已在允許的記憶更新目錄新增小型note（未改記憶主檔），並將驗收規則寫入site ops/MOBILE-VERIFICATION.md與SEO PRODUCT-FOCUS最新置頂，現有自動任務沿既有必讀文件取得。關閉的群承接不恢復，驗可見頁、隱藏卡、fallback/API/生成源，以及手機按鈕完整目的地。未新增排程或對外通知。
