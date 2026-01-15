"""Shared default operator definitions for Prolog parsing and semantics.

IMPORTANT: These precedence values are fixed by Scryer Prolog compatibility.
Do NOT change them unless Scryer changes.

The reserved reader syntax operators (:-, ?-, -->, ,) are included here for:
- current_op/3 compatibility
- Scryer Prolog compatibility
- Use in contexts where they appear as terms (e.g., functor names)

However, they are EXCLUDED from precedence-based term parsing (Layer 2).
They are parsed at the grammar level (Layer 1) by dedicated productions.
See generate_operator_rules() in parser.py for the exclusion logic.
"""

from __future__ import annotations

# IMPORTANT: These values match Scryer Prolog. Do not change unless Scryer changes.
#
# Layer 1 (Reader/Grammar): Handles clause structure via dedicated grammar productions.
#   - :- (directive/rule marker)
#   - ?- (query marker)
#   - --> (DCG arrow)
#   - , (conjunction in goals/args)
# These are parsed by grammar rules like `rule`, `directive`, `query`, `goals`, `args`,
# NOT via operator precedence. The generate_operator_rules() function excludes them
# from term-level operator grammar.
#
# Layer 2 (Precedence): All other operators are parsed via precedence rules.

DEFAULT_OPERATORS: list[tuple[int, str, str]] = [
    # Reserved reader syntax - parsed by grammar (Layer 1), not precedence (Layer 2)
    # These MUST remain here for current_op/3 and Scryer compatibility
    (1200, "xfx", ":-"),
    (1200, "fx", ":-"),
    (1200, "fx", "?-"),
    (1200, "xfx", "-->"),
    (1000, "xfy", ","),
    # Control operators
    (1100, "xfy", ";"),
    (1050, "xfy", "->"),
    (900, "fy", "\\+"),
    # Comparison operators
    (700, "xfx", "<"),
    (700, "xfx", "=<"),
    (700, "xfx", "="),
    (700, "xfx", "=\\="),
    (700, "xfx", "=.."),
    (700, "xfx", "=:="),
    (700, "xfx", ">="),
    (700, "xfx", ">"),
    (700, "xfx", "=="),
    (700, "xfx", "\\=="),
    (700, "xfx", "\\="),
    (700, "xfx", "@<"),
    (700, "xfx", "@=<"),
    (700, "xfx", "@>"),
    (700, "xfx", "@>="),
    (700, "xfx", "is"),
    (700, "xfx", "in"),   # CLP(Z) domain constraint
    (700, "xfx", "ins"),  # CLP(Z) list domain constraint
    (700, "fx", "non_counted_backtracking"),
    # Module qualification
    (600, "xfy", ":"),
    # Arithmetic operators
    (500, "yfx", "+"),
    (500, "yfx", "-"),
    (500, "yfx", "/\\"),
    (500, "yfx", "\\/"),
    # Range operator for CLP(Z)
    (450, "xfx", ".."),
    (400, "yfx", "*"),
    (400, "yfx", "/"),
    (400, "yfx", "//"),
    (400, "yfx", "<<"),
    (400, "yfx", ">>"),
    (400, "yfx", "div"),
    (400, "yfx", "mod"),
    (400, "yfx", "rem"),
    (400, "yfx", "rdiv"),
    (200, "xfy", "**"),
    (200, "xfy", "^"),
    (200, "fy", "+"),
    (200, "fy", "-"),
    # Note: (200, "fy", "\\") is NOT included - it conflicts with \+ at 900
    # LARL-work branch also doesn't include it
]

__all__ = ["DEFAULT_OPERATORS"]
