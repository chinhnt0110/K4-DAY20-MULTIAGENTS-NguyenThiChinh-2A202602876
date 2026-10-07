# Báo cáo Lab: Self evolving Agentic

> Sao chép tệp này thành `report/REPORT.md` (đã làm ở Phần 0) và điền dần qua các Phần của lab. Xóa các dòng hướng dẫn dạng trích dẫn (bắt đầu bằng `>`). Văn phong kỹ thuật, ngắn gọn, mọi nhận định đi kèm số liệu hoặc bằng chứng. Trong buổi học: điền mục 1 đến 7 (bản nháp). Sau buổi học: hoàn thiện mục 8 đến 10.

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Thị Chinh| 2A202602876 | Toàn bộ |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: OpenAI gpt-4o-mini, LAB_TEMPERATURE=0, recursion_limit=40
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker:
- Số lần chạy tác vụ đã dùng / ngân sách:
- Commit của tag `freeze`:

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

> Dự đoán điều kiện nào đạt điểm cao nhất trên **tác vụ đánh giá** và vì sao. Nêu căn cứ từ phân loại lỗi (mục 4) và từ tài liệu tham khảo. Điền cả ba dòng; `verify_freeze.py` kiểm tra điều này.

- H1 (subagents so với baseline): Điều kiện `subagents` sẽ đạt điểm tương đương hoặc chỉ nhỉnh hơn không đáng kể so với `baseline` trên tác vụ đánh giá, nhưng sẽ tiêu tốn lượng token cao hơn (dự kiến tăng 1.5 - 2.5 lần). Căn cứ: từ quan sát ở Phần 2.3, tác tử chính thường tự thực hiện hoặc khi ủy quyền thì subagent bị cô lập ngữ cảnh (`context isolation`), không nắm được các quy ước ngầm nên không giúp cải thiện các check `rule_`.
- H2 (skills-auto so với baseline): Điều kiện `skills-auto` có thể cải thiện điểm nếu tác vụ đánh giá tình cờ dùng chung một số quy ước lập trình chuẩn (như type hints hay changelog), nhưng mức cải thiện tổng thể trên tác vụ đánh giá sẽ thấp do hiện tượng quá khớp (overfitting). Căn cứ: nghiên cứu SkillsBench và SkillEvolBench ghi nhận skill do LLM tự sinh trung bình không mang lại lợi thế vượt trội trên tác vụ mới ngoài miền học.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số trên tác vụ học sẽ cao hơn tác vụ đánh giá ở điều kiện `skills-auto`, thể hiện rõ khoảng cách tổng quát hóa (generalization gap). Căn cứ: Curator được cung cấp phản hồi lỗi trực tiếp từ các check thất bại của tập học nên nội dung skill phản ánh sát các quy ước của tập học; trong khi đó tác vụ đánh giá chứa các yêu cầu và quy ước mới mà Curator chưa từng nhìn thấy.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có những công cụ nào? Công cụ nào cho phép chạy lệnh?
> Tác tử mặc định có các công cụ: file tools (`ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`), shell (`execute`) và subagents (`task`).
> Công cụ cho phép chạy lệnh là `execute`

2. Mô tả của công cụ `task` nói gì về subagent `general-purpose`? Subagent đó nhìn thấy ngữ cảnh nào của tác tử chính?
> Mô tả của công cụ `task` nói subagent `general-purpose` dùng để nghiên cứu các vấn đề phức tạp đòi hỏi nhiều ngữ cảnh, tìm kiếm file và nội dung nhưng không chắc sẽ tìm thấy kết quả ở lần thử đầu tiên, cũng như thực thi các tác vụ nhiều bước.
> Subagent này truy cập toàn bộ ngữ cảnh của tác tử chính.

3. System prompt mặc định của Deep Agents rỗng. Trích một câu hướng dẫn hành vi từ mô tả của công cụ `task` và một câu từ mô tả của công cụ `execute`.
> `task`: "Launch multiple agents concurrently when their tasks are independent, using a single message with multiple tool calls."
> `execute`: "Quote paths containing spaces (e.g. cd "/path/with spaces")"

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

> Chỉ dùng tác vụ học. Mỗi dòng là một check thất bại.

| Tác vụ | Check thất bại | Nhóm lỗi (A-G) | Bằng chứng (trích ngắn từ `detail` hoặc vết) |
|---|---|---|---|
| `data-learn` | `north_q1_revenue` | F (hoặc A) | Tác tử báo do môi trường thiếu `pandas` nên tự điền giá trị 0 vào `answer.json` thay vì đọc file csv bằng thư viện chuẩn csv. `detail: "north_q1_revenue: wrong value (got 0)"` |
| `data-learn` | `rule_money_in_cents` | E (Quy ước tổ chức) | `detail: "RULE: money values in answer.json are integer cents (1606.67 USD is written 160667)."` |
| `data-learn` | `rule_meta_block` | E (Quy ước tổ chức) | `detail: "RULE: answer.json has an object meta = {\"source\": <input file name>...}"` |
| `data-learn` | `rule_clean_csv` | E (Quy ước tổ chức) | `detail: "RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents..."` |
| `code-learn` | `parse_price_all_formats` | D (Dữ liệu bẩn/biên) | Tác tử chỉ replace `$` và `,` mà bỏ sót định dạng ngoặc đơn biểu thị số âm trong kế toán `(12.00)`. `detail: "wrong for: ['(12.00)']"`. |
| `code-learn` | `csv_quoting_follows_docstring` | A (Bỏ qua đặc tả) | Bỏ qua yêu cầu quote dấu nháy kép trong docstring. `detail: "to_csv_row returned 'Desk, large \"oak\",10.00,2'"`. |
| `code-learn` | `rule_type_hints` | E (Quy ước tổ chức) | `detail: "RULE: every public function in the package has type annotations on all parameters and on the return value."` |
| `code-learn` | `rule_regression_tests` | E (Quy ước tổ chức) | `detail: "RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass."` |
| `code-learn` | `rule_changelog` | E (Quy ước tổ chức) | `detail: "RULE: record each fix in CHANGELOG.md under the heading '## Unreleased'..."` |
| `logs-learn` | `rule_service_names` | E (Quy ước tổ chức) | `detail: "RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service)."` |
| `logs-learn` | `rule_schema_header` | E (Quy ước tổ chức) | `detail: "RULE: the top-level object has \"schema_version\": 2 and \"generated_by\": \"log-triage\"."` |
| `logs-learn` | `timestamps_utc` | D (Định dạng/múi giờ) | Không chuyển đổi đúng múi giờ UTC hoặc định dạng ISO-8601. `detail: "0/25 timestamps match"`. |


**Nhận xét:**
1. **Nhóm lỗi chiếm đa số:** Nhóm **E (Vi phạm quy ước tổ chức ngầm `rule_*`)** chiếm tỷ lệ lớn nhất trên cả 3 tác vụ. Đây là các quy ước nội bộ đặc thù của tổ chức Acme không có trong prompt/README của đề bài mà chỉ có review bot kiểm tra.
2. **Khả năng phòng ngừa của Skill:** Một skill do Curator sinh ra **hoàn toàn có thể phòng ngừa nhóm lỗi E**, vì skill có thể đóng gói các quy ước tổ chức ngầm này thành quy tắc hướng dẫn hành động (ví dụ: luôn viết `meta` block, chuyển tiền sang cents, thêm type hint và cập nhật `CHANGELOG.md`).
3. **Bằng chứng phủ định cho các nhóm kỹ thuật (A-D):** Đối với các tác vụ thuần kỹ thuật như `code-learn`, mô hình gpt-4o-mini thực hiện tốt hầu hết các yêu cầu cơ bản (đạt 5/5 check kỹ thuật: test suite ban đầu pass, không sửa bậy test, sửa đúng discount rounding và low_stock logic). Các lỗi ở nhóm A-D chủ yếu xảy ra khi dữ liệu có trường hợp biên phức tạp (`(12.00)`) hoặc khi tác tử vội vàng kết luận do thiếu thư viện (`data-learn`).

## 5. Điều kiện `subagents` (Phần 2.3)

- **Các subagent đã định nghĩa (tên, vai trò, lý do thiết kế):**
  - `explorer`: Vai trò chỉ đọc, khảo sát cấu trúc repository, README, docstrings và dữ liệu mẫu; báo cáo sự thật cho tác tử chính; không sửa đổi file.
  - `implementer`: Vai trò thực thi thay đổi mã nguồn, tạo file hoặc chạy các lệnh test/script kiểm chứng theo chỉ đạo chi tiết của tác tử chính.
  - `reviewer`: Vai trò kiểm tra độc lập kết quả sau khi cài đặt, đối chiếu với yêu cầu đề bài và các trường hợp biên; không sửa file.

- **`subagent_calls` ở từng tác vụ và nhận xét:**
  - `data-learn`: **1 lần gọi**. Tác tử chính sau khi đọc `sales.csv` và `README.md` đã chủ động ủy quyền cho subagent `implementer` với chỉ dẫn chi tiết: *"Analyze the sales data in 'workspace/sales.csv' to compute the following metrics... Write the results to 'workspace/answer.json' in JSON format."*
  - `code-learn`: **0 lần gọi**. Tác tử chính nhận định bài toán sửa lỗi code trong package `inventory` có thể tương tác trực tiếp với file và test bằng các công cụ shell/edit_file có sẵn, nên quyết định tự giải quyết mà không ủy quyền.
  - `logs-learn`: **0 lần gọi**. Tác tử chính tự đọc và xử lý log đơn giản trong 3 tool calls.

- **Thông tin thiếu hoặc thừa khi giao việc (nếu có giao việc):**
  - Ở `data-learn`, lời giao việc của tác tử chính cho `implementer` rất đầy đủ về mặt mô tả metric, nhưng **thiếu các quy ước tổ chức ngầm của Acme** (như `rule_money_in_cents`, `rule_meta_block`, `rule_clean_csv`) vì tác tử chính vốn không biết các quy ước này. Subagent làm đúng theo prompt ủy quyền nhưng vẫn không đạt các check `rule_`.

- **Ảnh hưởng đến token và thời gian:**
  - `data-learn`: Token tăng từ **25,637** (baseline) lên **61,141** (tăng ~2.4 lần) và thời gian tăng từ 13.7s lên 41.5s do phát sinh thêm ngữ cảnh và các bước suy luận bên trong subagent.
  - `code-learn` và `logs-learn`: Khi không kích hoạt subagent, chi phí token và thời gian tương đương baseline (code-learn: 69.8k so với 75.3k tokens; logs-learn: 21.9k so với 21.4k tokens).


## 6. Self-evolving: skill do curator sinh (Phần 3)

- Số lần chạy curator: 1 lần
- Số skill sinh ra: 3 skill
- Số skill bị xóa: 0

| Skill | Tổng quát hay riêng cho tác vụ học? | Đúng hay sai (nêu chỗ sai nếu có) | Độ dài, `description` và `skills_read` ở Phần 3.4 |
|---|---|---|---|
| `validate-function-annotations` | **Tổng quát**: Hướng dẫn thêm type hint cho mọi tham số và giá trị trả về của hàm công khai, không chứa tên file hay ID tác vụ cụ thể. | **Đúng**: Cung cấp checklist kiểm tra type hint chuẩn mực cho Python. | • Độ dài: 13 dòng.<br>• `description`: *"Use this skill when defining public functions to ensure all parameters and return values have type annotations."*<br>• `skills_read`: **0** |
| `ensure-test-coverage` | **Tổng quát**: Hướng dẫn viết unit test cho các hàm sửa đổi/thêm mới, bao phủ các trường hợp biên và kiểm tra test pass. | **Đúng**: Quy trình viết regression test tốt, độc lập với bài toán cụ thể. | • Độ dài: 15 dòng.<br>• `description`: *"Use this skill when making changes to code to ensure that adequate tests are created or updated."*<br>• `skills_read`: **0** |
| `maintain-changelog` | **Bán tổng quát**: Đóng gói quy ước định dạng `- fix(<function name>): <short description>` dưới mục `## Unreleased` trong `CHANGELOG.md` (học từ phản hồi của check `rule_changelog`). | **Đúng**: Định dạng chuẩn theo quy ước quản lý phiên bản và đáp ứng đúng quy tắc của review bot. | • Độ dài: 13 dòng.<br>• `description`: *"Use this skill when making changes to code to ensure that all modifications are documented in the changelog."*<br>• `skills_read`: **0** |

**Nhận xét việc dùng skill (Phần 3.4):**
- Qua quan sát `trace.md`, ở lượt hành động đầu tiên, tác tử chính tập trung ngay vào việc điều tra nguyên nhân lỗi code/data trong `workspace/` (gọi `glob` và `read_file` trên code) mà không chủ động gọi `read_file` trên các file trong `skills/`.
- Điều này phản ánh đặc tính thực tế: dù system prompt có khuyến khích đọc skill trước (`SKILLS_NOTE`), mô hình ngôn ngữ vẫn có xu hướng ưu tiên giải quyết trực diện nhiệm vụ chính khi `description` chưa đủ hấp dẫn để kích hoạt việc tra cứu tri thức bên ngoài.


## 7. Kết quả so sánh (Phần 4.3, 4.4)

> Dán nội dung `report/table.md` và kết quả `python scripts/check_breakdown.py`. Nêu các lần chạy có `error` hoặc `skills_modified = true` (nếu có) và cách xử lý.

```text
(dán bảng ở đây)
```
Sự cố và cách xử lý: Ở lần chạy baseline đầu tiên của tác vụ data-learn với recursion_limit=60, tác tử bị rơi vào vòng lặp gọi công cụ dẫn đến GraphRecursionError (tiêu tốn ~385k tokens). 
-> Cách xử lý: Đặt lại tham số --recursion-limit 40 theo hướng dẫn của GUIDE.md; lần chạy lại hoàn thành bình thường sau 13.7s, tiêu tốn 25,637 tokens, không còn lỗi (error: null).

## 8. Phân tích

> Trả lời từng câu bằng số liệu từ mục 7 và bằng chứng từ vết. Kết quả âm hoặc không có khác biệt vẫn hợp lệ nếu được phân tích tốt.

1. So với `baseline`, điều kiện nào cải thiện điểm tác vụ **học**? Điều kiện nào cải thiện điểm tác vụ **đánh giá**? Có điều kiện nào cải thiện tác vụ học nhưng không cải thiện tác vụ đánh giá? Nếu có, đó là dấu hiệu gì?
2. Tách điểm thành check kỹ thuật và check quy ước (`rule_`). Skill do curator sinh giúp nhóm check nào? Check quy ước **mới** của tác vụ đánh giá có được skill giúp không, và vì sao?
3. Dựa vào vết và `skills_read`, giải thích một check mà skill giúp đạt và một check mà skill không giúp (skill chưa được đọc, đọc nhưng không làm theo, skill thiếu hoặc sai).
4. Chi phí: so sánh số token trung bình giữa các điều kiện. Điều kiện nào có hiệu quả tốt nhất theo điểm trên mỗi token? Đa tác tử có đáng chi phí trong thí nghiệm này không?
5. Có dấu hiệu rò rỉ dữ liệu hoặc quá khớp nào trong skill sinh ra không? Nhóm đã phòng tránh như thế nào?
6. Nhiễu: so sánh điểm tác vụ học của cùng bộ skill ở Phần 3.4 (đã sao lưu) và sau đóng băng. Chênh lệch bao nhiêu? Nó cho biết điều gì về độ tin cậy của các chênh lệch trong bảng ở mục 7?

## 9. Hạn chế và tính hợp lệ

> Nêu ít nhất 3 hạn chế và ảnh hưởng của từng hạn chế đến kết luận (ví dụ: chỉ 3 tác vụ mỗi vai trò, mỗi cấu hình chạy một lần, nhiễu của mô hình, tác vụ do giảng viên thiết kế sẵn quy ước, chỉ một mô hình).

1.
2.
3.

## 10. Kết luận

> Tối đa 5 câu. Chỉ khẳng định điều số liệu hỗ trợ. Nêu một đề xuất cải tiến tiếp theo.

## Phụ lục

- Lệnh đã chạy (theo thứ tự):
- Thử thách mở rộng (nếu có): hướng chọn, kết quả, nhận xét.
- Ghi chú khác:
