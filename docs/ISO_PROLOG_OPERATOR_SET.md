# ISO Prolog Operator Set

This document lists the **ISO/IEC 13211-1 (core Prolog)** standard operators, including their **precedence** and **specifier**.

Lower precedence numbers bind **more tightly**.

---

## Operator Specifiers

| Specifier | Meaning |
|----------|--------|
| `xfx` | Infix, non-associative |
| `xfy` | Infix, right-associative |
| `yfx` | Infix, left-associative |
| `fx`  | Prefix, non-associative |
| `fy`  | Prefix, right-associative |
| `xf`  | Postfix, non-associative |
| `yf`  | Postfix, left-associative |

---

## ISO Operators by Precedence

### Precedence 1200

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `:-` | `xfx` | Clause definition |
| `:-` | `fx`  | Directive |
| `?-` | `fx`  | Query |

---

### Precedence 1100

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `;` | `xfy` | Disjunction |

---

### Precedence 1050

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `->` | `xfy` | If-then |
| `*->` | `xfy` | Soft cut if-then |

---

### Precedence 1000

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `,` | `xfy` | Conjunction |

---

### Precedence 900

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `\+` | `fy` | Negation as failure |

---

### Precedence 700

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `=` | `xfx` | Unification |
| `\=` | `xfx` | Not unifiable |
| `==` | `xfx` | Term identity |
| `\==` | `xfx` | Not identical |
| `@<` | `xfx` | Term less than |
| `@=<` | `xfx` | Term less or equal |
| `@>` | `xfx` | Term greater than |
| `@>=` | `xfx` | Term greater or equal |
| `=..` | `xfx` | Univ |
| `is` | `xfx` | Arithmetic evaluation |
| `=:=` | `xfx` | Arithmetic equality |
| `=\=` | `xfx` | Arithmetic inequality |
| `<` | `xfx` | Arithmetic less than |
| `=<` | `xfx` | Arithmetic less or equal |
| `>` | `xfx` | Arithmetic greater than |
| `>=` | `xfx` | Arithmetic greater or equal |

---

### Precedence 500

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `+` | `yfx` | Addition |
| `-` | `yfx` | Subtraction |

---

### Precedence 400

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `*` | `yfx` | Multiplication |
| `/` | `yfx` | Division |
| `//` | `yfx` | Integer division |
| `mod` | `yfx` | Modulo |
| `rem` | `yfx` | Remainder |

---

### Precedence 200

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `**` | `xfx` | Power |

---

### Precedence 200 (Prefix)

| Operator | Specifier | Description |
|--------|-----------|-------------|
| `+` | `fy` | Unary plus |
| `-` | `fy` | Unary minus |

---

## Minimal ISO Operator Declarations

```prolog
:- op(1200, xfx, ':-').
:- op(1200,  fx, ':-').
:- op(1200,  fx, '?-').
:- op(1100, xfy, ';').
:- op(1050, xfy, '->').
:- op(1050, xfy, '*->').
:- op(1000, xfy, ',').
:- op(900,  fy, '\+').
:- op(700,  xfx, [=, \=, ==, \==, @<, @=<, @>, @>=, =.., is, =:=, =\=, <, =<, >, >=]).
:- op(500,  yfx, [+,-]).
:- op(400,  yfx, [*, /, //, mod, rem]).
:- op(200,  xfx, '**').
:- op(200,   fy, [+,-]).
```

---

## Notes

- Precedence range is **1–1200**
- Operators are syntactic; semantics are provided by predicates
- `*->/2` is part of ISO Prolog
- `not/1` is **not** ISO (use `\+/1`)
- Lists are not operators in ISO
