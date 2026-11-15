#!/usr/bin/env bash
# Fresh environment: rebuild SUT from pristine (or patched) source, new DB, seed, warm-up migrations.
# usage: reset_env.sh [pristine_src_dir] [--big]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/env.sh"
SRC="${1:-${ANYN_SRC:?set ANYN_SRC or pass the source dir}}"
BIG=""; [[ "${2:-}" == "--big" ]] && BIG="--big"
mkdir -p "$ANYN_WORK"
"$HERE/build_sut.sh" "$SRC" "$ANYN_WORK/sut" >/dev/null
rm -f "$ANYN_QLOG"
php "$HERE/init_db.php" "$ANYN_SQLITE" "$HERE/../schema/base_schema_mysql.sql" >/dev/null
HASH=$(php -r 'echo password_hash(getenv("SEED_PASSWORD"), PASSWORD_DEFAULT);')
python3 "$HERE/seed.py" "$ANYN_SQLITE" 1 "$HASH" $BIG >/dev/null
"$HERE/start_server.sh" >/dev/null
# warm-up: trigger every auto-migration (schema.php, gems_lib, ideas_lib, community, gallery)
for p in index.php pages/ideas.php pages/community_gallery.php pages/gallery.php pages/shop.php pages/commission.php; do
  curl -s -o /dev/null -c /dev/null "$ANYN_BASE_URL/anyn/$p"
done
python3 "$HERE/seed.py" "$ANYN_SQLITE" 2 "$HASH" $BIG >/dev/null
rm -f "$ANYN_QLOG"
echo "environment ready: $ANYN_BASE_URL/anyn/  (seed password: $SEED_PASSWORD)"
