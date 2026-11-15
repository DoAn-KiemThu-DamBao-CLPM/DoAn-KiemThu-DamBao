#!/usr/bin/env bash
# Chạy MỘT vòng kiểm thử hoàn chỉnh (dựng môi trường sạch → chức năng + bảo mật + UI → hiệu năng dữ liệu nhỏ → hiệu năng dữ liệu lớn).
#
#   ./run_cycle.sh <tên_vòng> <thư_mục_anyn> [thư_mục_gốc_kết_quả]
#
#   Vòng 1 (bản gốc)  : ./run_cycle.sh cycle1 /đường/dẫn/anyn
#   Vòng 2 (bản vá)   : python3 test_environment/patches/fixes.py apply /đường/dẫn/anyn /đường/dẫn/anyn_fixed/anyn
#                       ./run_cycle.sh cycle2 /đường/dẫn/anyn_fixed/anyn
#
# Kết quả ghi vào <thư_mục_gốc_kết_quả>/<tên_vòng>/ (mặc định ./results). THƯ MỤC ĐÓ BỊ XOÁ TRƯỚC KHI CHẠY để không trộn với lần chạy cũ.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CYCLE="${1:?thiếu tên vòng (cycle1|cycle2)}"
SRC="$(cd "${2:?thiếu thư mục mã nguồn anyn}" && pwd)"
RES_ROOT="${3:-$HERE/results}"
source "$HERE/envrc.sh"
export QA_CYCLE="$CYCLE" QA_RESULTS_DIR="$RES_ROOT"
cd "$HERE"
rm -rf "$RES_ROOT/$CYCLE"; mkdir -p "$RES_ROOT/$CYCLE"
ENVSH="$HERE/test_environment/tools/reset_env.sh"

echo "== [1/4] Dựng môi trường sạch, dữ liệu NHỎ  (nguồn: $SRC)"
"$ENVSH" "$SRC" || exit 2
echo "== [2/4] Chức năng + bảo mật + giao diện (tests/)"
python3 -m pytest tests -q
echo "== [3/4] Hiệu năng – dữ liệu nhỏ (nonfunctional/)"
python3 -m pytest nonfunctional -q
echo "== [4/4] Dựng lại môi trường với dữ liệu LỚN rồi đo hiệu năng"
"$ENVSH" "$SRC" --big || exit 2
python3 -m pytest nonfunctional -q
pkill -f "php.*-S 127.0.0.1:$ANYN_PORT" 2>/dev/null || true
echo "== Xong. Kết quả: $RES_ROOT/$CYCLE/"
ls "$RES_ROOT/$CYCLE"
