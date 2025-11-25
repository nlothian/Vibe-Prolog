# ISO Prolog Coverage Map

## Status Legend
- ✅ **Implemented**: Fully compliant with ISO standard
- ⚠️ **Partial**: Implemented but with deviations or limitations
- ❌ **Missing**: Not implemented
- ❓ **Unknown**: Needs verification

## Built-in Predicates

### Control Constructs (ISO 7.8)
- ✅ `true/0` – Always succeeds
- ✅ `fail/0` – Always fails
- ✅ `,/2` – Conjunction (and)
- ✅ `;/2` – Disjunction (or)
- ✅ `->/2` – If-then-else
- ✅ `\+/1` – Negation as failure
- ✅ `!/0` – Cut operator

### Term Unification and Comparison (ISO 7.3, 8.4)
- ✅ `=/2` – Unification
- ✅ `\=/2` – Not unifiable
- ✅ `==/2` – Term identity (structural equality)
- ✅ `\==/2` – Term non-identity
- ✅ `@</2` – Term less than
- ✅ `@=</2` – Term less than or equal
- ✅ `@>/2` – Term greater than
- ✅ `@>=/2` – Term greater than or equal

### Type Testing (ISO 8.3)
- ✅ `var/1` – Test for unbound variable
- ✅ `nonvar/1` – Test for bound term
- ✅ `atom/1` – Test for atom
- ✅ `number/1` – Test for number (integer or float)
- ✅ `integer/1` – Test for integer
- ✅ `float/1` – Test for float
- ✅ `atomic/1` – Test for atomic term (atom or number)
- ✅ `compound/1` – Test for compound term
- ✅ `callable/1` – Test for callable term
- ✅ `ground/1` – Test for ground term (no variables)

### Term Manipulation (ISO 8.5)
- ✅ `functor/3` – Extract/construct functor name and arity
- ✅ `arg/3` – Access compound term arguments
- ✅ `=../2` – Term decomposition/construction (univ)
- ✅ `copy_term/2` – Create term copy with fresh variables

### Arithmetic Evaluation (ISO 9.1)
- ✅ `is/2` – Arithmetic evaluation
- ✅ `=:=/2` – Arithmetic equality
- ✅ `=\=/2` – Arithmetic inequality
- ✅ `</2` – Arithmetic less than
- ✅ `=</2` – Arithmetic less than or equal
- ✅ `>/2` – Arithmetic greater than
- ✅ `>=/2` – Arithmetic greater than or equal

### All Solutions (ISO 8.10)
- ✅ `findall/3` – Collect all solutions
- ✅ `bagof/3` – Collect solutions with duplicates
- ✅ `setof/3` – Collect unique sorted solutions

### Database Modification (ISO 8.9)
- ✅ `asserta/1` – Add clause at beginning
- ✅ `assertz/1` – Add clause at end
- ✅ `assert/1` – Add clause at end (equivalent to assertz/1)
- ✅ `retract/1` – Remove clause
- ✅ `abolish/1` – Remove all clauses for predicate
- ✅ `clause/2` – Retrieve clause definition

### Meta-Logical Predicates (ISO 7.8)
- ✅ `call/1` – Call goal dynamically
- ✅ `once/1` – Call goal, commit to first solution
- ✅ `setup_call_cleanup/3` – Execute goal with setup and cleanup
- ✅ `call_cleanup/2` – Execute goal with cleanup

### Exception Handling (ISO 7.12)
- ✅ `catch/3` – Exception handling with ISO error terms
- ✅ `throw/1` – Throw exception term
- ✅ ISO error term structure: `error(ErrorType, context(Predicate))`
- ✅ `instantiation_error` – Raised by built-ins when required arguments are unbound
- ✅ `type_error(Type, Culprit)` – Raised by built-ins when arguments have wrong types
- ✅ `domain_error(Domain, Culprit)` – Raised by built-ins when values are outside valid domains
- ✅ `syntax_error(Description)` – Parser throws ISO `error(syntax_error(_), _)` terms
- ❌ `existence_error(ObjectType, Culprit)` – Not implemented

### Input/Output (ISO 8.11-8.12)
- ✅ `write/1` – Write term
- ✅ `writeln/1` – Write term with newline
- ✅ `nl/0` – Write newline
- ✅ `format/2`, `format/3` – Formatted output
- ✅ `read_from_chars/2` – Parse term from character list/string
- ⚠️ `write_term_to_chars/3` – Write term to character list with options (basic implementation, operator handling incomplete)
- ❌ `read/1` – Read term from input
- ❌ `get_char/1` – Read character from input
- ❌ `put_char/1` – Write character to output
- ❌ `open/3` – Open file stream
- ❌ `close/1` – Close stream
- ✅ `current_input/1` – Get current input stream
- ✅ `current_output/1` – Get current output stream

### Predicate Inspection (ISO 8.8)
- ⚠️ `predicate_property/2` – Query predicate properties (limited to built-in detection)
- ✅ `current_predicate/1` – Enumerate defined predicates

### List Operations (Common Extensions)
- ✅ `member/2` – List membership
- ✅ `append/3` – List concatenation
- ✅ `length/2` – List length
- ✅ `reverse/2` – List reversal
- ✅ `sort/2` – List sorting with deduplication

### Higher-Order Operations (Common Extensions)
- ✅ `maplist/2` – Apply goal to list elements (SWI-Prolog extension, not ISO)
  - Streams goal solutions per element to preserve backtracking semantics

### System Predicates
- ✅ `argv/1` – Access command-line arguments as list
- ✅ `current_prolog_flag(argv, Args)` – ISO-style access to command-line arguments

## Directives (ISO 7.4)

### Program Directives
- ❌ `:- dynamic/1` – Declare dynamic predicate
- ❌ `:- multifile/1` – Declare multifile predicate
- ❌ `:- discontiguous/1` – Declare discontiguous predicate
- ✅ `:- initialization/1` – Specify initialization goal

### Operator Directives
- ❌ `:- op/3` – Define operator
- ❌ `:- char_conversion/2` – Define character conversion

## Syntactic Constructs (ISO 6)

### Terms
- ✅ Atoms (unquoted, quoted)
- ✅ Numbers (integers, floats, scientific notation)
- ✅ Variables
- ✅ Compound terms
- ✅ Lists (proper and improper)
- ✅ Character codes (`0'X`, `0'\n`, etc.)
- ✅ Character codes (`0'\\xHH\\` - hex escape syntax)

### Operators
- ✅ Arithmetic operators (`+`, `-`, `*`, `/`, `//`, `mod`, `**`)
- ✅ Comparison operators (`=`, `\=`, `=:=`, `=\=`, `<`, `=<`, `>`, `>=`)
- ✅ Control operators (`,`, `;`, `->`, `\+`, `!`)
- ✅ Term comparison operators (`==`, `\==`, `@<`, `@=<`, `@>`, `@>=`)

### Number Literals
- ✅ Decimal integers
- ✅ Binary (`0b`), octal (`0o`), hexadecimal (`0x`)
- ✅ Scientific notation
- ✅ Floating point
- ✅ Base-qualified numbers (`16'ff`, `2'abcd` - base'digits syntax)

### Comments
- ✅ Line comments (`%`)
- ✅ Block comments (`/* */`) - fully implemented with nesting support
- ✅ Nested block comments

### Special Syntax
- ✅ Curly braces `{Term}` (sugar for `{}(Term)`)
- ✅ List syntax `[H|T]`, `[Elements]`
- ✅ String syntax (double and single quoted)
- ✅ Operator syntax with proper precedence

## Execution Model
- ✅ Robinson-style unification
- ✅ Occurs check (prevents cyclic terms)
- ✅ Full backtracking search
- ✅ Dynamic clause enumeration
- ✅ Recursion handling
- ✅ Cut operator semantics
- ✅ If-then/else evaluates conditions lazily (only first success) to preserve backtracking
- ✅ Term comparison uses deterministic ordering (variables < numbers < atoms < compounds < lists) for deterministic sort/setof results
- ✅ List conversions honor active substitutions when traversing open list tails (e.g., append/sort/reverse)
- ✅ Python conversions reject improper or partially instantiated lists instead of silently truncating

## Error Handling
- ✅ ISO-style structured error terms (error(ErrorType, Context))
- ✅ Instantiation errors for unbound required arguments
- ✅ Type errors for incorrect argument types
- ✅ Domain errors for values outside valid domains
- ✅ Syntax errors for parse failures
- ✅ Error context with predicate information

## Data Types
- ✅ Atoms
- ✅ Integers (arbitrary precision via Python)
- ✅ Floats
- ✅ Variables
- ✅ Proper lists
- ✅ Improper lists
- ✅ Compound terms
- ✅ Empty list `[]` equivalent to `'[]'`

## High-Priority Gaps and Deviations

### Critical Missing Features
1. **File I/O**: Essential for practical Prolog programs
2. **Dynamic Declarations**: `dynamic/1`, `multifile/1` for module system
3. **Operator Definition**: `op/3` for custom operators
4. **Existence Errors**: `existence_error(ObjectType, Culprit)` not implemented

### Significant Deviations
1. **Error Reporting**: Now fully ISO-compliant with structured error terms and systematic error reporting in built-ins
2. **Character Code Syntax**: Some advanced character code forms not supported

### Parser Limitations
1. **Hex Character Codes**: `0'\xHH\` syntax now supported
2. **SWI-Style Dict Syntax**: `tag{a:1}` syntax not supported
3. **Operator Definition**: `:- op/3` directive rejected (not implemented)
4. **Unary Minus Precedence**: In some cases, unary minus may bind differently than expected (e.g., `-X + Y` parses as `-(X + Y)`)
