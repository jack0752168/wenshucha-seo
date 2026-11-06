#!/usr/bin/env python3
"""Isolated execution path checks, never invoke production publication."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class LegacySyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.bin=self.root/'bin';self.bin.mkdir()
        self.trace=self.root/'trace';self.web=self.root/'webroot';self.web.write_text('keep-site')
        self.stamp=self.root/'stamp';self.stamp.write_text('keep-revision')
        self.entry=self.root/'formal-sync.sh';self.lock=self.root/'sync.lock'
        self.env=dict(os.environ,PATH=str(self.bin)+':'+os.environ['PATH'],WSC_FORMAL_SYNC=str(self.entry),WSC_SYNC_LOCK=str(self.lock),TEST_TRACE=str(self.trace))
        self.command('flock','printf "%s\\n" "$@" >> "$TEST_TRACE"\nshift 4\nexec "$@"\n')
        for command in ('curl','tar','cp','rsync'):
            self.command(command,'echo FORBIDDEN >> "$TEST_TRACE"\nexit 99\n')

    def tearDown(self):self.tmp.cleanup()
    def command(self,name,code):
        file=self.bin/name;file.write_text('#!/bin/bash\n'+code);file.chmod(0o700)
    def run_sync(self):return subprocess.run(['bash',str(ROOT/'deploy/sync-wenshucha-site.sh')],env=self.env,capture_output=True,text=True)
    def unchanged(self):
        self.assertEqual(self.web.read_text(),'keep-site');self.assertEqual(self.stamp.read_text(),'keep-revision')

    def test_delegates_formal_path_and_shared_lock(self):
        self.entry.write_text('echo formal_guard >> "$TEST_TRACE"\nexit 0\n')
        self.assertEqual(self.run_sync().returncode,0)
        trace=self.trace.read_text();self.assertIn(str(self.lock),trace);self.assertIn(str(self.entry),trace);self.assertIn('formal_guard',trace);self.assertNotIn('FORBIDDEN',trace)
        self.unchanged()

    def test_failure_missing_no_fallback(self):
        self.assertEqual(self.run_sync().returncode,2);self.unchanged()
        self.entry.write_text('echo fetch_failed >> "$TEST_TRACE"\nexit 2\n')
        self.assertEqual(self.run_sync().returncode,2);self.unchanged()
        self.assertNotIn('FORBIDDEN',self.trace.read_text())

    def test_usage_only_never_calls_publication(self):
        scripts=self.root/'scripts';scripts.mkdir();deploy=self.root/'deploy';deploy.mkdir()
        shutil.copyfile(ROOT/'scripts/daily_run.sh',scripts/'daily_run.sh')
        (scripts/'product_usage_dashboard.py').write_text('print("private_only")\n')
        (deploy/'sync-wenshucha-site.sh').write_text('echo FORBIDDEN >> "$TEST_TRACE"\nexit 99\n')
        result=subprocess.run(['bash',str(scripts/'daily_run.sh'),'--usage-dashboard-only'],env=self.env,capture_output=True,text=True)
        self.assertEqual(result.returncode,0);self.assertEqual(result.stdout.strip(),'private_only');self.assertFalse(self.trace.exists());self.unchanged()


if __name__=='__main__':unittest.main()
