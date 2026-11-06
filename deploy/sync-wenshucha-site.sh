#!/bin/bash
# Legacy daily entry delegates to the verified publisher; never copy a tarball.
set -u
ENTRY=${WSC_FORMAL_SYNC:-/root/sync-wenshucha-site.sh}
LOCK=${WSC_SYNC_LOCK:-/tmp/sync-wsc.lock}
if [ ! -f "$ENTRY" ] || ! command -v flock >/dev/null 2>&1; then
    echo 'UNKNOWN: formal site publisher or shared lock unavailable; no publish' >&2
    exit 2
fi
# Same lock as the five-minute autoheal and direct deployment transaction.
flock -x -w 120 "$LOCK" bash "$ENTRY"
rc=$?
if [ "$rc" -ne 0 ]; then
    echo "UNKNOWN: formal site publisher failed ($rc); no legacy fallback" >&2
fi
exit "$rc"
