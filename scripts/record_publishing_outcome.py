#!/usr/bin/env python3
"""Persist a Mini publishing occurrence's terminal evidence once."""

import argparse
import datetime as dt
import json
from pathlib import Path
import re

STATUS = ('published_verified', 'no_eligible_topic', 'account_restricted', 'login_required',
          'policy_blocked', 'browser_unavailable', 'model_unavailable', 'submission_unknown', 'failed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('platform', choices=('zhihu', 'baijiahao'))
    parser.add_argument('occurrence', help='Scheduled occurrence in ISO 8601 with an offset')
    parser.add_argument('outcome', choices=STATUS)
    parser.add_argument('--evidence', required=True, type=Path, help='Immutable checkpoint or post readback')
    parser.add_argument('--reason', required=True)
    parser.add_argument('--product', choices=('case_search', 'mcp', 'local_data'))
    parser.add_argument('--post-id')
    args = parser.parse_args()

    try:
        occurrence = dt.datetime.fromisoformat(args.occurrence.replace('Z', '+00:00'))
        if occurrence.tzinfo is None:
            raise ValueError()
        occurrence = occurrence.astimezone(dt.timezone.utc)
    except ValueError:
        parser.error('occurrence must include the timezone offset')
    evidence = args.evidence.resolve()
    if not evidence.is_file():
        parser.error('evidence file does not exist')
    if args.outcome == 'published_verified':
        if not args.product or not re.fullmatch(r'[0-9]{16,22}', args.post_id or ''):
            parser.error('verified publication requires its product line and platform post ID')
        if args.post_id not in evidence.read_text():
            parser.error('checkpoint must include the verified post ID')
    elif args.post_id:
        parser.error('post ID is reserved for verified publication')
    root = Path(__file__).resolve().parents[1] / 'state/publishing-outcomes' / args.platform
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = root / f'{occurrence:%Y%m%dT%H%M%SZ}.json'
    result = {'platform': args.platform, 'occurrence': occurrence.isoformat(),
              'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat(), 'outcome': args.outcome,
              'reason': args.reason, 'product_line': args.product, 'post_id': args.post_id,
              'evidence_path': str(evidence)}
    try:
        with path.open('x') as document:
            json.dump(result, document, ensure_ascii=False, indent=2)
            document.write('\n')
    except FileExistsError:
        print(f'Existing receipt retained: {path}')
        return
    print(path)


if __name__ == '__main__':
    main()
