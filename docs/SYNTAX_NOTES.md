# Vibe-Prolog Syntax Notes

This document provides detailed notes on Vibe-Prolog's syntax features, including extensions, deviations, and compatibility considerations.

## Number Literal Formats

### Decimal Numbers

| Format | Example | Value | Status | Notes |
|--------|---------|-------|--------|-------|
| Integer | `42`, `-17` | 42, -17 | ✅ Supported | Not applicable |
| Float | `3.14`, `-0.5` | 3.14, -0.5 | ✅ Supported | - |
| Scientific notation | `1.5e-3`, `2E10` | 0.0015, 20000000000 | ✅ Supported | - |
| Underscore grouping | `1_000_000` | 1000000 | ✅ Supported | Same as Scryer & SWI |
| Space grouping | `1 000 000` | — | ❌ Not supported | SWI-only extension |

**Recommendation**: prefer digits (optionally with underscores) and avoid SWI-only spacing syntax so code runs on all three systems (see [docs/GRAMMAR_COMPARISON.md](./GRAMMAR_COMPARISON.md)).

### Hexadecimal Numbers

| Format | Example | Value | Status | Notes |
|--------|---------|-------|--------|-------|
| `0x` prefix (any case) | `0xff`, `0xFF`, `0xFf` | 255 | ✅ Supported | Mirrors Scryer & SWI |
| Edinburgh `<radix>'<number>` | `16'ff'`, `16'FF'` | 255 | ✅ Supported | SWI-compatible; Scryer rejects |

**Compatibility notes**:
- Hex digits are case-insensitive for the `0x` prefix syntax, matching the behavior documented in [GRAMMAR_COMPARISON.md](./GRAMMAR_COMPARISON.md).
- Edinburgh-style literals remain case-sensitive to the digits supplied and are portable only between Vibe and SWI (Scryer treats them as syntax errors).

**Recommendation**:
- For code shared across Vibe, Scryer, and SWI, prefer the `0x` notation, e.g., `0xFF`.
- Use Edinburgh `<radix>'<number>` only when you explicitly target Vibe + SWI or need bases beyond hexadecimal.

### Octal Numbers

| Format | Example | Value | Status |
|--------|---------|-------|--------|
| `0o` prefix | `0o77`, `0o755` | 63, 493 | ✅ Supported |
| Edinburgh <radix>'<number> | `8'77'`, `8'755'` | 63, 493 | ✅ Supported |

### Binary Numbers

| Format | Example | Value | Status |
|--------|---------|-------|--------|
| `0b` prefix | `0b101`, `0b1010` | 5, 10 | ✅ Supported |
| Edinburgh <radix>'<number> | `2'101'`, `2'1010'` | 5, 10 | ✅ Supported |

### Arbitrary Base Numbers (Edinburgh Extension)

Vibe-Prolog supports the Edinburgh `<radix>'<number>` notation for bases 2-36:

| Format | Example | Value | Status |
|--------|---------|-------|--------|
| Base 2-36 | `36'ZZZ'` | 46655 | ✅ Supported |
| Base validation | `37'ABC'` | N/A | ❌ Error: invalid base |
| Base 1 or 0 | `1'123'`, `0'456'` | N/A | ❌ Error: invalid base |

**Digit validation**: The parser ensures digits are valid for the specified base (e.g., `8'99'` is an error because `9` is not valid in octal).

### Character Code Literals

| Format | Example | Value | Status | Notes |
|--------|---------|-------|--------|-------|
| Basic | `0'a`, `0'Z` | 97, 90 | ✅ Supported | Single character |
| Escape sequences | `0'\n`, `0'\t`, `0'\r` | 10, 9, 13 | ✅ Supported | Standard escapes |
| Hex escape | `0'\x41` | 65 | ✅ Supported | No terminator needed |
| Backslash | `0'\\` | 92 | ✅ Supported | Escaped backslash |
| Single quote | `0'\'` | 39 | ✅ Supported | Escaped quote |
| Double quote | `0'\"` | 34 | ✅ Supported | Escaped quote |
| Empty | `0''` | N/A | ❌ Rejected | Syntax error as per ISO |

**Difference from Scryer-Prolog**: Vibe does not require a trailing backslash for hex/octal escapes.

## String and Atom Syntax

### Quoted Atoms

| Feature | Example | Result | Status |
|---------|---------|--------|--------|
| Single quotes | `'atom'` | atom | ✅ Supported |
| Spaces in atoms | `'hello world'` | hello world | ✅ Supported |
| Escaped quotes | `'it''s'` | it's | ✅ Supported |
| Backslash escape | `'\\'` | \ | ✅ Supported |
| Newline escape | `'\n'` | (newline) | ✅ Supported |
| Tab escape | `'\t'` | (tab) | ✅ Supported |
| Hex escape | `'\x48ello'` | Hello | ✅ Supported |
| Operators as atoms | `';'`, `','`, `'|'` | (operators) | ✅ Supported |

### Double-Quoted Strings

| Mode | Example | Result | Status |
|------|---------|--------|--------|
| Atom mode (default) | `"hello"` | atom: hello | ✅ Supported |
| Same escapes as atoms | `"hello\nworld"` | atom with newline | ✅ Supported |

**Note**: Unlike Scryer-Prolog, Vibe does not have configurable `double_quotes` flag for code/char list modes.

### Escape Sequences

| Escape | Meaning | Example | Status |
|--------|---------|---------|--------|
| `\'` | Single quote | `'it\'s'` or `'it''s'` | ✅ Supported |
| `\"` | Double quote | `"say \"hi\""` | ✅ Supported |
| `\\` | Backslash | `'\\'` | ✅ Supported |
| `\n` | Newline (LF) | `'\n'` | ✅ Supported |
| `\r` | Carriage return (CR) | `'\r'` | ✅ Supported |
| `\t` | Tab | `'\t'` | ✅ Supported |
| `\xHH` | Hex character code | `'\x41'` (A) | ✅ Supported |
| `\OOO\` | Octal character code | `'\101\'` (A) | ✅ Supported |

**Missing from Scryer-Prolog**:
- `\a` (alert/bell) - not supported in Vibe
- `\b` (backspace) - not supported in Vibe
- `\v` (vertical tab) - not supported in Vibe
- `\f` (form feed) - not supported in Vibe

### Special Atom Cases

| Feature | Example | Status | Notes |
|---------|---------|--------|-------|
| Bare dot atom | `phrase(upto_what(Bs0, .), Cs0, Ds).` | ✅ Supported | Dots inside terms no longer trigger clause-terminator errors |

## Operator Syntax

### Standard ISO Operators

All standard ISO operators are supported with correct precedence (1-1200):

| Precedence | Operators | Fixity | Purpose |
|------------|-----------|--------|---------|
| 1200 | `:-` | xfx, fx | Clause, directive |
| 1200 | `?-` | fx | Query |
| 1200 | `-->` | xfx | DCG rule |
| 1100 | `;` | xfy | Disjunction |
| 1050 | `->` | xfy | If-then |
| 1000 | `,` | xfy | Conjunction |
| 900 | `\+` | fy | Negation |
| 700 | `=`, `\=`, `==`, `\==` | xfx | Unification, equality |
| 700 | `@<`, `@=<`, `@>`, `@>=` | xfx | Term ordering |
| 700 | `is`, `=..` | xfx | Arithmetic, univ |
| 700 | `<`, `=<`, `>`, `>=` | xfx | Comparison |
| 700 | `=:=`, `=\=` | xfx | Arithmetic equality |
| 600 | `:` | xfy | Module qualification |
| 500 | `+`, `-` | yfx | Addition, subtraction |
| 500 | `/\`, `\/` | yfx | Bitwise AND, OR |
| 400 | `*`, `/`, `//` | yfx | Multiplication, division |
| 400 | `mod`, `div`, `rem` | yfx | Modular arithmetic |
| 400 | `<<`, `>>` | yfx | Bit shift |
| 200 | `**`, `^` | xfy | Exponentiation |
| 200 | `+`, `-` | fy | Unary plus, minus |

### Custom Operator Definition

| Feature | Example | Status | Notes |
|---------|---------|--------|-------|
| Define operator | `:- op(500, yfx, my_op).` | ✅ Supported | Dynamic definition |
| Multiple operators | `:- op(600, fx, [op1, op2]).` | ✅ Supported | List notation |
| Remove operator | `:- op(0, yfx, my_op).` | ✅ Supported | Precedence 0 removes |
| Export operators | `:- module(m, [my_op/2]).` | ✅ Supported | In module exports |

**Protected Operators** (cannot be redefined):
- `,` (conjunction)
- `;` (disjunction)
- `->` (if-then)
- `:-` (clause operator)
- `:` (module qualification)
- `|` (list separator)
- `{}` (curly braces)

### Operators as Functors

Operators can be used as regular functors by:

1. **Quoting the operator**:
   ```prolog
   ';'(a, b)      % Disjunction as functor
   ','(X, Y)      % Conjunction as functor
   '='(X, Y)      % Unification as functor
   ```

2. **Parenthesizing the operator** (as an atom):
   ```prolog
   X = (;)        % X is the atom ';'
   Y = (,)        % Y is the atom ','
   Z = (|)        % Z is the atom '|'
   ```

3. **Using operators directly followed by parentheses**:
   ```prolog
   ;(a, b)        % Valid: disjunction as functor
   |(a, b)        % Valid: pipe as functor
   ```

## List Syntax

| Feature | Example | Status |
|---------|---------|--------|
| Empty list | `[]` | ✅ Supported |
| Proper list | `[1, 2, 3]` | ✅ Supported |
| Head and tail | `[H\|T]` | ✅ Supported |
| Multiple heads | `[a, b, c\|Rest]` | ✅ Supported |
| Improper list | `[X\|Y]` where Y is not a list | ✅ Supported |
| Nested lists | `[[a, b], [c, d]]` | ✅ Supported |

**Internal representation**: Lists are represented as compounds using the `'.'` functor:
- `[1, 2, 3]` → `'.'(1, '.'(2, '.'(3, []))))`

## DCG (Definite Clause Grammar) Syntax

| Feature | Example | Status |
|---------|---------|--------|
| DCG rule | `rule --> body.` | ✅ Supported |
| Terminals | `[a, b, c]` | ✅ Supported |
| Non-terminals | `noun_phrase` | ✅ Supported |
| Sequence | `a, b, c` | ✅ Supported |
| Alternatives | `(a ; b)` | ✅ Supported |
| Embedded goals | `{write(x)}` | ✅ Supported |
| Empty production | `[]` | ✅ Supported |
| Cut in DCG | `!` | ✅ Supported |

**Expansion**: DCG rules are expanded to difference list predicates at parse time:
```prolog
% Input:
sentence --> noun_phrase, verb_phrase.

% Expands to:
sentence(S0, S) :- noun_phrase(S0, S1), verb_phrase(S1, S).
```

**Built-in predicates**:
- `phrase/2`: `phrase(Rule, List)` ≡ `Rule(List, [])`
- `phrase/3`: `phrase(Rule, List, Rest)` ≡ `Rule(List, Rest)`

**DCG indicators in exports**: `Name//Arity` in module export lists expands to `Name/Arity+2`.

## Module System Syntax

| Feature | Example | Status |
|---------|---------|--------|
| Module declaration | `:- module(name, [exports]).` | ✅ Supported |
| Export predicates | `:- module(m, [foo/1, bar/2]).` | ✅ Supported |
| Export operators | `:- module(m, [op/2]).` | ✅ Supported |
| DCG exports | `:- module(m, [rule//0]).` | ✅ Supported |
| Import module | `:- use_module(library(lists)).` | ✅ Supported |
| Selective import | `:- use_module(library(lists), [append/3]).` | ✅ Supported |
| Consult library file | `consult(library(dcgs)).` | ✅ Supported |
| Module-qualified call | `lists:append(X, Y, Z)` | ✅ Supported |
| Module-qualified head | `user:term_expansion(X, Y) :- ...` | ✅ Supported |

**Export list handling**:
- Valid predicate indicators: `Name/Arity`, `Name//Arity` (DCG)
- Invalid indicators (e.g., `!/0`) are skipped with a warning (Scryer-Prolog extension)

## Comment Syntax

| Feature | Example | Status |
|---------|---------|--------|
| Line comment | `% This is a comment` | ✅ Supported |
| Block comment | `/* This is a block comment */` | ✅ Supported |
| Nested blocks | `/* outer /* inner */ */` | ✅ Supported |
| Multi-line blocks | `/* Line 1\n   Line 2 */` | ✅ Supported |

**Note**: Comments are properly handled in all contexts, including:
- Inside clauses
- Between terms
- In module declarations
- Within operator definitions

The parser correctly distinguishes `.` as a clause terminator from `.` inside comments, floats, or parentheses.

## Directive Syntax

| Directive | Example | Status | Notes |
|-----------|---------|--------|-------|
| Dynamic | `:- dynamic(foo/1).` | ✅ Supported | Allow runtime modification |
| Multifile | `:- multifile(bar/2).` | ✅ Supported | Allow cross-file clauses |
| Discontiguous | `:- discontiguous(baz/3).` | ✅ Supported | Allow non-contiguous clauses |
| Initialization | `:- initialization(goal).` | ✅ Supported | Run at startup |
| Operator | `:- op(500, yfx, my_op).` | ✅ Supported | Define operator |
| Char conversion | `:- char_conversion(a, e).` | ✅ Supported | Character mapping |
| Table | `:- table(pred/1).` | ✅ Supported | Memoization |
| Attribute | `:- attribute(attr/1).` | ✅ Supported | Attributed variables |
| Conditional - if | `:- if(condition).` | ✅ Supported | Conditional compilation |
| Conditional - elif | `:- elif(condition).` | ✅ Supported | Alternative condition |
| Conditional - else | `:- else.` | ✅ Supported | Default case |
| Conditional - endif | `:- endif.` | ✅ Supported | End conditional |

**Scryer-specific directives** (ignored with warning):
- `:- non_counted_backtracking(pred/N).` - Inference counting hint
- `:- meta_predicate(...).` - Module expansion hints

## Parenthesized Comma Handling

Special handling prevents flattening of comma operators inside parentheses:

```prolog
% These are DIFFERENT:
test1 :- a, b, c.          % Three goals in sequence
test2 :- (a, b), c.        % Grouped: (a,b) then c
test3 :- call((a, b)), c.  % Same as test2
```

**Internal representation**: `ParenthesizedComma` type preserves grouping.

## Character Classification

Following ISO Prolog character categories:

| Category | Characters | Usage |
|----------|-----------|--------|
| **Lowercase** | `a-z` | Start of unquoted atom |
| **Uppercase** | `A-Z` | Start of variable |
| **Digit** | `0-9` | Numbers |
| **Underscore** | `_` | Variables, atoms |
| **Graphic** | `#$&*+-./:<=>?@^~` | Operators |
| **Solo** | `!(),[]{}\|` | Special syntax |
| **Layout** | Space, tab, newline | Whitespace |

## Special Constructs

### Curly Braces

```prolog
{Goal}    % Wraps Goal in '{}'/1 functor
```

Used in:
- DCG rules for embedded goals: `rule --> {Goal}.`
- Meta-predicates for delayed execution
- Constraint programming

### Cut

```prolog
!    % Cut operator - commits to current choice
```

- Prevents backtracking past this point
- Used to implement deterministic predicates
- Has special semantics in if-then-else

### Anonymous Variable

```prolog
_    % Matches anything, not unified
```

- Each `_` is a distinct variable
- Used to ignore arguments
- Common in patterns: `foo(_, X, _)`

## Clause Termination

The parser correctly handles the dot (`.`) as a clause terminator, distinguishing it from:

1. **Decimal points in floats**: `3.14` (not a terminator)
2. **Dots in operators**: `..` (range), `...` (ellipsis)
3. **Dots inside parentheses**: `f(a.)` would be an error, but the parser tracks nesting
4. **Dots inside lists**: `[a.]` would be an error
5. **Dots inside curly braces**: `{a.}` would be an error

A dot followed by whitespace (space, tab, newline) or EOF is recognized as a clause terminator.

## Compatibility Notes

### Scryer-Prolog Compatibility

**Compatible**:
- ✅ Core ISO syntax (facts, rules, queries)
- ✅ All standard ISO operators
- ✅ List syntax
- ✅ Comments (line and block)
- ✅ DCG syntax and semantics
- ✅ Module system (ISO Part 1 + SWI extensions)
- ✅ Binary and octal with `0b`/`0o` prefix

**Incompatible**:
- ❌ Hexadecimal: Vibe uses `0xff` (lowercase only), Scryer uses `0xABC` (any case)
- ❌ Edinburgh `<radix>'<number>`: Vibe supports `16'ff'`, Scryer does not
- ❌ Character escapes: Vibe doesn't require trailing `\` on hex/octal
- ❌ Number underscores: Scryer supports `1_000_000`, Vibe does not
- ❌ Backtick character literals: Scryer supports `` `a` ``, Vibe does not
- ❌ Additional escapes: Scryer has `\a`, `\b`, `\v`, `\f`; Vibe does not

### SWI-Prolog Compatibility

**Compatible**:
- ✅ Module system (SWI-Prolog style)
- ✅ Operator exports in module declarations
- ✅ DCG `//` notation in exports
- ✅ Most common SWI extensions

**Differences**:
- ⚠️ `double_quotes` flag: Different behavior/defaults
- ⚠️ Some SWI-specific built-ins may not be available

## Extension Features (Vibe-Specific)

These features are specific to Vibe-Prolog and may not be portable:

1. **Edinburgh `<radix>'<number>` notation** for arbitrary bases (2-36):
   ```prolog
   16'ff'    % Hexadecimal: 255
   36'ZZZ'   % Base-36: 46655
   ```

2. **Conditional compilation directives**:
   ```prolog
   :- if(some_condition).
   % ... code when true ...
   :- elif(other_condition).
   % ... alternative code ...
   :- else.
   % ... default code ...
   :- endif.
   ```


## Known Limitations

1. **Hexadecimal case sensitivity**: `0x` prefix only accepts lowercase `a-f`
   - Issue: Incompatible with Scryer-Prolog's case-insensitive hex
   - Workaround: Use lowercase or ISO `16'...'` format

2. **Limited escape sequences**: Missing `\a`, `\b`, `\v`, `\f`
   - Impact: Some Scryer-Prolog code with these escapes won't parse
   - Workaround: Use alternative representations or character codes

3. **No number underscores**: `1_000_000` not supported
   - Workaround: Write without underscores: `1000000`

## Best Practices for Portable Code

To write Prolog code that works across multiple implementations:

1. **Use standard number formats**:
   - ✅ Decimal: `123`, `3.14`, `1.5e-3`
   - ✅ Prefix notation: `0b1010`, `0o755`
   - ⚠️ For hex, choose one:
     - Vibe-portable: `0xff` (lowercase)
     - Scryer-portable: `0xABC` (any case)
     - Both: Use Edinburgh `<radix>'<number>` format like `16'ff'` or avoid hex

2. **Character escapes**:
   - ✅ Use basic escapes: `\n`, `\t`, `\r`, `\\`, `\'`, `\"`
   - ⚠️ Avoid system-specific escapes

3. **Operators**:
   - ✅ Use standard ISO operators
   - ✅ Define custom operators explicitly with `:- op/3`

4. **Module system**:
   - ✅ Use standard `module/2` and `use_module/1,2`
   - ✅ Export predicates and operators explicitly

5. **Comments**:
   - ✅ Use freely - fully portable

## Future Improvements

See GitHub issues for planned enhancements:

- Make `0x` hex literals case-insensitive (compatibility with Scryer-Prolog)
- Add support for number underscores (optional, for readability)
- Implement additional escape sequences (`\a`, `\b`, `\v`, `\f`)
- Consider `double_quotes` flag for string representation modes

---

*Last updated: 2025-01-05*
*Vibe-Prolog version: Current*
