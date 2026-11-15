# Source file:  source ./envrc.sh
# Đặt các biến môi trường cho bộ kiểm thử. Chỉ BẮT BUỘC đặt ANYN_SRC (thư mục "anyn" chứa index.php của mã nguồn gốc).
#   ANYN_SRC  : thư mục mã nguồn ứng dụng (giải nén anyn_updated_1.zip → thư mục anyn/)
#   ANYN_WORK : thư mục chạy tạm (bản sao SUT, CSDL SQLite, log). Mặc định ~/anyn_qa_runtime
QA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export QA_ROOT
source "$QA_ROOT/test_environment/tools/env.sh"
export ANYN_UPLOAD_DIR="$ANYN_WORK/sut/anyn/uploads"
export PYTHONDONTWRITEBYTECODE=1
