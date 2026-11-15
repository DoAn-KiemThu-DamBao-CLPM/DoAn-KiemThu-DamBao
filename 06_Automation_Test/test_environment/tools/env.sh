# Source me. Central place for the test-environment paths (location independent).
#   ANYN_SRC  : folder that contains the application source (the "anyn" directory with index.php)  [required for reset_env.sh]
#   ANYN_WORK : scratch/runtime folder (SUT copy, sqlite db, logs)                                  [default: ~/anyn_qa_runtime]
export HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ANYN_WORK="${ANYN_WORK:-$HOME/anyn_qa_runtime}"
export ANYN_SHIM="$HARNESS_DIR/shim/MysqlOnSqlitePDO.php"
export ANYN_SQLITE="${ANYN_SQLITE:-$ANYN_WORK/anyn.sqlite}"
export ANYN_QLOG="${ANYN_QLOG:-$ANYN_WORK/queries.log}"
export ANYN_PORT="${ANYN_PORT:-8765}"
export ANYN_BASE_URL="http://127.0.0.1:$ANYN_PORT"
export SEED_PASSWORD='User@12345'
