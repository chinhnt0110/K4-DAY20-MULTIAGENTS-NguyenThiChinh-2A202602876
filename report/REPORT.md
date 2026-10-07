# Báo cáo Lab: Self evolving Agentic

## 1. Thông tin nhóm và cấu hình

| Họ tên | Mã sinh viên | Phần đóng góp |
|---|---|---|
| Nguyễn Thị Chinh| 2A202602876 | Toàn bộ |

- Nhà cung cấp và mô hình (`LAB_MODEL`, không ghi khóa API), nhiệt độ (`LAB_TEMPERATURE`), `recursion_limit`: OpenAI gpt-4o-mini, LAB_TEMPERATURE=0, recursion_limit=40
- Phiên bản Deep Agents (`pip show deepagents`), hệ điều hành, chạy trực tiếp hay trong Docker: `deepagents==0.7.21`, macOS, chạy trực tiếp trong môi trường ảo conda
- Số lần chạy tác vụ đã dùng / ngân sách: ≥ 22 / 30 (21 lần lưu trong `results/`, gồm cả 3 lần `skills-auto-dev`, cộng 1 lần `baseline` `data-learn` bị ghi đè ở mục 7)
- Commit của tag `freeze`: `cc317f0`

## 2. Giả thuyết (commit TRƯỚC tag `freeze`, Phần 4.0)

- H1 (subagents so với baseline): Điều kiện `subagents` sẽ đạt điểm tương đương hoặc chỉ nhỉnh hơn không đáng kể so với `baseline` trên tác vụ đánh giá, nhưng sẽ tiêu tốn lượng token cao hơn (dự kiến tăng 1.5 - 2.5 lần). Căn cứ: từ quan sát ở Phần 2.3, tác tử chính thường tự thực hiện hoặc khi ủy quyền thì subagent bị cô lập ngữ cảnh (`context isolation`), không nắm được các quy ước ngầm nên không giúp cải thiện các check `rule_`.
- H2 (skills-auto so với baseline): Điều kiện `skills-auto` có thể cải thiện điểm nếu tác vụ đánh giá tình cờ dùng chung một số quy ước lập trình chuẩn (như type hints hay changelog), nhưng mức cải thiện tổng thể trên tác vụ đánh giá sẽ thấp do hiện tượng quá khớp (overfitting). Căn cứ: nghiên cứu SkillsBench và SkillEvolBench ghi nhận skill do LLM tự sinh trung bình không mang lại lợi thế vượt trội trên tác vụ mới ngoài miền học.
- H3 (tác vụ học so với tác vụ đánh giá): Điểm số trên tác vụ học sẽ cao hơn tác vụ đánh giá ở điều kiện `skills-auto`, thể hiện rõ khoảng cách tổng quát hóa (generalization gap). Căn cứ: Curator được cung cấp phản hồi lỗi trực tiếp từ các check thất bại của tập học nên nội dung skill phản ánh sát các quy ước của tập học; trong khi đó tác vụ đánh giá chứa các yêu cầu và quy ước mới mà Curator chưa từng nhìn thấy.

## 3. Làm quen Deep Agents (Phần 0.3)

1. Tác tử mặc định có những công cụ nào? Công cụ nào cho phép chạy lệnh?
   - Tác tử mặc định có các công cụ: nhóm công cụ tệp (`ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`), shell (`execute`) và subagents (`task`).
   - Công cụ cho phép chạy lệnh là `execute`.

2. Mô tả của công cụ `task` nói gì về subagent `general-purpose`? Subagent đó nhìn thấy ngữ cảnh nào của tác tử chính?
   - Mô tả của công cụ `task` chỉ rõ subagent `general-purpose` dùng để nghiên cứu các vấn đề phức tạp đòi hỏi nhiều ngữ cảnh, tìm kiếm file và nội dung nhưng không chắc chắn sẽ tìm thấy kết quả ở lần thử đầu tiên, cũng như thực thi các tác vụ nhiều bước.
   - Subagent không nhìn thấy ngữ cảnh của tác tử chính: mô tả công cụ `task` ghi mỗi lần gọi là *stateless*, subagent chỉ thấy prompt được giao và trả về một báo cáo cuối. Nó có cùng bộ công cụ với tác tử chính, nên mọi thông tin cần thiết phải nằm trong prompt giao việc.

3. System prompt mặc định của Deep Agents rỗng. Trích một câu hướng dẫn hành vi từ mô tả của công cụ `task` và một câu từ mô tả của công cụ `execute`.
   - `task`: *"Launch multiple agents concurrently when their tasks are independent, using a single message with multiple tool calls."*
   - `execute`: *"Quote paths containing spaces (e.g. cd "/path/with spaces")"*

## 4. Đường cơ sở và phân loại lỗi (Phần 2.2)

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


> Bảng chỉ liệt kê các check thất bại tiêu biểu của lần chạy `baseline` trên tác vụ học: `data-learn` thất bại 7/8 check, `code-learn` 5/10, `logs-learn` 9/9 (không qua check nào).

**Nhận xét:**
1. **Nhóm lỗi chiếm đa số:** Nhóm **E (Vi phạm quy ước tổ chức ngầm `rule_*`)** chiếm tỷ lệ lớn nhất trên cả 3 tác vụ. Đây là các quy ước nội bộ đặc thù của tổ chức Acme không có trong prompt/README của đề bài mà chỉ có review bot kiểm tra.
2. **Khả năng phòng ngừa của Skill:** Một skill do Curator sinh ra **hoàn toàn có thể phòng ngừa nhóm lỗi E**, vì skill có thể đóng gói các quy ước tổ chức ngầm này thành quy tắc hướng dẫn hành động (ví dụ: luôn viết `meta` block, chuyển tiền sang cents, thêm type hint và cập nhật `CHANGELOG.md`).
3. **Bằng chứng phủ định cho các nhóm kỹ thuật (A-D):** Đối với các tác vụ thuần kỹ thuật như `code-learn`, mô hình gpt-4o-mini thực hiện tốt hầu hết các yêu cầu cơ bản (đạt 5/7 check kỹ thuật, cả 3 check `rule_*` đều trượt; hai check kỹ thuật trượt là `parse_price_all_formats` và `csv_quoting_follows_docstring`). Các lỗi ở nhóm A-D chủ yếu xảy ra khi dữ liệu có trường hợp biên phức tạp (`(12.00)`) hoặc khi tác tử vội vàng kết luận do thiếu thư viện (`data-learn`).

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
| `validate-function-annotations` | **Tổng quát**: Hướng dẫn thêm type hint cho mọi tham số và giá trị trả về của hàm công khai, không chứa tên file hay ID tác vụ cụ thể. | **Đúng**: Cung cấp checklist kiểm tra type hint chuẩn mực cho Python. | • Độ dài: 12 dòng.<br>• `description`: *"Use this skill when defining public functions to ensure all parameters and return values have type annotations."*<br>• `skills_read`: **0** |
| `ensure-test-coverage` | **Tổng quát**: Hướng dẫn viết unit test cho các hàm sửa đổi/thêm mới, bao phủ các trường hợp biên và kiểm tra test pass. | **Đúng nhưng chưa đủ cụ thể**: Quy trình viết test tốt, độc lập với bài toán; có nhắc "một test cho mỗi bug" nhưng không nêu tên file `tests/test_regressions.py` hay yêu cầu tối thiểu 3 test như `rule_regression_tests`. | • Độ dài: 14 dòng.<br>• `description`: *"Use this skill when making changes to code to ensure that adequate tests are created or updated."*<br>• `skills_read`: **0** |
| `maintain-changelog` | **Bán tổng quát**: Đóng gói quy ước định dạng `- fix(<function name>): <short description>` dưới mục `## Unreleased` trong `CHANGELOG.md` (học từ phản hồi của check `rule_changelog`). | **Đúng, kèm vài dòng thừa**: Có đúng mục `## Unreleased` và định dạng bullet; các dòng như "cập nhật số phiên bản" là nội dung chung chung do mô hình thêm vào, không xuất phát từ check nào. | • Độ dài: 12 dòng.<br>• `description`: *"Use this skill when making changes to code to ensure that all modifications are documented in the changelog."*<br>• `skills_read`: **0** |

**Nhận xét việc dùng skill (Phần 3.4):**
- Qua quan sát `trace.md`, ở lượt hành động đầu tiên, tác tử chính tập trung ngay vào việc điều tra nguyên nhân lỗi code/data trong `workspace/` (gọi `glob` và `read_file` trên code) mà không chủ động gọi `read_file` trên các file trong `skills/`.
- Điều này phản ánh đặc tính thực tế: dù system prompt có khuyến khích đọc skill trước (`SKILLS_NOTE`), mô hình ngôn ngữ vẫn có xu hướng ưu tiên giải quyết trực diện nhiệm vụ chính khi `description` chưa đủ hấp dẫn để kích hoạt việc tra cứu tri thức bên ngoài.


## 7. Kết quả so sánh (Phần 4.3, 4.4)

### Bảng tổng hợp kết quả (`report/table.md`)

| Task | baseline | subagents | skills-auto |
|---|---|---|---|
| code-learn | 5/10 | 5/10 | 6/10 |
| data-learn | 1/8 | 1/8 | 0/8 |
| logs-learn | 0/9 | 0/9 | 0/9 |
| code-eval | 1/11 | 3/11 | 1/11 |
| data-eval | 0/9 | 0/9 | 3/9 |
| logs-eval | 1/10 | 1/10 | 0/10 |
| **Mean score - learning tasks** | 0.21 | 0.21 | 0.20 |
| **Mean score - evaluation tasks** | 0.06 | 0.12 | 0.14 |
| **Mean tokens per run** | 75,963 | 55,450 | 96,629 |
| **Runs that read a skill** | 0/6 | 0/6 | 0/6 |

### Phân rã kỹ thuật và quy ước (`python scripts/check_breakdown.py`)

| Điều kiện | Vai trò | Check kỹ thuật | Quy ước (`rule_*`) | Token trung bình | Số lần đọc skill |
|---|---|---|---|---|---|
| `baseline` | `eval` | 2/18 | 0/12 | 111,099 | 0/3 |
| `baseline` | `learn` | 6/18 | 0/9 | 40,827 | 0/3 |
| `subagents` | `eval` | 4/18 | 0/12 | 59,905 | 0/3 |
| `subagents` | `learn` | 6/18 | 0/9 | 50,994 | 0/3 |
| `skills-auto` | `eval` | 4/18 | 0/12 | 90,844 | 0/3 |
| `skills-auto` | `learn` | 6/18 | 0/9 | 102,414 | 0/3 |

**Các lần chạy có `error`** (cả 7 đều là `GraphRecursionError` ở `recursion_limit=40`; kết quả được chấm trên workspace dở dang):

| Lần chạy | Token | Điểm |
|---|---|---|
| `baseline` / `code-eval` | 128,361 | 1/11 |
| `baseline` / `data-eval` | 187,091 | 0/9 |
| `subagents` / `code-eval` | 116,130 | 3/11 |
| `skills-auto` / `code-eval` | 141,983 | 1/11 |
| `skills-auto` / `logs-eval` | 117,331 | 0/10 |
| `skills-auto` / `data-learn` | 198,296 | 0/8 |
| `skills-auto-dev` / `data-learn` | 247,943 | 0/8 |

Nghĩa là 5/9 lần chạy đánh giá và 1/9 lần chạy học trong bảng chính bị cắt giữa chừng; `code-eval` bị cắt ở cả ba điều kiện. Tôi giữ nguyên các lần chạy này (không chạy lại để chọn kết quả đẹp hơn) và coi đây là một nguồn nhiễu, xem mục 9.

**Sự cố đã xử lý:** Lần chạy đầu của `baseline` trên `data-learn` với `recursion_limit=60` bị `GraphRecursionError` do vòng lặp gọi công cụ khi thiếu `pandas` (~385k token). Sau khi đặt `--recursion-limit 40` theo GUIDE.md, lần chạy lại hoàn thành sau 13.7s, 25,637 token, `error: null`; lần chạy đầu bị ghi đè nên không còn trong `results/`.

**Kiểm tra `skills_modified`:** cả 21 lần chạy lưu trong `results/` đều có `skills_modified: false`, và `verify_freeze.py` báo `checked 6 runs of skill conditions: OK`.

## 8. Phân tích

1. **So sánh điểm tác vụ học và đánh giá giữa các điều kiện:**
   - Trên **tác vụ học**: Điểm trung bình ở cả 3 điều kiện gần như tương đương: `baseline` = 0.21, `subagents` = 0.21, `skills-auto` = 0.20. Không có điều kiện nào tạo ra sự đột phá rõ rệt trên tập học. Cụ thể, `skills-auto` cải thiện nhẹ ở `code-learn` (tăng từ 5/10 lên 6/10) nhưng lại bị 0/8 ở `data-learn` do lỗi đệ quy.
   - Trên **tác vụ đánh giá**: Cả hai điều kiện mở rộng đều ghi nhận điểm trung bình cao hơn so với baseline: `subagents` = 0.12 (đạt 3/11 ở `code-eval`), `skills-auto` = 0.14 (đạt 3/9 ở `data-eval`), so với `baseline` chỉ đạt 0.06.
   - **Lưu ý**: 5/9 lần chạy đánh giá bị `GraphRecursionError` (mục 7), nên điểm đánh giá là điểm của workspace dở dang chứ không phải của một lần giải hoàn chỉnh.
   - **Dấu hiệu**: Không xuất hiện hiện tượng "tăng điểm học nhưng sụt giảm điểm đánh giá" (dấu hiệu của overfitting nặng). Tuy nhiên, vì số lần đọc skill `skills_read = 0/6`, sự khác biệt về điểm ở tập đánh giá chủ yếu phản ánh tính ngẫu nhiên (nhiễu) trong quá trình khám phá không gian lời giải của mô hình chứ chưa chứng minh được hiệu quả nhân quả của skill.

2. **Phân tách check kỹ thuật và check quy ước (`rule_`):**
   - Theo kết quả từ `check_breakdown.py`:
     - **Check quy ước tổ chức (`house rules`)**: Đạt **0/12 ở tập eval** và **0/9 ở tập learn** trên TOÀN BỘ cả 3 điều kiện thí nghiệm. Mặc dù Curator sinh ra 3 skill nhằm thẳng vào các quy ước (type hints, changelog, regression tests), nhưng do tác tử không đọc các skill này (`read a skill = 0/3`), điểm số quy ước vẫn bằng 0 tuyệt đối.
     - **Check kỹ thuật**: Điểm số hoàn toàn đến từ nhóm này. Ở tập eval, `baseline` đạt 2/18, trong khi `subagents` và `skills-auto` đều đạt 4/18.
     - **Check quy ước mới của tác vụ đánh giá**: Hoàn toàn không được skill hỗ trợ vì: (1) Curator chỉ học từ phản hồi của tác vụ học, không thể biết trước quy ước mới của eval; (2) Tác tử không tra cứu thư mục `skills/` trong quá trình thực thi.

3. **Giải thích cơ chế qua vết và `skills_read`:**
   - **Check mà skill không giúp được**: Check `rule_type_hints` và `rule_changelog` ở `code-learn` (điều kiện `skills-auto`). Vết `trace.md` cho thấy tác tử dùng `glob` và `read_file` trực tiếp vào mã nguồn trong `workspace/inventory/`, phát hiện lỗi logic giá trị và sửa chữa, sau đó chạy test và kết thúc. Tác tử hoàn toàn không gọi `read_file` trên `skills/validate-function-annotations/SKILL.md` hay `skills/maintain-changelog/SKILL.md` (`skills_read = 0`), dẫn đến việc bỏ qua toàn bộ yêu cầu bổ sung type hint và changelog.
   - **Check đạt độc lập với skill**: `data-eval` đạt 3/9 ở `skills-auto` so với 0/9 ở `baseline`. `skills_read = 0`, và vết cho thấy tác tử chỉ đọc `orders.json`, `README.md` rồi chạy một script `python3 -c` bằng thư viện chuẩn (3 tool calls, 12.8s, 13,220 token). Script đạt `top_category`, `missing_total_orders`, `duplicate_events_removed` nhưng trượt hai check tháng 3 và cả 4 check `rule_*`. Khác biệt với `baseline` chủ yếu là `baseline` bị `GraphRecursionError` (187,091 token) và không để lại kết quả, nên đây là khác biệt về việc có hoàn thành hay không, không phải tác dụng của skill.

4. **Phân tích chi phí token và hiệu quả:**
   - **Token trung bình mỗi lần chạy**: `subagents` 55,450 (thấp nhất), `baseline` 75,963, `skills-auto` 96,629 (cao nhất, +27% so với `baseline`).
   - **Nguyên nhân chênh lệch là số lần chạy bị lặp đệ quy, không phải điều kiện**: `baseline` có 2, `subagents` có 1, `skills-auto` có 3 lần chạy đạt giới hạn đệ quy (mỗi lần 116k đến 198k token). Nếu bỏ các lần đó, token trung bình lần lượt là 35,082 (`baseline`, 4 lần), 43,314 (`subagents`, 5 lần) và 40,723 (`skills-auto`, 3 lần), tức ba điều kiện gần nhau, `subagents` thậm chí nhỉnh hơn `baseline`.
   - **Hiệu quả điểm trên token**: Không đủ cơ sở xếp hạng, vì thứ hạng token phụ thuộc vào số lần lặp đệ quy ngẫu nhiên.
   - **Đa tác tử có đáng chi phí không?**: Tác tử chính hầu như không ủy quyền (`subagent_calls` = 1 ở `data-learn`, 0 ở 20 lần chạy còn lại). Khi có ủy quyền, chi phí tăng ~2.4 lần (25,637 lên 61,141 token) mà điểm không đổi (1/8), nên trong lab này subagent chưa chứng minh được giá trị.

5. **Rò rỉ dữ liệu và quá khớp (Data Leakage & Overfitting):**
   - **Rò rỉ dữ liệu**: Hoàn toàn không xảy ra. Lệnh kiểm tra `python scripts/verify_freeze.py` đã xác nhận không có bất kỳ marker nào của tập đánh giá (`eval_markers`) xuất hiện trong các file skill. Quá trình chọn lọc trong `curate_skills` đã cô lập triệt để: chỉ quét các thư mục có `role == "learn"`.
   - **Quá khớp**: 3 skill sinh ra mang tính quy trình chuẩn (viết test, chú thích kiểu, cập nhật nhật ký thay đổi). Tuy nhiên, do tác tử không chủ động đọc skill lúc runtime, hiện tượng quá khớp tri thức không gây ảnh hưởng tiêu cực lên hành vi của tác tử ở tập eval.

6. **Đo lường độ nhiễu (Noise Estimation):**
   - Điểm tác vụ học ở Phần 3.4 (`results/skills-auto-dev`):
     - `code-learn`: 3/10 (0.30)
     - `data-learn`: 0/8 (0.00)
     - `logs-learn`: 1/9 (0.11)
     - $\rightarrow$ Điểm trung bình: **0.137** (~0.14)
   - Điểm tác vụ học sau khi đóng băng (`results/skills-auto`):
     - `code-learn`: 6/10 (0.60)
     - `data-learn`: 0/8 (0.00)
     - `logs-learn`: 0/9 (0.00)
     - $\rightarrow$ Điểm trung bình: **0.200**
   - **Mức độ chênh lệch**: $\Delta = +0.063$ (chênh lệch tới 46% so với ban đầu trên cùng một bộ skill đã đóng băng và cùng cấu hình mô hình).
   - **Ý nghĩa khoa học**: Sự dao động đáng kể này chứng minh **độ nhiễu nội tại (stochastic variance) của LLM khi chạy mẫu đơn ($n=1$) là rất lớn**. Do đó, sự chênh lệch điểm số giữa các điều kiện (ví dụ 0.06 ở baseline so với 0.12 ở subagents hay 0.14 ở skills-auto) nằm trong biên độ dao động ngẫu nhiên của mô hình, không thể khẳng định một cách tuyệt đối rằng điều kiện này vượt trội hơn điều kiện kia nếu chưa thực hiện lặp lại nhiều lần.

## 9. Hạn chế và tính hợp lệ

1. **Cỡ mẫu tác vụ nhỏ ($N=3$ mỗi vai trò):** Mỗi điều kiện chỉ được kiểm thử trên 3 tác vụ học và 3 tác vụ đánh giá. Kích thước mẫu quá nhỏ làm hạn chế ý nghĩa thống kê và khiến điểm số trung bình nhạy cảm mạnh với kết quả của từng tác vụ đơn lẻ.
2. **Số lần lặp lại cho mỗi cấu hình là $n=1$:** Thí nghiệm không chạy lặp lại nhiều lần (do giới hạn ngân sách API). Như đã chứng minh ở mục 8.6, độ nhiễu của cùng một cấu hình có thể lên tới $\pm 0.06$, dẫn đến rủi ro quy kết sai lệch nguyên nhân tăng/giảm điểm.
3. **Quy ước ngầm của tổ chức (`rule_*`) mang tính nhân tạo:** Các quy ước như chuyển tiền sang cents hay bắt buộc có khối `meta` không có trong mô tả đề bài mà chỉ có review bot kiểm tra. Điều này khiến tác tử mặc định 100% thất bại ở các check này nếu không có cơ chế ép buộc đọc skill.
4. **Nhiều lần chạy bị cắt bởi `recursion_limit=40`:** 6/18 lần chạy trong bảng chính (và 1 lần `skills-auto-dev`) kết thúc bằng `GraphRecursionError`, riêng 5/9 lần chạy đánh giá. Điểm của các lần này là điểm của workspace dở dang và token của chúng chi phối trung bình token (mục 8.4), nên so sánh điểm và token giữa điều kiện kém tin cậy hơn con số bề mặt. Giới hạn 40 có thể thấp hơn mức cần để hoàn thành các tác vụ code/data.
5. **Chỉ một mô hình nhỏ (`gpt-4o-mini`):** Kết luận về việc tác tử bỏ qua `skills/` có thể không áp dụng cho mô hình mạnh hơn.
6. **Vấn đề kích hoạt đọc Skill (Skill Retrieval Activation):** Mặc dù system prompt đã thêm chỉ dẫn `SKILLS_NOTE`, mô hình ngôn ngữ vẫn ưu tiên tương tác trực tiếp với file bài toán trong `workspace/` thay vì đọc `skills/` ở bước đầu tiên, dẫn đến việc tri thức tiến hóa của Curator không được đưa vào luồng suy luận runtime.

## 10. Kết luận

1. Điểm trung bình trên tác vụ đánh giá là 0.06 (`baseline`), 0.12 (`subagents`) và 0.14 (`skills-auto`). Mức chênh này nhỏ hơn độ nhiễu đo được: cùng bộ skill đóng băng, điểm tác vụ học đổi từ 0.137 sang 0.200 giữa hai lần chạy; thêm vào đó 5/9 lần chạy đánh giá bị cắt bởi giới hạn đệ quy. Với n=1, chưa thể kết luận điều kiện nào tốt hơn.
2. Check `rule_*` đạt 0/12 ở tập đánh giá và 0/9 ở tập học, trên cả ba điều kiện. Tác tử không đọc skill nào (`skills_read` = 0), nên chưa có bằng chứng 3 skill của curator có tác dụng; phần điểm tăng của hai điều kiện mở rộng chỉ đến từ check kỹ thuật (4/18 so với 2/18 của `baseline`).
3. `verify_freeze.py` không tìm thấy marker của tập đánh giá trong skill, và điểm học không tăng trong khi điểm đánh giá giảm, nên không có dấu hiệu rò rỉ hay quá khớp.
4. Chênh lệch token (55,450 / 75,963 / 96,629) chủ yếu do số lần chạy lặp đệ quy (1 / 2 / 3 lần); bỏ các lần đó thì cả ba điều kiện nằm trong khoảng 35k đến 43k token. Subagent hầu như không được dùng (1/21 lần chạy) nên chưa đánh giá được lợi ích của đa tác tử.
5. Đề xuất tiếp theo: đưa nội dung skill thẳng vào prompt (hoặc buộc đọc `skills/` trước khi làm), tăng `recursion_limit` hoặc thêm điều kiện dừng, rồi chạy mỗi cấu hình ít nhất 3 lần để tách tác dụng của skill khỏi nhiễu.

## Phụ lục

- **Lệnh đã chạy (theo thứ tự):**
  1. `pytest tests/test_01_provided.py` (kiểm tra môi trường ban đầu)
  2. `python scripts/tour.py` (khảo sát Deep Agents mặc định)
  3. `pytest tests/test_02_agent.py` & `pytest tests/test_03_runner.py` (kiểm thử harness hoàn thiện)
  4. `python -m lab.runner --condition baseline --tasks data-learn --recursion-limit 40`
  5. `python -m lab.runner --condition baseline --tasks code-learn logs-learn --recursion-limit 40`
  6. `python -m lab.runner --condition subagents --tasks learn --recursion-limit 40`
  7. `pytest tests/test_04_curator.py` & `python -m lab.curator` (sinh skill tự động)
  8. `python -m lab.runner --condition skills-auto --tasks learn --recursion-limit 40`
  9. `mv results/skills-auto results/skills-auto-dev` (sao lưu Phần 3.4)
  10. `git add -A && git commit -m "hypotheses"`
  11. `git add -A && git commit --allow-empty -m "freeze skills" && git tag freeze`
  12. `python -m lab.runner --condition baseline --tasks eval --recursion-limit 40`
  13. `python -m lab.runner --condition subagents --tasks eval --recursion-limit 40`
  14. `python -m lab.runner --condition skills-auto --tasks all --recursion-limit 40`
  15. `python scripts/verify_freeze.py` (xác thực quy trình đóng băng)
  16. `python -m lab.compare > report/table.md` & `python scripts/check_breakdown.py` (tổng hợp bảng và phân rã chỉ số)
- **Thử thách mở rộng (nếu có):** Không thực hiện.
- **Ghi chú khác:** Đã xử lý sự cố đệ quy trên tác vụ `data-learn` bằng cách hạ `--recursion-limit 40` và chuẩn hóa múi giờ ISO `+00:00` trong `run_task` để đồng bộ hoàn hảo với Git timestamp.
