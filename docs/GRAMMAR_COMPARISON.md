# Vibe-Prolog Grammar Comparison: Vibe vs Scryer vs SWI

This document provides a detailed three-way comparison of the grammar implementations in Vibe-Prolog, Scryer-Prolog, and SWI-Prolog, highlighting similarities, differences, and potential incompatibilities. For end-to-end SWI compatibility guidance, see [tests/README_SWI_COMPATIBILITY.md](../tests/README_SWI_COMPATIBILITY.md).

## Executive Summary

**Overall Compatibility**: High (95%+ for standard ISO Prolog across all three systems)

All three implementations are largely ISO-compliant with minor differences in:
- Number literal syntax (base notation, case sensitivity)
- String representation defaults
- Advanced extensions (dicts, quasi-quotations in SWI)
- Some parser implementation details

**Key Finding**: Most standard Prolog code will run on all three systems. The main incompatibilities are in extended syntax features, numeric literal formats, and SWI-Prolog's advanced extensions (dicts, quasi-quotations).

---

## 1. Architecture Comparison

| Aspect | Vibe-Prolog | Scryer-Prolog | SWI-Prolog |
|--------|-------------|---------------|------------|
| **Language** | Python | Rust | C |
| **Parser Library** | Lark (Earley/LALR) | Custom Pratt precedence climbing | Custom recursive descent |
| **Grammar Definition** | Dynamic string-based grammar generation | Hardcoded recursive descent with operator tables | Built-in with operator tables |
| **Operator Handling** | Grammar rules generated per operator set | Runtime precedence climbing algorithm | Runtime precedence climbing |
| **Performance** | Interpreted, grammar cached | Compiled, highly optimized | Compiled, highly optimized |
| **Extensibility** | Runtime grammar regeneration | Runtime operator table updates | Runtime operator table updates |

**Implication**: All three support dynamic operator definition, but use different parsing strategies. This generally doesn't affect compatibility for user code.

---

## 2. Number Literal Syntax

### 2.1 Decimal Numbers

| Format | Vibe-Prolog | Scryer-Prolog | SWI-Prolog | Notes |
|--------|-------------|---------------|------------|-------|
| **Integers** | `42`, `-17` | `42`, `-17` | `42`, `-17` | ✅ Fully compatible |
| **Floats** | `3.14`, `-0.5` | `3.14`, `-0.5` | `3.14`, `-0.5` | ✅ Fully compatible |
| **Scientific** | `1.5e-3`, `2E10` | `1.5e-3`, `2E10` | `1.5e-3`, `2E10` | ✅ Fully compatible |
| **Underscore grouping** | ✅ `1_000_000`| ✅ `1_000_000` | ✅ `1_000_000` | ✅ Fully compatible |
| **Space grouping** | ❌ Not supported | ❌ Not supported | ✅ `1 000 000` (radix ≤10) | ⚠️ SWI-only |

**Recommendation**: Avoid spaces in number literals for maximum portability.

### 2.2 Base-Qualified Numbers (SOME DIFFERENCES)

| Format | Vibe-Prolog | Scryer-Prolog | SWI-Prolog | Status |
|--------|-------------|---------------|------------|--------|
| **Hexadecimal** | `0xff` (any case) | `0xABC` (any case) | `0xABC` (any case) |  ✅ Fully compatible |
| **Octal** | `0o77` | `0o755` | `0o755` | ✅ Fully compatible |
| **Binary** | `0b101` | `0b1010` | `0b1010` | ✅ Fully compatible |
| **Edinburgh <radix>'<number>** | ✅ `16'FF`, `36'ZZZ` (2-36) | ❌ Not supported | ✅ `16'FF`, `36'ZZZ` (2-36) | ⚠️ Vibe/SWI only ([#303](https://github.com/nlothian/Vibe-Prolog/issues/303)) |
| **Rational numbers** | ❌ Not supported | ❌ Not supported | ✅ `1r3`, `1/2` (GMP) | ⚠️ SWI-only |
| **Special floats** | ❌ Not supported | ❌ Not supported | ✅ `1.0Inf`, `-1.0Inf`, NaN | ⚠️ SWI-only |

**INCOMPATIBILITY DETAILS**:

```prolog
% Hexadecimal literals - THREE DIFFERENT BEHAVIORS:
% Vibe-Prolog:
X = 0xABC.       % Works: X = 2748 (any case)
X = 0xff.        % Works: X = 255
X = 16'ff'.      % Works: X = 255 (Edinburgh syntax)

% Scryer-Prolog:
X = 0xABC.       % Works: X = 2748 (any case)
X = 0xff.        % Works: X = 255
X = 16'ff'.      % SYNTAX ERROR (no Edinburgh format)

% SWI-Prolog:
X = 0xABC.       % Works: X = 2748 (any case)
X = 16'ff'.      % Works: X = 255 (Edinburgh syntax)
X = 1r3.         % Works: X = 1/3 (rational)
X = 1.0Inf.      % Works: X = +infinity
```

**Recommendations for portability**:
- **All three systems**: Use decimal numbers or `0x` prefix with any case (`0xFF`) when possible
- **Vibe + SWI**: Edinburgh `<radix>'<number>` syntax (`16'ff'`)

### 2.3 Character Code Syntax

| Format | Vibe-Prolog | Scryer-Prolog | SWI-Prolog | Notes |
|--------|-------------|---------------|------------|-------|
| **Basic** | `0'a` → 97 | `0'a` → 97 | `0'a` → 97 | ✅ Fully compatible |
| **Backtick** | ❌ Not supported | ✅ `` `a` `` → 97 | ❌ Not supported | ⚠️ Scryer-only |
| **Hex escape** | `0'\x41` (no terminator) | `0'\x41\` (needs `\`) | `0'\x41` (no terminator) | ⚠️ Termination differs |


**Escape termination differences**:
```prolog
% Vibe-Prolog & SWI-Prolog:
X = 0'\x41.     % X = 65 (hex escape, no backslash terminator)

% Scryer-Prolog:
X = 0'\x41\.    % X = 65 (hex escape MUST end with backslash)
```

**Impact**: Character code escapes may need adjustment when porting between systems.

---

## 3. String and Atom Syntax

### 3.1 Quoted Atoms

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| Single quotes | `'atom'` | `'atom'` | ✅ Yes |
| Escape sequences | `\'`, `\"`, `\\`, `\n`, `\t`, `\r` | `\a`, `\b`, `\v`, `\f`, `\t`, `\n`, `\r` | ⚠️ Scryer has more |
| Doubled quotes | `'it''s'` → `it's` | `'it''s'` → `it's` | ✅ Yes |
| Hex escapes | `'\x41'` (no terminator) | `'\x41\'` (backslash required) | ⚠️ Different |
| Octal escapes | ✅ `'\101\'` (backslash required) | `'\101\'` (backslash required) | ✅ Compatible |

**Scryer additional escape sequences**:
- `\a` - alert (bell)
- `\b` - backspace
- `\v` - vertical tab
- `\f` - form feed

**Escape termination**:
```prolog
% Vibe-Prolog:
Atom = '\x48ello'.    % 'Hello' (hex escape for 'H')

% Scryer-Prolog:
Atom = '\x48\ello'.   % 'Hello' (backslash terminates hex)
```

### 3.2 Double-Quoted Strings

| Aspect | Vibe-Prolog | Scryer-Prolog | Compatible? |
|--------|-------------|---------------|-------------|
| **Default representation** | Atom | Configurable flag | ⚠️ Different defaults |
| Atom mode | `"hello"` → atom | `double_quotes(atom)` | ✅ Compatible |
| Code list mode | Not default | `double_quotes(codes)` → `[104,101,...]` | ⚠️ Different |
| Char list mode | Not default | `double_quotes(chars)` → `[h,e,...]` | ⚠️ Different |

**Impact**: Programs relying on specific string representation may behave differently. Check flags/settings.

---

## 4. Operator System

### 4.1 Operator Definitions

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| `:- op(Prec, Type, Name)` | ✅ Full support | ✅ Full support | ✅ Yes |
| Precedence range | 1-1200 | 1-1200 | ✅ Yes |
| Fixity types | xfx, xfy, yfx, yfy, fx, fy, xf, yf | Same | ✅ Yes |
| Multiple ops | `op(500, yfx, [+, -])` | Same | ✅ Yes |
| Remove operator | `op(0, Type, Name)` | Same | ✅ Yes |
| Protected operators | `,`, `;`, `->`, `:-`, `:`, `|`, `{}` | `,`, `:-`, `|` | ⚠️ Slightly different |

**Protected operator differences**:
- **Vibe**: Cannot redefine `,`, `;`, `->`, `:-`, `:`, `|`, `{}`
- **Scryer**: Cannot redefine `,`, `:-`, `|` (more permissive on some)

### 4.2 Default ISO Operators

Both implement the same ISO operator set (precedence 1-1200), including:

| Precedence | Operators | Both? |
|------------|-----------|-------|
| 1200 | `:-` (xfx, fx), `?-` (fx), `-->` (xfx) | ✅ Yes |
| 1100 | `;` (xfy) | ✅ Yes |
| 1050 | `->` (xfy) | ✅ Yes |
| 1000 | `,` (xfy) | ✅ Yes |
| 900 | `\+` (fy) | ✅ Yes |
| 700 | `=`, `\=`, `==`, `\==`, `@<`, `@>`, `is`, `=..`, etc. | ✅ Yes |
| 600 | `:` (xfy) | ✅ Yes |
| 500 | `+`, `-` (yfx), `/\`, `\/` | ✅ Yes |
| 400 | `*`, `/`, `//`, `mod`, `div`, `rem`, `<<`, `>>` | ✅ Yes |
| 200 | `**`, `^` (xfy), `+`, `-` (fy) | ✅ Yes |

**Compatibility**: ✅ Excellent - all standard operators align.

### 4.3 Operator Export/Import in Modules

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| Export operators | ✅ SWI-Prolog compatible | ✅ Yes | ✅ Yes |
| Import operators | ✅ Two-pass parsing | ✅ Two-pass parsing | ✅ Yes |
| Operator discovery | Pre-scan `use_module` targets | Pre-scan module files | ✅ Yes |

**Both implement**: When a module is loaded via `use_module`, its operators are registered before parsing dependent code.

---

## 5. List Syntax

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| Empty list | `[]` | `[]` | ✅ Yes |
| Proper lists | `[1,2,3]` | `[1,2,3]` | ✅ Yes |
| Head/tail | `[H\|T]` | `[H\|T]` | ✅ Yes |
| Multiple heads | `[a,b\|Rest]` | `[a,b\|Rest]` | ✅ Yes |
| Improper lists | `[X\|Y]` (Y not a list) | `[X\|Y]` | ✅ Yes |
| Pipe priority check | Yes | `\|` must have priority > 1000 | ✅ Yes |

**Compatibility**: ✅ Perfect - list syntax is identical.

---

## 6. Comments

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| Line comments | `% comment` | `% comment` | ✅ Yes |
| Block comments | `/* comment */` | `/* comment */` | ✅ Yes |
| Nested blocks | `/* outer /* inner */ */` | `/* outer /* inner */ */` | ✅ Yes |

**Compatibility**: ✅ Perfect.

---

## 7. DCG (Definite Clause Grammars)

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| Syntax | `Head --> Body` | `Head --> Body` | ✅ Yes |
| Expansion timing | Parse-time | Parse-time | ✅ Yes |
| Terminals | `[a, b]` | `[a, b]` | ✅ Yes |
| Non-terminals | `foo` → `foo(S0, S)` | `foo` → `foo(S0, S)` | ✅ Yes |
| Embedded goals | `{Goal}` | `{Goal}` | ✅ Yes |
| `phrase/2,3` | ✅ Built-in | ✅ Built-in | ✅ Yes |
| DCG indicators | `Name//Arity` in exports | `Name//Arity` in exports | ✅ Yes |

**Compatibility**: ✅ Perfect - DCG implementations are identical in semantics.

---

## 8. Module System

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| Module declaration | `:- module(Name, Exports)` | `:- module(Name, Exports)` | ✅ Yes |
| Module-qualified calls | `Module:Goal` | `Module:Goal` | ✅ Yes |
| Export enforcement | ✅ Yes | ✅ Yes | ✅ Yes |
| `use_module/1,2` | ✅ Yes | ✅ Yes | ✅ Yes |
| `library(Name)` resolution | `./library/` preferred | Standard library paths | ⚠️ Path differences |
| Operator exports | ✅ SWI-compatible | ✅ Yes | ✅ Yes |
| Module-scoped namespaces | ✅ Yes | ✅ Yes | ✅ Yes |
| Module-qualified heads | `M:Head :- Body` | `M:Head :- Body` | ✅ Yes |
| Invalid indicators in exports | Skip with warning (Scryer ext) | Skip with warning | ✅ Yes |

**Compatibility**: ✅ Excellent - both follow ISO Part 1 with SWI-Prolog extensions.

**Path resolution difference**: Both use `library/` directories, but may differ in search paths for loading modules.

---

## 9. Directives

| Directive | Vibe-Prolog | Scryer-Prolog | Compatible? |
|-----------|-------------|---------------|-------------|
| `:- dynamic/1` | ✅ | ✅ | ✅ Yes |
| `:- multifile/1` | ✅ | ✅ | ✅ Yes |
| `:- discontiguous/1` | ✅ | ✅ | ✅ Yes |
| `:- initialization/1` | ✅ | ✅ | ✅ Yes |
| `:- op/3` | ✅ | ✅ | ✅ Yes |
| `:- char_conversion/2` | ✅ | ✅ | ✅ Yes |
| `:- table/1` | ✅ Variant tabling | ✅ Tabling library | ✅ Yes |
| `:- attribute/1` | ✅ | ✅ | ✅ Yes |
| `:- if/elif/else/endif` | ✅ | ❓ Unknown | ⚠️ Vibe extension |
| `:- non_counted_backtracking` | Ignored with warning | ✅ Native | ⚠️ Scryer-specific |
| `:- meta_predicate` | Ignored with warning | ✅ Native | ⚠️ Scryer-specific |

**Compatibility**: ✅ Good - core directives align; Scryer-specific directives handled gracefully in Vibe.

---

## 10. Special Syntax Features

### 10.1 Compound Terms

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| Functor application | `f(a, b)` | `f(a, b)` | ✅ Yes |
| Operators as functors | `';'(a, b)`, `','(X, Y)` | Same | ✅ Yes |
| Parenthesized operators | `(;)`, `(,)`, `(\|)` | Same | ✅ Yes |
| Curly braces | `{Goal}` → `'{}'(Goal)` | Same | ✅ Yes |
| Cut | `!` | `!` | ✅ Yes |

**Compatibility**: ✅ Perfect.

### 10.2 Variables

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| Named variables | `X`, `Var`, `_Result` | Same | ✅ Yes |
| Anonymous variable | `_` | Same | ✅ Yes |
| Uppercase start | Required | Required | ✅ Yes |
| Underscore start | Allowed | Allowed | ✅ Yes |

**Compatibility**: ✅ Perfect.

---

## 11. Clause and Query Syntax

| Feature | Vibe-Prolog | Scryer-Prolog | Compatible? |
|---------|-------------|---------------|-------------|
| Facts | `fact(a).` | `fact(a).` | ✅ Yes |
| Rules | `head :- body.` | `head :- body.` | ✅ Yes |
| Queries | `?- goal.` | `?- goal.` | ✅ Yes |
| Directives | `:- directive.` | `:- directive.` | ✅ Yes |
| Clause terminator | `.` (dot) | `.` (dot) | ✅ Yes |
| Decimal vs terminator | Distinguishes floats | Distinguishes floats | ✅ Yes |

**Compatibility**: ✅ Perfect.

---

## 12. Implementation-Specific Features

### 12.1 Vibe-Prolog Specific

| Feature | Description | Portable? |
|---------|-------------|-----------|
| **Conditional compilation** | `:- if/elif/else/endif` | ⚠️ Vibe-specific |
| **Edinburgh <radix>'<number> format** | `16'ff`, `36'ZZZ` (radix 2-36) | ⚠️ Not in Scryer (see [#303](https://github.com/nlothian/Vibe-Prolog/issues/303)) |
| **Hex without prefix** | `0xff` (lowercase only) | ⚠️ Not in Scryer (see [#302](https://github.com/nlothian/Vibe-Prolog/issues/302)) |
| **Lark-based parsing** | Implementation detail | ✅ No impact |
| **Grammar caching** | Performance optimization | ✅ No impact |

### 12.2 Scryer-Prolog Specific

| Feature | Description | Portable? |
|---------|-------------|-----------|
| **Backtick character literals** | `` `a` `` → 97 | ⚠️ Not in Vibe |
| **Underscores in numbers** | `1_000_000` | ⚠️ Not in Vibe |
| **Escape termination** | Hex/octal escapes need `\` | ⚠️ Not in Vibe |
| **Additional escape codes** | `\a`, `\b`, `\v`, `\f` | ⚠️ Not in Vibe |
| **Configurable string modes** | `double_quotes` flag | ⚠️ Different in Vibe |
| **Layout-sensitive parsing** | `(` vs `OpenCT` tokens | ✅ No impact |
| **Delimited continuations** | `reset/3`, `shift/1` | ⚠️ Not in Vibe |
| **Backtrackable globals** | `bb_get/2`, `bb_put/2` | ⚠️ Not in Vibe |

---

## 13. Practical Compatibility Matrix

### 13.1 ISO Core Prolog

| Category | Portable? | Notes |
|----------|-----------|-------|
| Facts and rules | ✅ 100% | Fully compatible |
| Variables | ✅ 100% | Fully compatible |
| Atoms | ✅ 100% | Fully compatible |
| Basic numbers | ✅ 100% | Decimal, float, scientific all work |
| Lists | ✅ 100% | Fully compatible |
| Operators | ✅ 100% | ISO operator set identical |
| Unification | ✅ 100% | Fully compatible |
| Control constructs | ✅ 100% | `,`, `;`, `->`, `\+`, `!` all work |
| Comments | ✅ 100% | Fully compatible |

### 13.2 Common Extensions

| Feature | Portable? | Notes |
|---------|-----------|-------|
| DCG syntax | ✅ 100% | Fully compatible |
| Module system | ✅ 95% | Minor path resolution differences |
| Dynamic predicates | ✅ 100% | `assert*/retract` work identically |
| Attributed variables | ✅ 100% | Both support SICStus-style atts |
| Tabling | ✅ 90% | Both support, may differ in details |
| Higher-order predicates | ✅ 100% | `maplist`, `findall`, etc. work |

### 13.3 Extended Syntax

| Feature | Portable? | Notes |
|---------|-----------|-------|
| Hex literals | ⚠️ 50% | **Different syntax**: `0xff` (Vibe) vs `0xABC` (Scryer) - see [#302](https://github.com/nlothian/Vibe-Prolog/issues/302) |
| Octal literals | ✅ 100% | `0o77` works in both |
| Binary literals | ✅ 100% | `0b101` works in both |
| Edinburgh <radix>'<number> | ⚠️ 0% | **Vibe-only**: `16'ff'` not in Scryer - see [#303](https://github.com/nlothian/Vibe-Prolog/issues/303) |
| Character escapes | ⚠️ 80% | **Different termination**: `\x41` vs `\x41\` |
| Number underscores | ⚠️ 0% | **Scryer-only**: `1_000_000` |
| Backtick chars | ⚠️ 0% | **Scryer-only**: `` `a` `` |

---

## 14. Migration Guidance

### 14.1 Scryer → Vibe-Prolog

**Syntax changes needed**:

1. **Hexadecimal literals**:
   ```prolog
   % Scryer:
   X = 0xABC.

   % Vibe:
   X = 0xabc.     % Or use 16'abc'
   ```

2. **Character escape terminators**:
   ```prolog
   % Scryer:
   Atom = '\x41\Hello'.

   % Vibe:
   Atom = '\x41Hello'.   % No backslash terminator
   ```

3. **Remove number underscores**:
   ```prolog
   % Scryer:
   X = 1_000_000.

   % Vibe:
   X = 1000000.
   ```

4. **Backtick character literals**:
   ```prolog
   % Scryer:
   X = `a`.

   % Vibe:
   X = 0'a.      % Or X = 97
   ```

### 14.2 Vibe → Scryer-Prolog

**Syntax changes needed**:

1. **Edinburgh `<radix>'<number>` literals** (if used):
   ```prolog
   % Vibe:
   X = 16'ff'.

   % Scryer:
   X = 0xFF.     % Use 0x prefix
   ```

2. **Hexadecimal case**:
   ```prolog
   % Vibe:
   X = 0xabc.    % Lowercase works

   % Scryer:
   X = 0xABC.    % Use any case
   ```

3. **Conditional compilation** (if used):
   ```prolog
   % Vibe:
   :- if(some_condition).
   % ... code ...
   :- endif.

   % Scryer:
   % Rewrite using alternative approaches
   ```

---

## 15. Recommendations

### For Maximum Portability

1. **Use standard number formats**:
   - ✅ Decimal: `123`, `3.14`, `1.5e-3`
   - ✅ Binary with `0b` prefix: `0b1010`
   - ✅ Octal with `0o` prefix: `0o755`
   - ⚠️ **AVOID**: Edinburgh `<radix>'<number>` like `16'ff'` (use `0xFF` or decimal)
   - ⚠️ **AVOID**: Number underscores `1_000_000`

2. **Character escapes**:
   - ✅ Use basic escapes: `\n`, `\t`, `\r`, `\\`, `\'`, `\"`
   - ⚠️ **AVOID**: Hex/octal escapes if possible
   - If needed, test on both systems

3. **String handling**:
   - ✅ Use single-quoted atoms: `'atom'`
   - ⚠️ Be aware of `double_quotes` flag differences
   - Test string-heavy code on both systems

4. **Operators**:
   - ✅ Use standard ISO operators
   - ✅ Define custom operators with `:- op/3`
   - ✅ Export operators in module declarations

5. **Module system**:
   - ✅ Use standard `module/2`, `use_module/1,2`
   - ✅ Export operators and predicates explicitly
   - ⚠️ Test library resolution paths

6. **Comments**:
   - ✅ Use freely - both systems handle identically

---

## 18. Conclusion

**Overall Assessment**: Vibe-Prolog has **highly compatible** grammars with both Scryer-Prolog and SWI-Prolog for standard ISO Prolog code. The main incompatibilities are:

### Critical Differences (Require Code Changes)

**Scryer-Prolog vs Vibe-Prolog**:
1. **Hexadecimal literals**: Different syntax (`0xff` vs `0xABC`)
2. **Edinburgh `<radix>'<number>` format**: Vibe supports (`16'ff'`), Scryer does not
3. **Character escape terminators**: Different requirements

**SWI-Prolog vs Vibe-Prolog**:
1. **Dicts syntax**: SWI supports (`tag{key:value}`, `#{}`, `.key`), Vibe does not
2. **Quasi-quotations**: SWI supports (`{|Syntax||Content|}`), Vibe does not
3. **Rational numbers**: SWI supports (`1r3`), Vibe does not
4. **Number digit grouping**: SWI supports (`1_000_000`), Vibe does not

### Minor Differences (Usually Don't Affect Code)

**Scryer-Prolog**:
1. **Additional escape sequences**: Scryer has more (`\a`, `\b`, `\v`, `\f`)
2. **Number underscores**: Scryer supports `1_000_000`
3. **Backtick character literals**: Scryer supports `` `a` ``
4. **String representation defaults**: May need flag adjustment

**SWI-Prolog**:
1. **Unicode escapes**: SWI supports `\uXXXX`, `\UXXXXXXXX`
2. **Extended escapes**: SWI has `\a`, `\b`, `\e`, `\f`, `\s`, `\v`
3. **Special floats**: SWI supports Inf, NaN
4. **Hex case sensitivity**: SWI accepts `0xFF`, Vibe requires `0xff`

### Identical (100% Compatible)

1. ISO core syntax (facts, rules, queries, operators)
2. List syntax
3. Comments
4. DCG syntax and semantics
5. Module system basics
6. Standard ISO operators

---

## 17. SWI-Prolog Specific Extensions

### 17.1 Dicts (SWI-Prolog Only)

**SWI-Prolog dict syntax** is a major extension not supported in Vibe-Prolog or Scryer-Prolog.

| Feature | Vibe-Prolog | Scryer-Prolog | SWI-Prolog |
|---------|-------------|---------------|------------|
| Dict creation `tag{key:value}` | ❌ | ❌ | ✅ |
| Anonymous dict `#{key:value}` | ❌ | ❌ | ✅ |
| Dot access `Dict.key` | ❌ | ❌ | ✅ |
| Operators `:<`, `>:<` | ❌ | ❌ | ✅ |

**SWI example**:
```prolog
Point = point{x:1, y:2}.
X = Point.x.  % X = 1
```

**Portable workaround**: Use compound terms or key-value lists.

### 17.2 Quasi-Quotations (SWI-Prolog Only)

| Feature | Vibe-Prolog | Scryer-Prolog | SWI-Prolog |
|---------|-------------|---------------|------------|
| `{|Syntax||Content|}` | ❌ | ❌ | ✅ |

**SWI example**:
```prolog
HTML = {|html||<div>Content</div>|}.
```

**Portable workaround**: Use regular strings or atoms.

---

**Recommendation**: For code that needs to run across Vibe-Prolog, Scryer-Prolog, and SWI-Prolog:
- **Stick to ISO core syntax** wherever possible
- **Number literals**: Use Edinburgh `<radix>'<number>` syntax (works in Vibe and SWI, not Scryer) OR use decimal
- **Avoid system-specific extensions**:
  - ❌ Dicts (SWI-only)
  - ❌ Quasi-quotations (SWI-only)
  - ❌ Rational number syntax (SWI-only)
  - ❌ Digit grouping underscores (SWI/Scryer, not Vibe)
  - ❌ Unicode escape sequences (SWI-only)
- **Test on all target platforms** to catch incompatibilities early

Most standard ISO Prolog programs will work across all three systems with minimal or no changes. The main incompatibilities are in advanced extensions (dicts, quasi-quotations) and numeric literal syntax.
