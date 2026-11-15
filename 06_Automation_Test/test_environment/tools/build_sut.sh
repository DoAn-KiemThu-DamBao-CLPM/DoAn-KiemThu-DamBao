#!/usr/bin/env bash
# Build the System Under Test (SUT) from the pristine source archive.
# Only config/database.php is touched: the MySQL connection is swapped for the SQLite shim.
# usage: build_sut.sh <pristine_anyn_dir> <sut_root_dir> [patched_dir_for_fixed_build]
set -euo pipefail
SRC="${1:?pristine anyn dir}"; DST="${2:?sut root}"
rm -rf "$DST/anyn"; mkdir -p "$DST"
cp -a "$SRC" "$DST/anyn"
python3 - "$DST/anyn/config/database.php" <<'PY'
import sys,re
p=sys.argv[1]; s=open(p,encoding='utf-8').read()
old="    $pdo = new PDO($dsn, $user, $pass, $options);"
new=("    // [QA-HARNESS] MySQL is not available in the test sandbox -> SQLite compatibility layer.\n"
     "    require_once getenv('ANYN_SHIM');\n"
     "    $pdo = new MysqlOnSqlitePDO('sqlite:' . getenv('ANYN_SQLITE'), null, null, $options);")
assert old in s, "anchor not found"
open(p,'w',encoding='utf-8').write(s.replace(old,new))
PY
echo "SUT built at $DST/anyn"
