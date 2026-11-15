Nhom05_AnynRoleplayBotStore – gói nộp bài đồ án Kiểm thử & Đảm bảo chất lượng phần mềm
=========================================================================================

Hệ thống kiểm thử: Anyn – cửa hàng & cộng đồng nhân vật nhập vai (PHP 8 + MySQL), mã nguồn anyn_updated_1.zip.
Nhóm: Nhóm 05  |  GVHD: Trần Thị Tuyết Vân  |  Ngày lập: 14/11/2026
Repository: https://github.com/DoAn-KiemThu-DamBao-CLPM/DoAn-KiemThu-DamBao

CẤU TRÚC (theo gợi ý ở mục 12 của hướng dẫn)
  01_Project_Proposal/          Mô tả hệ thống, FR/NFR, phạm vi, kế hoạch 15 tuần
  02_Test_Plan/                 Kế hoạch kiểm thử, môi trường, tiêu chí vào/ra, rủi ro, threats to validity
  03_Test_Scenario_Test_Case/   11 scenario, 94 test case (xlsx) + đặc tả chi tiết và giải thích kỹ thuật (docx)
  04_Test_Execution/            Kết quả thực thi 2 vòng, hồi quy, hiệu năng, chỉ mục bằng chứng (xlsx) + evidence/
  05_Defect_Reports/            Sổ lỗi (xlsx), 19 phiếu lỗi chi tiết (docx), bản vá từng lỗi (per_bug/)
  06_Automation_Test/           Mã kiểm thử tự động, môi trường dựng lại, kết quả thô, báo cáo automation
  07_Nonfunctional_Test/        Báo cáo bảo mật / hiệu năng / responsive + dữ liệu thô
  08_Test_Summary_Report/       Báo cáo tổng kết và khuyến nghị phát hành
  09_Presentation/              Slide bảo vệ (pptx) + kịch bản demo và bộ câu hỏi vấn đáp
  Contribution_Log.xlsx         Mẫu nhật ký đóng góp – NHÓM TỰ ĐIỀN

THÀNH VIÊN: Thái Hoàng Minh (DPM235451, QA Lead), Lâm Hoài An (DPM235402, Functional Tester 1, chủ hệ thống Anyn), Nguyễn Phúc Khang (DPM235429, Functional Tester 2), Võ Trường Hải (DPM235414, Automation Tester), Châu Minh Tuệ (DPM235494, Performance/Security Tester)

KẾT QUẢ CHÍNH (số liệu lấy từ các tệp JSON trong 06_Automation_Test/results)
  - 118 test case tự động (94 chức năng + 9 giao diện + 15 phi chức năng), 7 kỹ thuật thiết kế test case.
  - Vòng 1 (bản gốc): 98 Pass / 20 Fail; vòng 2 (bản đã vá): 115 Pass / 2 Fail / 1 Blocked; hồi quy 98/98.
  - 19 lỗi: 1 Critical, 6 High, 7 Medium, 5 Low. Khuyến nghị: bản gốc NO-GO; bản đã vá là ứng viên phát hành có điều kiện.

CHẠY LẠI KẾT QUẢ (chi tiết: 06_Automation_Test/README.md)
  cd 06_Automation_Test && export ANYN_SRC=/đường/dẫn/anyn && source ./envrc.sh
  ./run_cycle.sh cycle1 "$ANYN_SRC"                       # ~70 giây

LƯU Ý TRUNG THỰC / HẠN CHẾ
  1. Môi trường kiểm thử dùng SQLite qua lớp tương thích MySQL (không có MySQL) – cần chạy lại trên MySQL thật trước khi phát hành.
  2. Gói nguồn không có lược đồ CSDL của các bảng lõi: lược đồ được dựng lại (giả định A-01); không có tài liệu yêu cầu nên kết quả mong đợi suy ra từ mã nguồn.
  3. Máy chủ PHP built-in bỏ qua .htaccess: BUG-018 chưa kiểm chứng được (Blocked), cần chạy lại trên Apache.
  4. Số đo thời gian hiệu năng chỉ mang tính chỉ báo (loopback, SQLite).
  5. Các bản vá do người kiểm thử viết và chỉ kiểm chứng trên bản sao thử nghiệm; nhóm phát triển cần rà soát. BUG-013 và BUG-019 chủ động hoãn.
  6. Nhật ký đóng góp (Contribution_Log.xlsx) và nỗ lực thực tế: để trống, do từng thành viên tự ghi.
  7. Hướng dẫn đồ án yêu cầu sinh viên hiểu, kiểm chứng và giải thích được mọi nội dung nộp (mục 11): hãy đọc và chạy lại trước khi bảo vệ.
