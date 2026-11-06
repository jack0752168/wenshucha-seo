#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthetic analytics fixtures; never create real studies or customer accounts."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import product_usage_source as src
import product_usage_dashboard as dash

NOW=src.epoch('2026-11-06T04:00:00Z')
DAY=86400000


class UsageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.db=self.root/'research.sqlite'
        db=sqlite3.connect(self.db)
        db.executescript('''
        CREATE TABLE users(id TEXT PRIMARY KEY,email TEXT,org TEXT,password TEXT);
        CREATE TABLE tasks(id TEXT PRIMARY KEY,user TEXT,status TEXT,created INTEGER,question TEXT);
        CREATE TABLE followups(user TEXT,created INTEGER);
        CREATE TABLE activity(user TEXT,kind TEXT,created INTEGER);
        CREATE TABLE ledger(task TEXT UNIQUE,status TEXT);
        CREATE TABLE credit_packs(id TEXT,org TEXT,plan TEXT,credits INTEGER,starts INTEGER,expires INTEGER);
        CREATE TABLE ledger_packs(task TEXT PRIMARY KEY,pack TEXT);
        CREATE TABLE funnel_daily(day TEXT,event TEXT,n INTEGER);
        ''')
        db.executemany('INSERT INTO users VALUES(?,?,?,?)',[
            ('raw-client-a','private@example.cn','org-a','SECRET-PASSWORD'),
            ('raw-client-b','other@example.cn','org-a','SECRET-PASSWORD'),
            ('raw-qa','qa@fixture.test','org-qa','SECRET-PASSWORD'),
            ('raw-known-qa','qa@company.cn','org-qa','SECRET-PASSWORD')])
        db.executemany('INSERT INTO activity VALUES(?,?,?)',[
            ('raw-client-a','register:iphash',NOW-10*DAY),('raw-client-a','register:duplicate',NOW-9*DAY),
            ('raw-qa','register:iphash',NOW-DAY)])
        start=src.windows(NOW)['today']['start']
        tasks=[('old','raw-client-a','completed',NOW-9*DAY,'SECRET-QUESTION'),
            ('today','raw-client-a','completed',start,'SECRET-QUESTION'),
            ('failed','raw-client-a','failed',NOW-1,'SECRET-QUESTION'),
            ('cancel','raw-client-b','cancelled',NOW-2,'SECRET-QUESTION'),
            ('pending','raw-client-b','awaiting_confirmation',NOW-3,'SECRET-QUESTION'),
            ('qa-task','raw-qa','completed',NOW-4,'SECRET-QUESTION'),
            ('known-qa-task','raw-known-qa','completed',NOW-5,'SECRET-QUESTION')]
        db.executemany('INSERT INTO tasks VALUES(?,?,?,?,?)',tasks)
        db.execute('INSERT INTO followups VALUES(?,?)',('raw-client-a',NOW-8*DAY))
        db.executemany('INSERT INTO ledger VALUES(?,?)',[('today','charged'),('old','charged'),('failed','refunded'),('cancel','refunded')])
        db.execute('INSERT INTO credit_packs VALUES(?,?,?,?,?,?)',('pack-a','org-a','monthly',10,NOW-20*DAY,NOW+DAY))
        db.executemany('INSERT INTO ledger_packs VALUES(?,?)',[(x,'pack-a') for x in ['today','old','failed','cancel']])
        db.executemany('INSERT INTO funnel_daily VALUES(?,?,?)',[('2026-11-06','contact_open',9),('2026-11-06','entitlement_granted',2)])
        db.commit();db.close()
        self.log=self.root/'logs';self.log.mkdir()
        (self.log/'tracking-state.json').write_text(json.dumps({'started_at':'2026-10-01T00:00:00Z','research_cta_tracking_started_at':'2026-11-06T00:00:00Z'}))
        self.leads=self.root/'applications.jsonl'; self.leads.write_text('')
        (self.log/'qa-events.jsonl').write_text('')
        self.events=[]
        for i,kwargs in enumerate([{}, {'qa':True},{'self':True},{'bot':True}]):
            self.events.append(dict(event='cta_search',site='www',surface='report',path='/research/',eid=str(i),sid='SECRET-SID-'+str(i),received_at='2026-11-06T01:00:00Z',**kwargs))
        self.events.append(self.events[0].copy())
        self.write_events()

    def tearDown(self): self.tmp.cleanup()
    def write_events(self): (self.log/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in self.events))
    def research(self): return src.research(self.db,NOW,[src.anonymous('raw-known-qa')])
    def web(self): return src.web(self.log,NOW,self.leads)
    def snapshot(self):
        return {'schema_version':1,'generated_at':src.iso(NOW),'mode':'synthetic_fixture','research':self.research(),'web':self.web()}

    def test_read_only_and_privacy(self):
        before=hashlib.sha256(self.db.read_bytes()).hexdigest();result=self.snapshot()
        self.assertEqual(before,hashlib.sha256(self.db.read_bytes()).hexdigest())
        text=json.dumps(result)+dash.accounts_csv(result)+dash.html_page(result,[],'snapshot.json')
        for secret in ['raw-client','private@example','SECRET-QUESTION','SECRET-PASSWORD','SECRET-SID','org-a','pack-a']:
            self.assertNotIn(secret,text)

    def test_qa_status_refunds_shared_quota(self):
        r=self.research();self.assertEqual(r['account_count'],2)
        self.assertEqual(r['exclusions']['reserved_test_domain'],1)
        self.assertEqual(r['exclusions']['explicit_known_qa'],1)
        a=r['windows']['today'];self.assertEqual(a['completed_tasks'],1);self.assertEqual(a['refunded_slots'],2)
        self.assertEqual(a['states']['awaiting_confirmation'],1)
        self.assertEqual(a['qa_mixed_operations']['entitlement_granted'],2)
        self.assertTrue(all(x['quota_shared_with_other_accounts'] for x in r['accounts']))
        self.assertTrue(all(x['remaining']==8 for x in r['accounts']))
        self.assertEqual(a['registration_time_unknown_accounts'],1)

    def test_sg_boundaries_and_maturity(self):
        spans=src.windows(NOW);self.assertEqual(src.iso(spans['today']['start']),'2026-11-05T16:00:00+00:00')
        self.assertEqual(spans['7d']['start'],spans['today']['start']-6*DAY)
        r=self.research();self.assertEqual(r['return_7d']['rate'],1)
        self.assertEqual(r['return_7d']['immature_accounts'],1)
        self.assertIsNone(r['trend'][0]['started'])
        self.assertEqual(r['windows']['today']['first_research_accounts'],1)

    def test_receipt_dedupe_not_payments(self):
        receipt={'id':'PRIVATE-RECEIPT','ts':'2026-11-06T01:00:00Z','email':'SECRET-MAIL'}
        self.leads.write_text(json.dumps(receipt)+'\n'+json.dumps(receipt)+'\n'+json.dumps(dict(receipt,id='qa',funnel={'qa':True}))+'\n')
        w=self.web();self.assertEqual(w['windows']['today']['cta_sessions']['research_app'],1)
        self.assertEqual(w['windows']['today']['mcp_application_receipts'],1)
        self.assertIsNone(w['mcp_verified_payments'])
        for key in ['self','bot','qa_in_natural_log','duplicate_event_id','duplicate_application_receipt']:
            self.assertEqual(w['exclusions'][key],1)
        self.assertEqual(w['windows']['7d']['status'],'partial')
        self.assertNotIn('PRIVATE-RECEIPT',json.dumps(w))

    def test_missing_corrupt_sources_unknown(self):
        (self.log/'events.jsonl').unlink();w=self.web()
        self.assertEqual(w['status'],'unknown');self.assertIsNone(w['windows']['today']['mcp_cta_sessions'])
        (self.log/'events.jsonl').write_text('[]\nnot-json\n');self.assertEqual(self.web()['status'],'unknown')
        self.leads.write_text('not-json\n');self.assertIsNone(self.web()['windows']['today']['mcp_application_receipts'])
        self.assertEqual(src.collect(self.root/'missing.db',self.log,self.leads,now=NOW)['research']['status'],'unknown')

    def test_immutable_stale_and_component_recovery(self):
        out=self.root/'private';a=self.snapshot();first=dash.save(a,out)
        original=(out/first['snapshot']).read_bytes();good=(out/'last-good.json').read_bytes()
        failed={'schema_version':1,'generated_at':src.iso(NOW+DAY),'mode':'synthetic_fixture','research':{'status':'unknown'},'web':{'status':'unknown'}}
        dash.save(failed,out);v=json.loads((out/'latest.json').read_text())
        self.assertEqual(v['research']['status'],'stale');self.assertEqual(v['research']['as_of'],src.iso(NOW))
        self.assertEqual(v['research']['window_bounds']['today'],a['research']['window_bounds']['today'])
        self.assertEqual(good,(out/'last-good.json').read_bytes());self.assertEqual(original,(out/first['snapshot']).read_bytes())
        failed['research']=a['research'];dash.save(failed,out)
        self.assertEqual(json.loads((out/'latest.json').read_text())['web']['status'],'stale')
        self.assertEqual(len(list((out/'snapshots').rglob('*.json'))),3)
        self.assertEqual((out/'index.html').stat().st_mode&0o777,0o600)

    def test_public_rejected_and_offline_isolated(self):
        with self.assertRaises(ValueError):dash.save(self.snapshot(),self.root/'wenshucha-site'/'admin')
        a=self.snapshot();out=self.root/'private';dash.save(a,out)
        a['mode']='production';a['research']={'status':'unknown'};a['web']={'status':'unknown'}
        dash.save(a,out);self.assertEqual(json.loads((out/'latest.json').read_text())['research']['status'],'unknown')

    def test_html_links_unknowns_and_window_labels(self):
        page=dash.html_page(self.snapshot(),[],'snapshots/a.json')
        self.assertIn('匿名帳號 CSV',page);self.assertIn('href="snapshots/a.csv"',page)
        self.assertIn('實際窗口',page);self.assertIn('來源讀取品質',page)


if __name__=='__main__':unittest.main()
