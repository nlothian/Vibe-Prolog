# ISO/IEC 13211-1 Prolog  — Conformance Tables

This documents a **minimal ISO Prolog conformance checklist**, organised by **ISO/IEC 13211-1 section**.

Status legend:

* ✅ Implemented
* ⚠️ Partial / Deviates from ISO
* ❌ Missing
* 📘 Extension (non-ISO, but compatible)

---

## §5–§6 — Prolog Text, Tokens, Syntax

| Feature                          | Status | Notes                                     |
| -------------------------------- | ------ | ----------------------------------------- |
| Atoms (quoted, unquoted)         | ✅      | Fully implemented; Unicode letters (Greek, Cyrillic, Arabic, CJK, etc.) supported in unquoted atoms |
| Variables                        | ✅      | ISO semantics                             |
| Numbers (int, float, scientific) | ✅      | Includes Edinburgh `<radix>'<number>` syntax (`16'ff`, `2'1010`, `36'ZZZ`) for bases 2-36; `0x`/`0X` prefix accepts case-insensitive hex digits (`0xFF`, `0xff`, `0xAbC`, `0X1a`); underscore digit grouping (`1_000_000`, `3.1415_9265`, `1_0.0e-5`) |
| Lists (proper, improper)         | ✅      |                                           |
| Compound terms                   | ✅      |                                           |
| Strings (quoted)                 | ✅      | ISO escapes (\a \b \c \d \e \f \n \r \s \t \v \0...\777 \x... \\x...\\ \uXXXX \' \" \\) with backslash-newline continuation; octal escapes accept up to three digits without a trailing backslash terminator (SWI-compatible, differs from Scryer) |
| `%` line comments                | ✅      |                                           |
| `/* … */` block comments         | ✅      | Treated as whitespace; nested supported; `/**` starts PlDoc comments; `/*` after graphic char is part of operator (e.g., `//*`) |
| Character code syntax (`0'X`)    | ✅      | ISO-compliant escapes (\x...\\, \uXXXX, octal, named), rejects \c and trailing characters, rejects empty literals |
| Built-in operator syntax         | ✅      |                                           |
| `:- op/3` declaration            | ✅      | Full support - defines operators dynamically |
| Directive prefix operator `:-` (1200, fx) | ✅ | **ISO-required** - Prefix form for directives |
| Custom operator syntax in source | ✅      | Parser dynamically generates grammar for custom operators (infix/prefix/postfix) |
| Parser/operator grammar cache | ✅📘 | Grammar + Earley parser cached per module/operator set; repeated directives/clauses reuse the cached parser instead of rebuilding the grammar |
| Query prefix operator `?-` (1200, fx) | ✅ | **ISO-required** - Reserved reader syntax; not redefinable via `op/3` |
| DCG rule operator `-->` (1200, xfx) | ✅    | **ISO-required** - DCG syntax |
| `:- char_conversion/2`           | ✅      | **ISO-mandatory** - Character conversion during parsing |
| Dot as clause terminator         | ✅      | Correctly ignores dots inside parentheses/brackets/braces |
| Dot as atom in expressions       | ✅      | Single `.` valid as atom argument (e.g., `upto_what(X, .)`) |
| Range operator `..`              | ✅      | `1..9` parses as `..(1, 9)` - used by CLP(Z) |
| Ellipsis `...`                   | ✅      | Three dots as atom/operator for DCG patterns |
| Operators as functor names (quoted) | ✅   | `';'(A, B)`, `'|'(X, Y)`, `':'(a, b)` work |
| Operators as functor names (unquoted) | ✅ | `;(A, B)`, `|(X, Y)`, `:(a, b)` work |
| Parenthesized operators as atoms | ✅      | `(;)`, `(|)`, `(,)`, `(->)` work |
| Bare `.` atom inside terms        | ✅      | Supports constructs like `phrase(upto_what(Bs0, .), Cs0, Ds)` |

---

## §6 — Program Structure & Execution

| Feature                         | Status | Notes                              |
| ------------------------------- | ------ | ---------------------------------- |
| Facts and rules                 | ✅      |                                    |
| Clause ordering                 | ✅      | Preserved                          |
| Predicate identity (Name/Arity) | ✅      |                                    |
| Depth-first SLD resolution      | ✅      |                                    |
| Backtracking                    | ✅      |                                    |
| Cut (`!/0`)                     | ✅      | Correct semantics                  |
| If-then-else (`->/2`)           | ✅      | Lazy condition                     |
| Negation as failure (`\\+/1`)   | ✅      |                                    |
| First-argument indexing         | ✅      | O(1) clause lookup for large DBs   |
| Occurs check                    | ⚠️     | Always enabled (stricter than ISO) |
| Recursion handling with depth limits | ✅      | Configurable recursion depth limit (default: 10,000); supports deep tail recursion |
| Operator import caching         | ✅📘    | Operator directives cached by path + mtime to avoid re-scanning transitive imports across consults/interpreters; import scanning uses a lightweight directive parser |
| Python recursion limit management | ✅      | Automatically increases Python's recursion limit to support Prolog depth |

---

## §7.4 — Directives

| Directive              | Status | Notes                                    |
| ---------------------- | ------ | ---------------------------------------- |
| `:- dynamic/1`         | ✅      |                                          |
| `:- multifile/1`       | ✅      |                                          |
| `:- discontiguous/1`   | ✅      |                                          |
| `:- initialization/1`  | ✅      |                                          |
| `:- op/3`              | ✅      | Full support - defines operators with validation |
| `:- char_conversion/2` | ❌      | **ISO-required**                         |
| `:- if(Condition)`     | ✅📘    | Conditional compilation - begin block    |
| `:- elif(Condition)`   | ✅📘    | Conditional compilation - else-if        |
| `:- else`              | ✅📘    | Conditional compilation - alternative block |
| `:- endif`             | ✅📘    | Conditional compilation - end block      |
| `:- char_conversion/2` | ✅      | **ISO-required** - Character conversion during parsing |

### Ignored Directives (Scryer-Prolog Specific)

The following Scryer-Prolog specific directives are recognized but ignored (with a warning):

| Directive | Purpose | Status |
|-----------|---------|--------|
| `:- non_counted_backtracking pred/N` | Inference counting hint | ⚠️ Ignored with warning |
| `:- meta_predicate(...)` | Module expansion hints | ⚠️ Ignored with warning |

---

## §7.8 — Control Constructs

| Predicate              | Status | Notes     |
| ---------------------- | ------ | --------- |
| `true/0`               | ✅      |           |
| `fail/0`               | ✅      |           |
| `,/2`                  | ✅      |           |
| `;/2`                  | ✅      |           |
| `->/2`                 | ✅      |           |
| `\\+/1`                | ✅      |           |
| `not/1`                | ✅📘    | Alias for `\\+/1` (negation-as-failure) |
| `not_/1`               | ✅📘    | Alias for `\\+/1` to support custom operator names |
| `!/0`                  | ✅      |           |
| `call/1`               | ✅      |           |
| `once/1`               | ✅      |           |
| `setup_call_cleanup/3` | ✅📘    | Extension |
| `call_cleanup/2`       | ✅📘    | Extension |

---

## §7.3 / §8.4 — Unification & Term Comparison

| Predicate / Rule                 | Status | Notes                                                                                                    |
| -------------------------------- | ------ | -------------------------------------------------------------------------------------------------------- |
| `=/2`                            | ✅      |                                                                                                          |
| `\\=/2`                          | ✅      |                                                                                                          |
| `==/2`                           | ✅      |                                                                                                          |
| `\\==/2`                         | ✅      |                                                                                                          |
| `@</2`, `@=</2`, `@>/2`, `@>=/2` | ✅      |                                                                                                          |
| `compare/3`                      | ✅      | **ISO-required** - Three-way term comparison                                                             |
| `unify_with_occurs_check/2`      | ✅      | **ISO-required** - Logically sound unification                                                           |
| ISO standard term order          | ✅      | Lists now correctly ordered as compounds                                                                 |

---

## §8.3 — Type Testing

| Predicate    | Status | Notes                                |
| ------------ | ------ | ------------------------------------ |
| `var/1`      | ✅      |                                      |
| `nonvar/1`   | ✅      |                                      |
| `atom/1`     | ✅      |                                      |
| `number/1`   | ✅      |                                      |
| `integer/1`  | ✅      |                                      |
| `float/1`    | ✅      |                                      |
| `atomic/1`   | ✅      |                                      |
| `compound/1` | ✅      |                                      |
| `callable/1` | ✅      |                                      |
| `ground/1`   | ✅      |                                      |
| `is_list/1`  | ✅      | Common extension (de facto standard); supports Atom('[]') as list terminator |

---

## §8.5 — Term Creation and Decomposition

| Predicate           | Status | Notes                   |
| ------------------- | ------ | ----------------------- |
| `functor/3`         | ✅      |                         |
| `arg/3`             | ✅      |                         |
| `=../2` (univ)      | ✅      |                         |
| `copy_term/2`       | ✅      |                         |
| `term_variables/2`  | ✅      | **ISO-required**        |
| `numbervars/3`      | ✅      | Common extension        |
| `subsumes_term/2`   | ✅      | ISO extension (Part 2)  |

---

## §8.16 — Atom Processing

| Predicate        | Status | Notes                                    |
| ---------------- | ------ | ---------------------------------------- |
| `atom_length/2`  | ✅      | **ISO-required**                         |
| `atom_concat/3`  | ✅      | **ISO-required**                         |
| `sub_atom/5`     | ✅      | **ISO-required**                         |
| `atom_chars/2`   | ✅      | **ISO-required** (needed for DCG examples) |
| `atom_codes/2`   | ✅      | **ISO-required**                         |
| `char_code/2`    | ✅      | **ISO-required**                         |
| `number_chars/2` | ✅      | **ISO-required**                         |
| `number_codes/2` | ✅      | **ISO-required**                         |
| `name/2`         | 📘      | Classic Prolog extension (pre-ISO)       |

---

## §9 — Arithmetic

| Feature                           | Status | Notes                                 |
| --------------------------------- | ------ | ------------------------------------- |
| `is/2`                            | ✅      |                                       |
| Arithmetic comparison operators   | ✅      |                                       |
| Arithmetic evaluation: `+/2`, `-/2`, `*/2`, `//2`, `///2`, `mod/2`, `div/2` | ✅      | **ISO-required** - Used within `is/2` |
| Integer division: `div/2`         | ✅      | **ISO-required** - Operator available   |
| Unary operators: `-/1`, `+/1`     | ✅      | **ISO-required** - Negation and plus  |
| Power operators: `^/2`, `**/2`    | ✅      | **ISO-required** - Operators available     |
| `abs/1`                           | ✅      |                                       |
| `min/2`, `max/2`                  | ✅      |                                       |
| `sqrt/1`                          | ✅      |                                       |
| Trig / exp / log                  | ✅      |                                       |
| `floor/1`, `ceiling/1`, `round/1` | ✅      |                                       |
| `rem/2`                           | ✅      | **ISO-required** - Integer remainder  |
| Bitwise AND: `/\`                 | ✅      | **ISO-required** - Operator available   |
| Bitwise OR: `\/`                  | ✅      | **ISO-required** - Operator available   |
| Bitwise complement: `\`           | ✅      | **ISO-required** - Operator available   |
| Bitwise shift: `<<`, `>>`         | ✅      | **ISO-required** - Operators available  |
| `between/3`                       | ✅      | **ISO-required** - Integer generation |
| `succ/2`                          | ✅      | **ISO-required** - Successor relation |
| `plus/3`                          | ✅      | **ISO-required** - Addition relation  |
| `divmod/4`                        | ✅      | Common extension                      |

---

## List Operations (ISO §8.5.3 + Common Extensions)

| Predicate               | Status | Notes                                         |
| ----------------------- | ------ | --------------------------------------------- |
| `append/3`              | ✅      |                                               |
| `member/2`              | ✅      |                                               |
| `length/2`              | ✅      |                                               |
| `reverse/2`             | ✅      |                                               |
| `sort/2`                | ✅      |                                               |
| `msort/2`               | ✅      | **ISO-required** - Sort keeping duplicates    |
| `keysort/2`             | ✅      | **ISO-required** - Sort Key-Value pairs       |
| `nth0/3`, `nth1/3`      | ✅      | Common extension - Access by index            |
| `last/2`                | ✅      | Common extension                              |
| `select/3`              | ✅      | Common extension - Select element             |
| `memberchk/2`           | ✅      | Common extension - Deterministic member       |
| `sumlist/2`             | ✅      | Common extension                              |
| `max_list/2`            | ✅      | Common extension                              |
| `min_list/2`            | ✅      | Common extension                              |
| `is_set/1`              | ✅      | Common extension - Test if list has no duplicates |
| `list_to_set/2`         | ✅      | Common extension - Remove duplicates          |
| `list_to_ord_set/2`     | ✅      | Common extension - Convert to ordered set     |
| `ord_subtract/3`        | ✅      | Common extension - Ordered set difference     |
| `numlist/3`             | ✅      | Common extension - Generate list of integers  |
| `permutation/2`         | ✅      | Common extension - Generate permutations      |
| `maplist/3-5`           | ✅      | Higher-order                                  |
| `include/3`             | ✅      | Higher-order - Filter list                    |
| `exclude/3`             | ✅      | Higher-order - Filter list (negated)          |
| `partition/4`           | ✅      | Higher-order - Split list by condition        |
| `foldl/4-6`             | ✅      | Higher-order - Fold left                      |

---

## §8.10 — All-Solutions Predicates

| Predicate   | Status | Notes                  |
| ----------- | ------ | ---------------------- |
| `findall/3` | ✅      |                        |
| `bagof/3`   | ✅      | Correct quantification |
| `setof/3`   | ✅      | ISO semantics          |

## §8.14 — Definite Clause Grammars (DCGs)

| Predicate / Feature          | Status | Notes                                                                 |
| ---------------------------- | ------ | --------------------------------------------------------------------- |
| DCG syntax (`-->`)           | ✅      | **ISO-required** - Full DCG syntax support                           |
| `phrase/2`                   | ✅      | **ISO-compliant** - Complete list consumption with error handling    |
| `phrase/3`                   | ✅      | **ISO-compliant** - Remainder support with error handling            |
| Terminal lists as rulesets   | ✅      | `phrase([a, b, c], L)` unifies L with [a, b, c]                       |
| Cut (`!`) as ruleset         | ✅      | `phrase(!, L)` unifies L with []                                      |
| DCG expansion                | ✅      | Automatic conversion to standard Prolog clauses                       |
| DCG variable goals           | ✅      | Variables can be used as terminal sequences: `foo --> { X = [a,b] }, X.` |
| Embedded Prolog goals `{G}`  | ✅      | Full support for embedded goals in DCG rules                         |
| Alternatives (`;`)           | ✅      | Choice points in DCG rules                                           |
| Error handling               | ✅      | **ISO-compliant** - Proper instantiation_error, type_error, existence_error |

---

## Meta-Predicates & Control Flow Extensions

| Predicate   | Status | Notes                               |
| ----------- | ------ | ----------------------------------- |
| `forall/2`  | ✅      | Common extension - Universal quantification |
| `ignore/1`  | ✅      | Common extension - Always succeed   |
| `apply/2`   | ✅      | Common extension - Call with args   |

---

## §8.9 — Dynamic Program Modification

| Predicate / Rule                       | Status | Notes                                                               |
| -------------------------------------- | ------ | ------------------------------------------------------------------- |
| Static by default                      | ⚠️     | Semantics implemented; additional cross-module test coverage needed |
| `asserta/1`                            | ✅      |                                                                     |
| `assertz/1`                            | ✅      |                                                                     |
| `assert/1`                             | ✅      |                                                                     |
| `retract/1`                            | ✅      |                                                                     |
| `retractall/1`                         | ✅      | **ISO-required** - Retracts all clauses whose heads unify with Head |
| `abolish/1`                            | ✅      |                                                                     |
| `clause/2`                             | ✅      |                                                                     |
| Permission errors on static predicates | ⚠️     | Enforced, but requires further validation across modules            |

---

## §8.11 — Character Input/Output

| Predicate       | Status | Notes                            |
| --------------- | ------ | -------------------------------- |
| `get_char/1-2`  | ✅      |                                  |
| `put_char/1-2`  | ✅      |                                  |
| `get_code/1-2`  | ✅      | **ISO-required**                 |
| `put_code/1-2`  | ✅      | **ISO-required**                 |
| `get/1-2`       | ✅      | **ISO-required** - Skip whitespace |
| `put/1-2`       | ✅📘    | **ISO-required** - Write character code or single-character atom (SWI-Prolog compatible) |
| `peek_char/1-2` | ✅      | **ISO-required** - Look ahead    |
| `peek_code/1-2` | ✅      | **ISO-required** - Look ahead    |
| `peek_byte/1-2` | ✅      | **ISO-required**                 |
| `get_byte/1-2`  | ✅      | **ISO-required**                 |
| `put_byte/1-2`  | ✅      | **ISO-required**                 |
| `nl/0-1`        | ✅      |                                  |

---

## §8.12 — Term Input/Output

| Predicate               | Status | Notes                            |
| ----------------------- | ------ | -------------------------------- |
| `read/1-2`              | ✅      |                                  |
| `read_term/2-3`         | ✅      | **ISO-required** - With options  |
| `write/1-2`             | ✅      |                                  |
| `writeq/1-2`            | ✅      | **ISO-required** - With quotes   |
| `write_canonical/1-2`   | ✅      | **ISO-required** - Canonical form|
| `write_term/2-3`        | ✅      | **ISO-required** - With options  |
| `print/1-2`             | ✅      | Common extension                 |
| `writeln/1-2`           | ✅      | Extension                        |
| `format/2-3`            | ✅📘    | Extension                        |
| `write_term_to_chars/3` | ⚠️     | Minor formatting differences     |

---

## §8.13 — Stream Selection and Control

| Predicate                | Status | Notes                        |
| ------------------------ | ------ | ---------------------------- |
| `open/3-4`               | ✅      |                              |
| `close/1-2`              | ✅      |                              |
| `current_input/1`        | ✅      |                              |
| `current_output/1`       | ✅      |                              |
| `set_input/1`            | ✅      | **ISO-required**             |
| `set_output/1`           | ✅      | **ISO-required**             |
| `flush_output/0-1`       | ✅      | **ISO-required**             |
| `at_end_of_stream/0-1`   | ✅      | **ISO-required** - EOF test  |
| `stream_property/2`      | ✅      | **ISO-required**             |
| `set_stream_position/2`  | ✅      | **ISO-required** - Seek      |

## Classic I/O Predicates (Edinburgh Style)

| Predicate | Status | Notes                                      |
| --------- | ------ | ------------------------------------------ |
| `see/1`   | ✅      | Classic input redirection                  |
| `seen/0`  | ✅      | Close classic input                        |
| `tell/1`  | ✅      | Classic output redirection                 |
| `told/0`  | ✅      | Close classic output                       |

---

## §7.12 — Errors & Exceptions

| Feature                                                           | Status | Notes                                        |
| ----------------------------------------------------------------- | ------ | -------------------------------------------- |
| `throw/1`                                                         | ✅      |                                              |
| `catch/3`                                                         | ✅      |                                              |
| `instantiation_error`                                             | ✅      |                                              |
| `type_error/2`                                                    | ✅      |                                              |
| `domain_error/2`                                                  | ✅      |                                              |
| `permission_error/3`                                              | ✅      | Enforced consistently for most predicates    |
| `existence_error/2`                                               | ✅      |                                              |
| `syntax_error/1`                                                  | ✅      |                                              |
| `resource_error/2`                                                | ✅      | Recursion depth exceeded                      |
| Arithmetic errors (`zero_divisor`, `undefined`, `float_overflow`) | ✅      | Full ISO-compliant arithmetic error handling |

---

## §8.8 — Reflection

| Predicate                             | Status | Notes                   |
| ------------------------------------- | ------ | ----------------------- |
| `current_predicate/1`                 | ✅      | Module-qualified indicators (`module:Name/Arity`) supported |
| `predicate_property/2`                | ⚠️     | Built-in detection only |
| `dynamic/static/multifile` properties | ❌      | Needed for ISO tooling  |

---

## Attributed Variables (SICStus/Scryer Style)

Attributed variables are the foundation for constraint logic programming. They allow metadata to be attached to unbound variables, and hooks to be called when those variables are unified.

| Feature | Status | Notes |
|---------|--------|-------|
| `:- attribute(Name/Arity)` directive | ✅ | Declare attributes in module |
| `put_atts/2` | ✅ | Set/remove attributes on variables |
| `get_atts/2` | ✅ | Query attributes on variables |
| `attvar/1` | ✅ | Test if variable has attributes |
| `term_attvars/2` | ✅ | Find all attributed variables in a term |
| `copy_term/3` | ✅ | Copy term with attributes as goals |
| `del_atts/1` | ✅ | Delete all attributes from a variable |
| `verify_attributes/3` hook | ✅ | Called on attributed variable unification |
| `library(atts)` | ✅ | Module providing attributed variable predicates |
| `term_residual_goals/2` | ✅ | Collect residual goals from attributed variables |
| `project_attributes/2` | ✅ | Project constraints onto query variables |
| `attribute_goals//1` hook | ✅ | Module hook for custom goal representation |
| `library($project_atts)` | ✅ | Internal module for residual goal projection |

**Usage example:**
```prolog
:- use_module(library(atts)).

% Define a verify_attributes hook for constraint checking
verify_attributes(Var, Value, []) :-
    get_atts(Var, domain(Domain)),
    member(Value, Domain).

% Use attributed variables
?- put_atts(X, +domain([a, b, c])), X = b.
X = b.
```

---

## SWI-Prolog Specific Extensions (Non-ISO)

These predicates are specific to SWI-Prolog and not part of the ISO standard.

| Category | Predicates | Status | Notes |
| -------- | ---------- | ------ | ----- |
| **Networking** | `tcp_socket/1`, `tcp_connect/4` | 🚫 Won't Implement | SWI-specific socket operations - out of scope |
| **DDE (Windows)** | `open_dde_conversation/3`, `close_dde_conversation/1`, `dde_request/3`, `dde_execute/2`, `dde_poke/3`, `dde_register_service/2` | 🚫 Won't Implement | Windows Dynamic Data Exchange - obsolete technology |
| **CLP(Z)** | `#=/2`, `#</2`, `#>/2`, `#=</2`, `#>=/2`, `ins/2`, `in/2`, etc. | 📘 | Constraint Logic Programming over Integers - Implemented in [library/clpz.pl](../library/clpz.pl) (8041 lines, Markus Triska) - **Requires library(atts)** |
| **CLP(B)** | `sat/1`, `taut/2`, `labeling/1`, Boolean operators | 📘 | Constraint Logic Programming over Booleans - Implemented in [library/clpb.pl](../library/clpb.pl) (1970 lines, Markus Triska) - **Requires library(atts)** |
| **Tabling** | `:- table/1` directive | ✅ | Variant tabling with memoized answers |
| **CHR** | `:- chr_constraint/1` | ❌ | Constraint Handling Rules |
| **RDF** | `:- rdf_meta/1` | 🔽 Low Priority | RDF (Resource Description Framework) support - specialized use case |
| **Random** | `random/1` | ❌ | Random number generation (non-ISO) |

---

## Tabling (Memoization)

Basic variant tabling is available via the `:- table` directive.

| Feature | Status | Notes |
| --- | --- | --- |
| `:- table pred/arity` | ✅ | Declare predicates for memoized execution |
| Variant-based caching | ✅ | Calls with identical shapes reuse cached answers |
| Multiple predicate indicators | ✅ | `:- table foo/1, bar/2.` supported |

---

## §10 — Modules (ISO Part 1)

| Feature                           | Status | Notes                                                          |
| --------------------------------- | ------ | -------------------------------------------------------------- |
| `:- module/2`                     | ✅      |                                                                |
| Module-qualified calls (`M:Goal`) | ✅      |                                                                |
| Export enforcement                | ✅      |                                                                |
| Built-ins visible in all modules  | ✅      |                                                                |
| Clause body module resolution     | ✅      | Unqualified goals resolve via imports → defining module → user |
| `use_module/1,2`                  | ✅      | Supports full and selective imports, including `library(Name)`; library/ preferred over examples/modules/ for module resolution |
| `consult/1` with `library(Name)`  | ✅      | `consult("library(dcgs)")` resolves via library search paths just like `use_module/1` |
| Parsed module cache               | ✅📘    | Parsed directives/clauses cached per interpreter using resolved path, operator table version, char conversions, conditional stack, and file mtime to avoid redundant parsing |
| **Operator exports in module/2**  | ✅      | **SWI-Prolog compatible - operators can be exported**          |
| Imported operator discovery       | ✅      | Two-pass parsing: operators from `use_module` targets are pre-scanned and registered before parsing dependent code. Handles block comments, line comments, and recursive imports |
| **Module-scoped predicate namespaces** | ✅  | Each module can define predicates with the same name/arity without conflict. `library(a):foo/1` and `library(b):foo/1` are distinct |
| **DCG predicate indicators**      | ✅📘    | SWI-Prolog extension: `Name//Arity` in module exports (expanded to `Name/Arity+2`) |
| **Module-qualified clause heads** | ✅      | `Module:Head :- Body` syntax for cross-module predicate definitions (e.g., `user:goal_expansion/2`) |
| **Module-qualified predicate directives** | ✅  | `Module:Name/Arity` syntax in `dynamic/1`, `multifile/1`, `discontiguous/1` directives for cross-module predicate property declarations (e.g., `:- discontiguous user:goal_expansion/2`) |
| **Invalid export indicators**     | ⚠️📘    | Scryer-Prolog extension: Invalid predicate indicators (e.g., control constructs like `!/0`) in export lists are skipped with a warning rather than causing a type error |
| Cross-module dynamic semantics    | ⚠️     | Implemented; dynamic predicate isolation per module needs further work |

---

## ISO Conformance Snapshot

| Category                  | Status                                                     |
| ------------------------- | ---------------------------------------------------------- |
| Core execution model      | ✅ Strong                                                   |
| Control constructs        | ✅ Strong                                                   |
| Unification & comparison  | ✅ Strong                                                   |
| Type testing              | ✅ Strong                                                   |
| Term manipulation         | ✅ Strong                                                   |
| Atom processing (§8.16)   | ✅ Strong                                                   |
| Arithmetic                | ✅ Strong                                                   |
| List operations           | ✅ Strong - Including higher-order predicates (maplist, foldl, include, exclude) |
| All-solutions             | ✅ Strong                                                   |
| Meta-predicates           | ✅ Strong - Including higher-order list operations          |
| Database operations       | ✅ Strong - All ISO-required predicates implemented         |
| Character I/O (§8.11)     | ✅ Strong - All ISO-required predicates implemented         |
| Term I/O (§8.12)          | ✅ Strong - All ISO-required predicates implemented        |
| Stream control (§8.13)    | ✅ Strong - All ISO-required predicates implemented        |
| Errors & exceptions       | ✅ Strong                                                   |
| Parsing & syntax          | ✅ Strong - op/3 ✅, custom operator syntax parsing ✅, ISO operators ✅, prefix `:-` ✅, char_conversion ✅ |
| Modules                   | ✅ Largely ISO-consistent (Part 1)                          |
| Reflection                | ⚠️ Partial                                                 |

---

## ISO Blocking Issues

_No blocking issues remain. All ISO-required syntax features are now implemented._

## Common Extensions Status

Common extensions frequently used in real-world Prolog programs:

1. **List utilities** - ✅ Implemented: `is_set/1`, `list_to_set/2`, `list_to_ord_set/2`, `ord_subtract/3`, `numlist/3`, `permutation/2`
2. **Higher-order** - ✅ Implemented: `maplist/3-5`, `include/3`, `exclude/3`, `partition/4`, `foldl/4-6`
3. **Constraint solving** - 📘 Available as libraries: CLP(Z) in [library/clpz.pl](../library/clpz.pl), CLP(B) in [library/clpb.pl](../library/clpb.pl)

---

## ISO Conformity Testing

Vibe-Prolog is tested against the official ISO/IEC JTC1 SC22 WG17 conformity test suite:
- 355 test cases covering syntax, operators, escapes, and numeric literals
- Results tracked in [docs/CONFORMITY_TESTING.md](./CONFORMITY_TESTING.md)
- Tests can be re-run with `uv run python tools/conformity_test.py`

Current conformity: Run `uv run python tools/conformity_test.py` to see current results

---

## Command-Line Interface

The Vibe-Prolog CLI supports both interactive and batch modes, with optional program file loading.

### Interactive Mode Without Files

Unlike many Prolog systems that require a program file, Vibe-Prolog allows starting interactive mode without loading any files:

```bash
# Start interactive REPL without any loaded program
uv run vibeprolog.py

# Execute queries directly without file loading
uv run vibeprolog.py -q "member(X, [1,2,3])"
```

This matches the behavior of standard Prolog systems like SWI-Prolog and Scryer-Prolog.

### File Loading (Optional)

Program files can still be loaded as before:

```bash
# Load and start interactive mode
uv run vibeprolog.py examples.pl

# Load and execute query
uv run vibeprolog.py examples.pl -q "my_predicate(X)"
```

## Command-Line Options

### `--builtin-conflict` Flag

Controls how the interpreter handles library definitions that conflict with built-in predicates.

**Syntax:**
```
--builtin-conflict=MODE
```

**Modes:**

| Mode | Behavior |
|------|----------|
| `skip` | **(Default)** Silently skip the library definition and use the existing built-in. Allows libraries like `clpz` to load without errors. |
| `error` | Raise a `permission_error` when a library tries to redefine a built-in predicate. Useful for strict checking and debugging library compatibility. |
| `shadow` | Allow a module to define a predicate that shadows a built-in within that module's namespace. Module-qualified calls use the module's definition; unqualified calls from user context use the built-in. |

**Examples:**

Skip mode (default):
```prolog
% Program tries to define length/2
:- module(my_lib, [length/2]).
length([], custom_zero).
length([_|T], s(N)) :- length(T, N).

?- length([a, b], L).  % Uses built-in: L = 2
```

Shadow mode:
```prolog
% Same program with --builtin-conflict=shadow
:- module(my_lib, [length/2]).
length([], custom_zero).
length([_|T], s(N)) :- length(T, N).

?- my_lib:length([a, b], L).  % Uses module version: L = s(s(custom_zero))
?- length([a, b], L).         % Uses built-in: L = 2
?- user:length([a, b], L).    % Uses built-in: L = 2
```

When importing a shadowed predicate:
```prolog
:- use_module(my_lib, [length/2]).
?- length([a, b], L).  % Uses imported shadow: L = s(s(custom_zero))
```

### Operator Shadowing

The `shadow` mode is particularly important for CLP (Constraint Logic Programming) libraries like `clpz` and `clpb` that need to redefine the `|` operator with extended semantics for constraint programming.

**Protected Operators:**

The following operators are protected and require `shadow` mode to redefine:
- `,` (conjunction)
- `;` (disjunction)
- `->` (if-then)
- `:-` (clause/directive)
- `:` (module qualification)
- `|` (list/constraint syntax)
- `{}` (curly braces)

**Key Characteristics:**
- Module-scoped shadowing: Protected operators can be redefined within a module's scope without affecting global behavior
- List syntax preservation: Shadowing `|` does not break standard list syntax `[H|T]`
- Independent modules: Multiple modules can independently shadow the same operator
- Global protection: Protected operators cannot be modified at global scope even in shadow mode

**Example - Loading CLP libraries:**
```bash
# Load clpz with shadow mode to allow | operator redefinition
uv run vibeprolog.py --builtin-conflict=shadow my_program.pl
```

```prolog
:- use_module(library(clpz)).
?- X in 1..10, X #> 5, label([X]).  % CLP constraint programming works
?- Y = [a, b | [c]].                % Standard list syntax still works: Y = [a, b, c]
```

### `--run-slow-tests` Flag

Controls whether pytest includes the subset of tests that currently take longer than ~4 seconds.

```
uv run pytest --run-slow-tests
```

These slow tests are skipped by default so the typical fast feedback loop remains snappy; enable the flag when you need to validate the heavy operator-import and fixture cases that power the performance/memory safety guarantees.
