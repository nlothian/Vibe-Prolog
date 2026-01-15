# Goals

These goals are what we are working towards in this project:
- A complete, Scryer Prolog compatible Prolog implementation
- Robust: It should handle all kinds of error conditions gracefully
- Fast: It should run prolog programs fast
- Scalable: It should be able to run large prolog programs

# Coding rules
- Follow PEP 8 for Python code
  - **All imports must be at the top of the file** (after module docstring, before other code)
  - Never use `import` statements inside functions or methods
  - Group imports: standard library, third-party, local (separated by blank lines)
- Run all tests before pushing a PR
- Use type hints where helpful
- Add docstrings to all public methods
- Keep functions focused and testable
- Use descriptive variable names



# Prolog Interpreter - Development Guide

This document provides an overview of the project structure and guidelines for development and testing.

## Project Structure

See @docs/ARCHITECTURE.md

## Features

See @docs/FEATURES.md

You must keep ./docs/FEATURES.md up to date when you add or change these

## Documentation

**All new markdown documentation should go in @docs/** 

Standard documentation files:
- `@docs/ARCHITECTURE.md` - System architecture and design
- `@docs/FEATURES.md` - ISO Prolog conformance matrix and feature checklist
- Any additional documentation, guides, or specs should be added as new files within the `@docs/` directory.

## Error Handling 

Handle Prolog errors like this:
```python
   except PrologThrow:
      # Re-raise Prolog errors
      raise
   except Exception: # Or use a more specific Exception if possible
      # Unexpected errors - convert to evaluation error
      raise PrologThrow(PrologError.evaluation_error("error", f"{op}/2"))
```



## Testing Guidelines

### Where to Put Tests

**All test files must go in the `tests/` directory.**

- **Unit tests**: `test_<module>.py` - Tests for specific modules
- **Integration tests**: `test_<feature>.py` - Tests for features spanning multiple modules
- **Fixtures**: `*.pl` files - Prolog code used by tests


### Test File Naming

- Python test files: `test_*.py`
- Prolog fixtures: `test_*.pl` or descriptive names like `minimal_mi_test.pl`
- Follow pytest conventions


### Writing Tests

1. **Import the interpreter**:
   ```python
   from vibeprolog import PrologInterpreter
   ```

2. **Create a new interpreter for each test**:
   ```python
   def test_something():
       prolog = PrologInterpreter()
       # Your test code
   ```

3. **Use pytest test classes to organize related tests**:
   ```python
   class TestAppend:
       """Tests for append/3 predicate."""

       def test_append_two_lists(self):
           prolog = PrologInterpreter()
           result = prolog.query_once("append([1, 2], [3, 4], X).")
           assert result['X'] == [1, 2, 3, 4]
   ```

4. **Test both success and failure cases**:
   ```python
   def test_unification_success(self):
       prolog = PrologInterpreter()
       assert prolog.has_solution("X = 5")

   def test_unification_failure(self):
       prolog = PrologInterpreter()
       assert not prolog.has_solution("1 = 2")
   ```


### Running Tests

Always run tests in parallel. The are too slow otherwuse

```bash
# Run all tests
uv run pytest  -n auto

# Run all tests including performance (skipped by default). This is slow so run only when required.
uv run pytest --run-performance  -n auto

# Run all slow tests (tests empirically longer than ~4 seconds). Skip unless flag is present.
uv run pytest --run-slow-tests  -n auto

# Run specific test file
uv run pytest tests/test_builtins.py  -n auto

# Run specific test class
uv run pytest tests/test_builtins.py::TestAppend  -n auto

# Run specific test
uv run pytest tests/test_builtins.py::TestAppend::test_append_two_lists  -n auto

# Run with verbose output
uv run pytest -v  -n auto

# Run with output capture disabled (see print statements)
uv run pytest -s  -n auto
```

### Long-running tests

- When adding a new test that consistently takes longer than ~4 seconds, mark it with `@pytest.mark.performance` (or set `pytestmark = pytest.mark.performance` for whole classes/files) so it only runs when `--run-performance` is used.
- Document why the test is performance-marked in its docstring when the reason is not obvious.


## Development Workflow

This is Prolog implementation. The parser should parse standard prolog syntax. We follow what Scryer prolog does. 

### Adding a New Built-in

1. **Choose a module in `vibeprolog/builtins/`** that fits (e.g., `arithmetic.py`, `list_ops.py`, `type_tests.py`).
2. **Implement a static handler** with the signature `(args, subst, engine)` and annotate return types.
3. **Register the predicate** in the module's `register(registry, engine_ref=None)` using `register_builtin`.
4. **Write tests in `tests/`** covering success and failure cases.
5. **Update documentation** (`CLAUDE.md`/`FEATURES.md`) to reflect the new predicate.
6. **Run tests**:
   ```bash
   uv run pytest tests/test_new_builtins.py -v
   ```

> **Syntax errors**: When a built-in parses text (e.g., via `PrologParser` or `read_from_chars/2`) and the input might be malformed, wrap the parser call in `try/except (ValueError, LarkError)` and create an error term with `PrologError.syntax_error(str(exc), "predicate/arity")` then raise `PrologThrow(error_term)`. This ensures callers can intercept the ISO-style `error(syntax_error(_), Context)` term with `catch/3`.

### Debugging Tips

1. **Use print statements in built-ins**:
   ```python
   def _builtin_something(self, arg, subst):
       print(f"Debug: arg={arg}, subst={subst}")
       # ...
   ```

2. **Create minimal test cases**:
   - Start with the simplest possible query
   - Gradually add complexity
   - Put test files in `tests/` directory

3. **Check parser output**:
   ```python
   from vibeprolog.parser import PrologParser
   parser = PrologParser()
   result = parser.parse("your_query.")
   print(result)
   ```


## Developer Tools

The `tools/` directory contains utilities for analyzing Prolog code and identifying missing functionality.

### Check Operators (`tools/check_operators.py`)

Analyzes which operators are used in a Prolog file and compares them against what Vibe-Prolog supports.

**Usage:**
```bash
uv run python tools/check_operators.py <prolog_file>
```

**Example:**
```bash
uv run python tools/check_operators.py library/clpb.pl
```

**What it does:**
- Finds all operators used in the code
- Identifies operators declared in `:- op(...)` directives or module exports
- Categorizes operators as:
  - Supported (defined in `operator_defaults.py`)
  - Unsupported ISO operators (required by standard)
  - Unsupported non-ISO operators (extensions)
- Outputs a markdown report

**When to use:**
- Before implementing support for a new library
- To prioritize which operators to implement
- To understand operator dependencies
- To verify compliance

**Exit codes:**
- 0: All operators are supported
- 1: Some operators are missing

### Find Built-ins (`tools/find_builtins.py`)

Scans a directory of Prolog files to identify which predicates are called but not defined, indicating they're likely built-in predicates.

**Usage:**
```bash
uv run python tools/find_builtins.py <directory>
```

**Example:**
```bash
uv run python tools/find_builtins.py examples/
```

**What it does:**
- Parses all `.pl` files in the directory
- Identifies predicates that are called but not defined
- Categorizes predicates as:
  - Actual built-ins (registered in Vibe-Prolog)
  - Dynamic predicates (declared `:- dynamic` but asserted at runtime)
  - Undefined predicates (not built-in, not dynamic, not defined - might be missing)
- Shows which files use each predicate

**When to use:**
- To discover what built-ins are needed for a set of examples
- To identify missing implementations
- To prioritize built-in development
- To verify completeness of built-in coverage

**Note:** This tool identifies predicates, not operators. Operators are syntactic and checked by `check_operators.py`.

### ISO Conformity Testing (`tools/conformity_test.py`)

Tests Vibe-Prolog against the official ISO Prolog conformity test suite (355 tests).

**Usage:**
```bash
# Run all tests and generate report
uv run python tools/conformity_test.py

# Run specific tests
uv run python tools/conformity_test.py --tests 1-50

# Verbose output
uv run python tools/conformity_test.py --verbose
```

**When to use:**
- Before major releases to verify compliance
- After parser/syntax changes to catch regressions
- When investigating compatibility issues
- To track conformity improvements over time

**Output:** Generates `docs/CONFORMITY_TESTING.md` with detailed results.

## Resources

- ./docs/ISO_PROLOG_OPERATOR_SET.md
- ./docs/SCRYER_PROLOG_OPERATORS_SET.md
- [pytest Documentation](https://docs.pytest.org/) - Testing framework
- [Lark Parser](https://lark-parser.readthedocs.io/) - Parser generator used for Prolog syntax

## Contributing

1. Write tests first (TDD approach recommended)
2. Ensure all tests pass before committing
3. Update this documentation when adding features
4. Keep the codebase clean and well-organized
