---
name: pytest-testing
description: 'Expertise in writing high-quality, rigorous Python tests using pytest. Use this skill when writing or reviewing tests, ensuring meaningful assertions, proper fixture usage, and comprehensive edge-case handling.'
---

# High-Quality Pytest Testing

This skill guides the creation of robust, maintainable, and high-quality tests using `pytest`. It enforces strict standards to prevent weak tests, meaningless assertions, and poor test architecture.

## When to Use

- Writing new unit or integration tests for Python code.
- Modifying or reviewing existing tests.
- Setting up pytest fixtures or parameterizations.
- Debugging failing tests or improving test coverage.

## Core Principles

1. **Meaningful Assertions Only**: Never write tests that just assert `True`, `is not None`, or check that a function simply runs without raising an error (unless explicitly testing execution safety). Assert specific data states, correct mutations, and precise return values.
2. **Arrange, Act, Assert (AAA)**: Strictly structure every test logically. 
3. **Isolate State**: Tests should not share mutable state. Use localized fixtures instead of global variables.
4. **Test Behavior, Not Implementation**: Avoid over-mocking. If you must mock, mock at the boundaries, not the internals.

## Available scripts

- **`scripts/run_pytest.sh`** — Wrapper to execute `pytest` using strict defaults. Separates diagnostics to `stderr` and test results to `stdout`.

## Procedure

### 1. Structure and Naming
- Name tests descriptively to indicate the scenario and expected outcome: `test_<function/method>_<scenario>_<expected_result>`.
  - *Good*: `test_calculate_total_with_empty_cart_returns_zero`
  - *Bad*: `test_calculate_total`
- Keep tests focused. A single test should ideally verify one logical behavior.

### 2. High-Quality Assertions
- Assert exact expected output states or rich properties.
- When comparing collections, assert on specific elements, lengths, or use exact dictionary/list comparisons.
- For floating-point arithmetic, use `pytest.approx`.
- **Exception Testing**: When testing errors, always assert the exact exception type AND the error message.
  ```python
  import pytest

  def test_divide_by_zero_raises_value_error():
      with pytest.raises(ValueError, match=r"Cannot divide by zero"):
          divide(10, 0)
  ```

### 3. Effective Fixture Usage
- Use `pytest.fixture` to handle setup and teardown cleanly. 
- Avoid using `setup_method` or `setUp` from `unittest` style.
- Scope fixtures appropriately (e.g., `scope="session"` for expensive DB setup, default `function` scope for isolated state).
- Use `yield` inside fixtures to safely tear down resources even if the test fails.

### 4. Parameterization for Coverage
- Use `pytest.mark.parametrize` to test multiple inputs and edge cases without duplicating test logic.
  ```python
  @pytest.mark.parametrize("input_val, expected", [
      (0, 0),
      (1, 1),
      (-1, -1),
  ])
  def test_identity(input_val, expected):
      assert identity(input_val) == expected
  ```

### 5. Mocking (If needed)
- Use `unittest.mock.patch` or `pytest-mock` (`mocker` fixture) carefully.
- Assert that mocks are called with the exact expected arguments using `mock.assert_called_once_with(...)`.

### 6. Executing Tests
Always use the bundled script to run tests. It enforces the project's `uv` environment and applies strict defaults.
```bash
bash scripts/run_pytest.sh tests/
```
*(Use `bash scripts/run_pytest.sh --help` for additional options like `--fail-fast` and `--quiet`)*.

## Completion Checklist
- [ ] Are the assertions rigorous? (No `assert result is not None` unless justified).
- [ ] Is `pytest.raises` used with a `match` argument for exceptions?
- [ ] Are tests properly isolated and stateless?
- [ ] Is test data covered thoroughly using `pytest.mark.parametrize`?
- [ ] Is the AAA (Arrange, Act, Assert) pattern visually clear?