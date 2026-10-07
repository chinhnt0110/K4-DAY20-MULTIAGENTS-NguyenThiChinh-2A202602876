---
name: validate-function-annotations
description: Use this skill when defining public functions to ensure all parameters and return values have type annotations.
---
- Review each public function in your code.
- Ensure that every parameter has a type annotation.
- Ensure that the return value of the function has a type annotation.
- Use consistent and clear type hints (e.g., `List[str]`, `Optional[int]`).
- If using complex types, consider creating type aliases for clarity.
- Run a linter or type checker (like mypy) to verify that all functions comply with the type annotation rules.
- Document any exceptions or special cases in the function's docstring.
- Regularly review and update type annotations as the code evolves.
