#!/usr/bin/env python3
"""Inspect the Mini's publishing receipts and scheduler without opening a browser."""

import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import tempfile
import time

SGT = dt.timezone(dt.timedelta(hours=8))
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', 'codex-mini',
       '/Users/jack/es-mini/python/bin/python3 -']
TUNNEL_LABEL = 'com.jack.magpie-gateway-to-mini'
PORTS = (3425, 9201)
CODEX_JOBS = ('daily-seo-optimize', 'wenshucha-geo-monthly-check')
RECEIPTS_REQUIRED_AFTER = dt.datetime(2026, 11, 25, 16, 30, tzinfo=SGT)

REMOTE = r'''
import datetime as dt
import json
from pathlib import Path
import re
import socket

home = Path.home()
root = home / 'wenshucha-seo'
schedule = json.loads((home / '.dsh/storages/schedule.json').read_text())
log = (root / 'content/drafts/PUBLISH-LOG.md').read_text()
now = dt.datetime.now(dt.timezone.utc)
out = {'checked_at': now.isoformat(), 'platforms': {}, 'listeners': {}}
for port in (3425, 9201):
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=2):
            out['listeners'][str(port)] = True
    except OSError:
        out['listeners'][str(port)] = False

for key, term in [('zhihu','知乎'), ('baijiahao','百家')]:
    entries = []
    for line in log.splitlines():
        fields = line.split('|')
        if len(fields) < 4 or term not in fields[1]:
            continue
        date = re.match(r'(20\d\d-\d\d-\d\d)', fields[0])
        if not date or not re.search(r'已发[布佈]|已發[布佈]', line):
            continue
        if any(word in line for word in ('未发布','未發布','BLOCKER','草稿未','待核验')):
            continue
        identifier = re.search(r'(?<!\d)\d{16,22}(?!\d)', '|'.join(fields[2:5]))
        if identifier:
            entries.append((date[1], identifier[0]))
    latest = max(entries, default=(None, None))
    data = {'last_ledger_publication_date': latest[0],
            'last_ledger_publication_id': latest[1], 'ledger_is_not_current_backend': True}
    for task in schedule['tables']['tasks'].values():
        record = task.get('record', {})
        if term in record.get('title',''):
            data.update(schedule_status=task.get('status'), last_delivery=task.get('lastDelivery'),
                        next_delivery=record.get('scheduledAt'),
                        recovery_rules_linked='PUBLISHING-AUTO-RECOVERY' in record.get('prompt',''),
                        outcome_writer_linked='record_publishing_outcome.py' in record.get('prompt',''))
    receipt = root / ('state/publishing-' + key + '-recovery.json')
    if receipt.is_file():
        recovery = json.loads(receipt.read_text())
        data['last_browser_check'] = {name: recovery.get(name) for name in
                                      ('checked_at','status','publication_attempted','restriction')}
    if occurrence := (data.get('last_delivery') or {}).get('scheduledAt'):
        when = dt.datetime.fromisoformat(occurrence.replace('Z', '+00:00')).astimezone(dt.timezone.utc)
        outcome = root / 'state/publishing-outcomes' / key / f'{when:%Y%m%dT%H%M%SZ}.json'
        if outcome.is_file():
            evidence = json.loads(outcome.read_text())
            data['last_occurrence_receipt'] = {k: evidence.get(k) for k in
                                               ('occurrence','recorded_at','outcome','product_line','post_id','evidence_path')}
    out['platforms'][key] = data
print(json.dumps(out, ensure_ascii=False))
'''


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def at(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00')) if value else None


def assess(snapshot, previous=None):
    now = at(snapshot['checked_at'])
    today = now.astimezone(SGT).date()
    previous = previous or {}
    old_platforms = previous.get('platforms') or previous.get('previous_platform_evidence', {})
    for name, data in snapshot['platforms'].items():
        date = data.get('last_ledger_publication_date')
        data['days_since_ledger_publication'] = (today - dt.date.fromisoformat(date)).days if date else None
        next_due = at(data.get('next_delivery'))
        last_delivery = at((data.get('last_delivery') or {}).get('deliveredAt'))
        if data.get('schedule_status') != 'active':
            data['delivery_status'] = 'expected_schedule_not_active'
        elif not next_due:
            data['delivery_status'] = 'unknown_next_occurrence'
        elif now - next_due > dt.timedelta(minutes=10):
            data['delivery_status'] = 'overdue'
        else:
            data['delivery_status'] = 'observed' if last_delivery else 'awaiting_first_evidence'

        occurrence = at((data.get('last_delivery') or {}).get('scheduledAt'))
        receipt = data.get('last_occurrence_receipt')
        if receipt and at(receipt['occurrence']) == occurrence:
            data['execution_status'] = receipt['outcome']
        elif occurrence and occurrence >= RECEIPTS_REQUIRED_AFTER:
            data['execution_status'] = ('missing_terminal_receipt' if now - occurrence > dt.timedelta(minutes=45)
                                        else 'awaiting_terminal_receipt')
        else:
            data['execution_status'] = 'unknown_before_receipt_policy'

        check = data.get('last_browser_check', {})
        check_at = at(check.get('checked_at'))
        previous_platform = old_platforms.get(name, {})
        last_gate = previous_platform.get('last_account_gate') or previous_platform.get('last_browser_check')
        # A busy or failed probe provides no new account observation.
        if check.get('status') in ('account_restricted', 'ready_for_publication_checks') and check_at:
            if not last_gate or not (gate_at := at(last_gate.get('checked_at'))) or check_at >= gate_at:
                last_gate = check
        if last_gate:
            data['last_account_gate'] = last_gate
        gate_at = at((last_gate or {}).get('checked_at'))
        fresh = bool(gate_at and gate_at <= now and gate_at.astimezone(SGT).date() == today)
        data['browser_evidence_fresh'] = bool(check_at and check_at <= now and check_at.astimezone(SGT).date() == today)
        data['current_account_observation'] = last_gate['status'] if fresh else 'unverified_today'
        if data['current_account_observation'] == 'account_restricted':
            data['business_status'] = 'blocked_account_restricted'
        elif date is None:
            data['business_status'] = 'unknown_publication_evidence'
        elif data['days_since_ledger_publication'] >= 3:
            data['business_status'] = 'stale_publication_requires_investigation'
        else:
            data['business_status'] = 'recent_ledger_publication_requires_backend_verification'
    return snapshot


def probe():
    result = subprocess.run(SSH, input=REMOTE, text=True, capture_output=True, timeout=25, check=True)
    return json.loads(result.stdout)


def local_listeners_ready():
    for port in PORTS:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=2):
                pass
        except OSError:
            return False
    return True


def tunnel_repair(snapshot, previous):
    """Restart only the registered tunnel when both listeners are confirmed down."""
    if snapshot['listeners'] != {str(port): False for port in PORTS}:
        return snapshot, {'status': 'not_needed_or_not_isolated'}
    last_attempt = at((previous.get('tunnel_repair') or {}).get('attempted_at'))
    if last_attempt and at(snapshot['checked_at']) - last_attempt < dt.timedelta(hours=6):
        return snapshot, {'status': 'cooldown', 'attempted_at': last_attempt.isoformat()}
    if not local_listeners_ready():
        return snapshot, {'status': 'local_gateway_dependency_unavailable'}
    second = probe()
    if second['listeners'] != snapshot['listeners']:
        return second, {'status': 'transient_failure_no_restart'}
    service = f'gui/{os.getuid()}/{TUNNEL_LABEL}'
    found = subprocess.run(['launchctl', 'print', service], capture_output=True, timeout=5)
    if found.returncode:
        return second, {'status': 'existing_service_unavailable'}
    attempt = {'attempted_at': second['checked_at'], 'before': second['listeners']}
    restart = subprocess.run(['launchctl', 'kickstart', '-k', service], capture_output=True, timeout=10)
    if restart.returncode:
        return second, {**attempt, 'status': 'restart_failed'}
    time.sleep(2)
    try:
        recovered = probe()
    except (subprocess.SubprocessError, ValueError, OSError):
        return second, {**attempt, 'status': 'restart_unverified'}
    return recovered, {**attempt, 'after': recovered['listeners'],
                       'status': 'listeners_recovered' if all(recovered['listeners'].values()) else 'still_unavailable'}


def codex_jobs(now):
    """Read the active registry and latest formal business receipt independently."""
    root = Path.home() / '.codex'
    db_path = root / 'sqlite/codex.db'
    if not db_path.is_file():
        return {}
    with sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True, timeout=3) as db:
        schedules = db.execute(
            'SELECT id,status,last_run_at,next_run_at FROM automations WHERE id IN (?,?)', CODEX_JOBS
        ).fetchall()
    jobs = {}
    for task, state, last_ms, next_ms in schedules:
        folder = root / 'automations' / task / 'output-evidence'
        paths = sorted(folder.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:12]
        receipts = []
        for path in paths:
            record = read_json(path)
            if record.get('checked_at') and record.get('automation_id') == task:
                receipts.append((at(record['checked_at']), record, path))
        last = dt.datetime.fromtimestamp(last_ms / 1000, dt.timezone.utc) if last_ms else None
        due = dt.datetime.fromtimestamp(next_ms / 1000, dt.timezone.utc) if next_ms else None
        job = {'schedule_status': state, 'last_run_at': last.isoformat() if last else None,
               'next_run_at': due.isoformat() if due else None, 'execution_status': 'unknown'}
        if receipts:
            recorded, evidence, path = max(receipts, key=lambda row: row[0])
            job['last_formal_receipt'] = {'checked_at': recorded.isoformat(), 'outcome': evidence.get('outcome'),
                                          'reason': evidence.get('reason'), 'path': str(path)}
        if state != 'ACTIVE':
            job['execution_status'] = 'expected_schedule_not_active'
        elif due and now - due > dt.timedelta(minutes=10):
            job['execution_status'] = 'overdue'
        elif last and receipts and recorded >= last:
            job['execution_status'] = evidence.get('outcome', 'unknown')
        elif last:
            job['execution_status'] = ('missing_terminal_receipt' if now - last > dt.timedelta(minutes=45)
                                       else 'awaiting_terminal_receipt')
        jobs[task] = job
    return jobs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-dir', type=Path, help='Save immutable observations and issue transitions')
    parser.add_argument('--repair-tunnel', action='store_true')
    parser.add_argument('--with-growth', action='store_true', help='Include the existing SEO and GEO jobs')
    args = parser.parse_args()
    if args.repair_tunnel and not args.state_dir:
        parser.error('--repair-tunnel requires --state-dir for durable retry tracking')
    if args.state_dir:
        args.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (args.state_dir / '.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            run(args)
    else:
        run(args)


def run(args):
    previous = {}
    if args.state_dir:
        previous = read_json(args.state_dir / 'latest.json')
        if not previous:
            baseline = Path(__file__).resolve().parents[1] / 'reports/2026-11-25-mini-publishing-audit/health-baseline.json'
            previous = read_json(baseline)
    recovery = {}
    try:
        snapshot = probe()
        if args.repair_tunnel:
            snapshot, recovery = tunnel_repair(snapshot, previous)
        snapshot = assess(snapshot, previous)
    except (subprocess.SubprocessError, ValueError, OSError) as error:
        snapshot = {'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                    'status': 'unknown', 'reason': type(error).__name__}
    # Preserve the timestamp for retry control even if the next scan is healthy.
    prior_attempt = previous.get('tunnel_repair', {}).get('attempted_at')
    if prior_attempt and 'attempted_at' not in recovery:
        recovery['attempted_at'] = prior_attempt
    snapshot['tunnel_repair'] = recovery
    issues = {}
    if snapshot.get('status') == 'unknown':
        issues['mini'] = 'unreachable_or_unreadable'
        snapshot['previous_platform_evidence'] = previous.get('platforms') or previous.get('previous_platform_evidence', {})
    else:
        if not all(snapshot['listeners'].values()):
            issues['tunnel'] = 'mini_listener_missing'
        for name, data in snapshot['platforms'].items():
            if data['delivery_status'] not in ('observed', 'awaiting_first_evidence'):
                issues[name + ':schedule'] = data['delivery_status']
            if not data['business_status'].startswith('recent_'):
                issues[name + ':publishing'] = data['business_status']
            execution = data['execution_status']
            if execution in ('missing_terminal_receipt', 'login_required', 'policy_blocked',
                             'browser_unavailable', 'model_unavailable', 'submission_unknown', 'failed'):
                issues[name + ':execution'] = execution
    if args.with_growth:
        try:
            snapshot['growth_jobs'] = codex_jobs(at(snapshot['checked_at']))
        except (OSError, ValueError, sqlite3.Error):
            snapshot['growth_jobs'] = {}
        for task in CODEX_JOBS:
            state = snapshot['growth_jobs'].get(task, {}).get('execution_status', 'unknown')
            if state in ('overdue', 'missing_terminal_receipt', 'failed', 'blocked', 'partial', 'unknown',
                         'expected_schedule_not_active'):
                issues[task] = state
            elif state == 'awaiting_terminal_receipt':
                # A new attempt does not clear the preceding unfinished business result.
                prior = snapshot['growth_jobs'][task].get('last_formal_receipt', {}).get('outcome')
                if prior in ('failed', 'blocked', 'partial', 'unknown'):
                    issues[task] = prior
    previous_issues = previous.get('issues', {})
    snapshot['issues'] = issues
    snapshot['new_or_changed_issues'] = {key: value for key, value in issues.items()
                                         if previous_issues.get(key) != value}
    snapshot['cleared_issue_keys'] = sorted(previous_issues.keys() - issues.keys()) if snapshot.get('status') != 'unknown' else []
    if args.state_dir:
        folder = args.state_dir
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        stem = at(snapshot['checked_at']).astimezone(SGT).strftime('%Y%m%dT%H%M%S%f')
        path = folder / f'{stem}.json'
        snapshot['evidence_path'] = str(path)
        output = json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n'
        with path.open('x') as stream:
            stream.write(output)
        with tempfile.NamedTemporaryFile(mode='w', dir=folder, delete=False) as stream:
            stream.write(output)
        Path(stream.name).replace(folder / 'latest.json')
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
