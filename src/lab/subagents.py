"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    """Trả về danh sách subagent (ít nhất 2, tên khác nhau).

    Mỗi phần tử là một dict có các khóa bắt buộc:
      "name":          tên duy nhất (chữ thường, có thể có dấu gạch ngang)
      "description":   khi nào tác tử chính nên giao việc cho subagent này (viết như một hướng dẫn hành động)
      "system_prompt": chỉ dẫn cho subagent
    Gợi ý vai trò: explorer (đọc và báo cáo), implementer (thực hiện), reviewer (kiểm tra độc lập).
      explorer     - đọc README, docstring, mẫu dữ liệu; báo cáo sự thật; không sửa gì
      implementer  - thực hiện thay đổi, chạy test hoặc script, báo cáo kết quả
      reviewer     - kiểm tra độc lập kết quả theo đề bài và các trường hợp biên; không sửa
    """
    explorer = {
        "name": "explorer",
        "description": (
            "Delegate to this subagent to explore the workspace, inspect repository structure, "
            "read files (README, docstrings, configs, sample data), and gather facts. "
            "Never use to modify or create files."
        ),
        "system_prompt": (
            "You are an exploration subagent. Your role is strictly to read, inspect, and analyze "
            "the files and repository structure. Report factual observations, schemas, and requirements "
            "back to the main agent. Do NOT create, modify, or delete any files."
        ),
    }

    implementer = {
        "name": "implementer",
        "description": (
            "Delegate to this subagent when you need to write code, edit files, or execute commands "
            "and unit tests in the workspace. Provide complete instructions and context."
        ),
        "system_prompt": (
            "You are an implementation subagent. Your role is to perform changes to files, write scripts "
            "or code, and run tests or commands to verify your implementation. Report the exact actions "
            "taken, modifications made, and execution results back to the main agent."
        ),
    }

    reviewer = {
        "name": "reviewer",
        "description": (
            "Delegate to this subagent after implementation to independently verify the solution, "
            "check against all task rules and edge cases, and run validation tests. Do not use to edit code."
        ),
        "system_prompt": (
            "You are a code and quality reviewer subagent. Your role is to independently inspect "
            "the solution, verify compliance with all task requirements, detect subtle bugs or edge case "
            "failures, and run verification tests if needed. Report your findings and verdict back to "
            "the main agent. Do NOT modify any files."
        ),
    }

    return [explorer, implementer, reviewer]
    
