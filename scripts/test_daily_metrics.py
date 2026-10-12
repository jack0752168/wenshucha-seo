#!/usr/bin/env python3
"""Regression checks for freshness, source windows and durable receipt counts."""
import datetime as dt
import tempfile
import unittest
from pathlib import Path
import bing_report as bing
import funnel_report as funnel
import traffic_report as traffic
import build_daily_narrative as narrative

NOW = dt.datetime(2026,10,12,8,tzinfo=dt.timezone.utc)
def reading():
    return {'site':'https://wenshucha.com/','scope':'query_served_page_web','query':'裁判文书','url':bing.TARGET,'observed_at':'2026-10-12T06:52:58Z','date_start':'2026-09-12','date_end':'2026-10-10','impressions':2988,'clicks':9,'source':'bing_webmaster_csv','evidence':'qa-fixture.csv'}

class DailyMetrics(unittest.TestCase):
    def test_ctr_is_ratio_of_counts(self):
        self.assertAlmostEqual(bing.validate(reading(),NOW)['ctr'],9/2988)
    def test_no_impressions_is_undefined_not_zero_ctr(self):
        r=reading();r.update(impressions=0,clicks=0)
        self.assertIsNone(bing.validate(r,NOW)['ctr'])
    def test_bad_scope_future_date_and_fake_counts_rejected(self):
        for changes in [{'scope':'all_total'},{'date_end':'2026-10-12'},{'clicks':True},{'clicks':4000},{'observed_at':'2026-10-12T10:00:00Z'}]:
            r=reading();r.update(changes)
            with self.assertRaises(ValueError):bing.validate(r,NOW)
    def test_failed_read_retains_known_value_and_marks_unknown(self):
        original=bing.STATE
        try:
            with tempfile.TemporaryDirectory() as t:
                bing.STATE=Path(t)/'bing.json';bing.update(reading());state=bing.update(reason='login_required')
                text=bing.report(state,NOW)
                self.assertIn('0.30%',text);self.assertIn('讀取受阻',text);self.assertIn('不冒充',text)
                self.assertEqual(bing.STATE.stat().st_mode&0o777,0o600)
        finally:bing.STATE=original
    def test_stale_missing_and_window_are_explicit(self):
        self.assertIn('未知',bing.report({},NOW))
        r=reading();r['observed_at']='2026-10-10T06:00:00Z';r['date_end']='2026-10-09'
        text=bing.report({'latest':r},NOW)
        self.assertIn('未更新',text);self.assertIn('非昨日單日或全站',text)
    def test_daily_sources_do_not_use_cumulative_fallback(self):
        self.assertIn('未取得',traffic.daily_source_line('昨日',None))
        line=traffic.daily_source_line('昨日',{'sources':{'Bing':3,'直接／來源不明':7}})
        self.assertIn('Bing 3（30%）',line);self.assertIn('來源不明',line)
    def test_receipts_are_deduped_exclude_qa_self_bots_and_need_not_follow_search(self):
        r={'id':'real','kind':'report','received_at':'2026-10-11T01:00:00Z','funnel':None}
        data={'meta':{'started_at':'2026-10-10T01:00:00Z'},'events':[],'receipts':[r,r,{**r,'id':'qa','funnel':{'qa':True}},{**r,'id':'self','self':True},{**r,'id':'bot','bot':True}]}
        c=funnel.summarize(data,dt.date(2026,10,11))['counts']
        self.assertEqual(c['report_demand_receipts'],1);self.assertEqual(c['search_to_read_to_lead_sessions'],0)
    def test_all_metrics_pass_through_existing_daily_report(self):
        text=bing.report({'latest':reading()},NOW)+'\n*📨 昨日實際提交需求:* 合計 1 筆\n'
        result=narrative.parse_input('=== TRAFFIC ===\n'+text+'=== INDEXNOW ===\n')
        self.assertTrue(any('Bing 點擊率' in line for line in result['traffic']))
        self.assertTrue(any('合計 1 筆' in line for line in result['traffic']))

if __name__=='__main__':unittest.main()
