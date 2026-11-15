#!/usr/bin/env bash
# Start the PHP built-in web server (4 workers) serving <sut_root>/anyn  ->  http://127.0.0.1:$ANYN_PORT/anyn/
# php.ini values mimic a default XAMPP install (upload 40M, display_errors on, E_ALL).
set -euo pipefail
source "$(dirname "$0")/env.sh"
SUT_ROOT="${1:-$ANYN_WORK/sut}"
pkill -f "php.*-S 127.0.0.1:$ANYN_PORT" 2>/dev/null || true
sleep 0.3
PHP_CLI_SERVER_WORKERS=4 nohup php \
  -d upload_max_filesize=40M -d post_max_size=40M -d memory_limit=256M \
  -d display_errors=1 -d error_reporting=E_ALL -d date.timezone=UTC \
  -d session.gc_maxlifetime=1440 \
  -S 127.0.0.1:$ANYN_PORT -t "$SUT_ROOT" > "$ANYN_WORK/server.log" 2>&1 &
echo $! > "$ANYN_WORK/server.pid"
for i in $(seq 1 40); do
  if curl -s -o /dev/null "http://127.0.0.1:$ANYN_PORT/anyn/pages/login.php"; then echo "server up (pid $(cat $ANYN_WORK/server.pid))"; exit 0; fi
  sleep 0.25
done
echo "server failed to start"; cat "$ANYN_WORK/server.log"; exit 1
