# Simple Prolog Interpreter Architecture & Usage

A minimal yet capable Prolog interpreter in Python. This document combines
usage guides, architecture notes, testing guidance, and contributor-focused
context so you can reason about the system in one place.

## Project Structure

```
vibeprolog/
├── interpreter.py          # High-level PrologInterpreter interface
├── engine.py               # Core execution engine (~200 lines)
├── parser.py               # Prolog syntax parser
├── unification.py          # Unification algorithm
├── builtins/               # Built-in predicate implementations
│   ├── arithmetic.py
│   ├── control.py
│   ├── ...
└── utils/                  # Utility functions
    ├── term_utils.py
    ├── list_utils.py
    └── variable_utils.py
```

## Features & ISO Coverage

See `FEATURES.md` for the full checklist of ISO predicates and syntax features.
At the moment 102 entries in that matrix are marked ✅, covering ISO-style
parsing, unification, backtracking execution, and a broad set of built-ins. Use
that document to understand missing directives, error terms, and parser gaps.

## Usage

### Running the Demo

```bash
uv run vibeprolog.py
```

### Running Tests

```bash
uv run pytest        # all tests
uv run pytest -v     # verbose
uv run pytest tests/test_builtins.py
uv run pytest tests/test_parser.py
```

See the "Tooling & Tests" section for additional harness info.

### Using as a Library

```python
from vibeprolog import PrologInterpreter

prolog = PrologInterpreter()
prolog.consult_string("""
    parent(tom, bob).
    parent(tom, liz).
    grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
""")

results = prolog.query("grandparent(tom, Who)")
for result in results:
    print(f"Tom's grandchild: {result['Who']}")

result = prolog.query_once("parent(tom, X)")
if result:
    print(f"Tom's child: {result['X']}")

if prolog.has_solution("parent(tom, bob)"):
    print("Tom is bob's parent")
```

### Loading from Files

```python
prolog = PrologInterpreter()
prolog.consult("my_rules.pl")
results = prolog.query("my_query(X)")
```

## Architecture Overview

The interpreter consists of four main components:

1. **Parser** (`vibeprolog/parser.py`) - Uses Lark to parse Prolog syntax with full
    operator precedence, multi-base numeric literals (including base-qualified
    numbers like `16'ff`), quoted atoms/strings, escapes, and ISO character code
    forms (except for a handful of noted edge cases).
2. **Unification** (`vibeprolog/unification.py`) - Robinson-style unification with
   occurs-check by default so cyclic structures are prevented.
3. **Engine** (`vibeprolog/engine.py`) - Backtracking search with built-in
   predicates, cut semantics, dynamic predicate assertion/retraction, and the
   dispatcher that resolves functor/arity to handlers.
4. **Interpreter** (`vibeprolog/interpreter.py`) - Public API for loading and
   querying programs, plus helpers for consulting strings/files and capturing
   output streams.

## Built-in Registry

Built-ins live under `vibeprolog/builtins/` and register themselves via
`prolog.builtins.register_builtin`. Each module exposes a static `register`
method so the engine can populate its registry at startup. Handlers use the
signature `(args, subst, engine)` and can yield multiple substitutions for
non-deterministic predicates.

### Adding a New Built-in Predicate

1. **Choose the appropriate module** in `vibeprolog/builtins/`:
   - Arithmetic operations → `arithmetic.py`
   - List operations → `list_ops.py`
   - Type tests → `type_tests.py`
   - Control flow → `control.py`
   - Database → `database.py`
   - I/O → `io.py`
   - Term manipulation → `term_manipulation.py`
   - All-solutions → `all_solutions.py`
   - Exceptions → `exceptions.py`
   - Reflection → `reflection.py`
   - Higher-order → `higher_order.py`

2. **Add a static method** to the module's class:

   ```python
   @staticmethod
   def my_builtin(args: BuiltinArgs, subst: Substitution, engine: EngineContext) -> BuiltinResult:
       """my_builtin/N - Description."""
       # Implementation
   ```

3. **Register in the module's register() method**:

   ```python
   @staticmethod
   def register(registry: BuiltinRegistry, engine_ref=None):
       registry[("my_builtin", N)] = ModuleClass.my_builtin
   ```

4. **Add tests** in `tests/test_*.py`.
5. **Update FEATURES.md** to mark the predicate as implemented.

## Tooling & Tests

- Exercise the system primarily through the Python API (`from vibeprolog import
  PrologInterpreter`) and the pytest suite (800+ tests covering ISO core,
  parser pathologies, and built-in behaviors).
- `PrologInterpreter` exposes `consult/consult_string`, `query`, `query_once`,
  and `has_solution`, plus optional stdout capture so predicates like `write`
  and `format` can be observed while still returning substitutions.
- Built-in predicates are dispatched through the registry in
  `vibeprolog/engine.py`. To add one, register a handler that either yields
  substitutions or returns `None`. Helpers such as `_format_to_string`,
  `_list_to_python` (respects active substitutions), and `_fresh_variable`
  centralize tricky behavior so new built-ins stay consistent.

## Utility Modules

Shared helpers for the AST live in `vibeprolog/utils/`:

- `term_utils.py`: Formatting, comparison, and sorting helpers for terms.
- `list_utils.py`: Convert between Python and Prolog list forms; match/shape
  lists.
- `variable_utils.py`: Variable collection, copying, and existential stripping.

These modules are imported by `vibeprolog/engine.py` and have focused coverage in
`tests/utils/`.

## Examples

### Family Relationships

```prolog
parent(tom, bob).
parent(bob, ann).

grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :- parent(X, Z), ancestor(Z, Y).
```

### List Operations

```prolog
% member/2 is built-in
?- member(2, [1,2,3]).  % True
?- member(X, [a,b,c]).  % X = a ; X = b ; X = c
```

### Logic Puzzles

```prolog
person(alice).
person(bob).

job(alice, doctor).
job(bob, engineer).

% Who has which job?
?- job(Person, doctor).  % Person = alice
```

## Limitations

This interpreter intentionally focuses on ISO core features. Significant gaps
you should be aware of:

- File/stream I/O predicates (`see/1`, `read/1`, `open/3`, etc.) and character
  I/O helpers are stubbed or missing.
- Directive handling (`dynamic/1`, `multifile/1`, `op/3`, etc.) is not
  implemented, so programs that rely on dynamic declarations or custom
  operators are rejected.
- ISO error term infrastructure (`error(ErrorType, Context)` along with
  `instantiation_error`, `type_error`, etc.) still needs work; most built-ins
  fail silently instead of raising structured errors.
- A handful of parser edge cases remain unimplemented.
- No DCG, module system, CLP libraries, or tail-call optimization. Very deep
  recursion can still overflow Python's stack in pathological cases.

## Test Coverage Snapshot

As of 2025-11-23 the pytest suite reports `878 passed, 4 skipped` (out of 882
collected) via `uv run pytest`. The skips are parser stress cases that require
future ISO syntax additions; everything else (unification, type checks,
arithmetic, lists, control flow, meta-predicates) currently passes.
