"""Shared default operator definitions for Prolog parsing and semantics.

IMPORTANT: Reserved reader syntax operators (:-  ?-  ,  -->) are NOT included here.
These are handled at the grammar/reader layer (Layer 1) and cannot be redefined via op/3.

Layer 1 (Reader): Parses clause structure - :-  ?-  -->  ,  ()  []  {}
Layer 2 (Precedence): Parses term expressions using operators from this table

See docs/ARCHITECTURE.md "Reader vs. Operator Layers" for details.
"""

from __future__ import annotations

# Reserved syntax that is handled by the reader layer (not via operator precedence):
# - :- (directive/rule - infix xfx and prefix fx at precedence 1200)
# - ?- (query prefix - fx at precedence 1200)
# - --> (DCG arrow - xfx at precedence 1200)
# - , (conjunction - xfy at precedence 1000, but structural in args/goals)
# These MUST NOT be included in DEFAULT_OPERATORS since they are protected
# from redefinition via op/3 and parsed by dedicated grammar productions.

DEFAULT_OPERATORS: list[tuple[int, str, str]] = [
    # Note: :-, ?-, -->, and , are reserved reader syntax (Layer 1)
    # and are NOT included here. They are parsed by grammar productions
    # like rule, directive, query, goals, args, and dcg_rule.
    (1100, "xfy", ";"),
    (1050, "xfy", "->"),
    (900, "fy", "\\+"),
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
    (700, "fx", "non_counted_backtracking"),
    (600, "xfy", ":"),
    (500, "yfx", "+"),
    (500, "yfx", "-"),
    (500, "yfx", "/\\"),
    (500, "yfx", "\\/"),
    (400, "yfx", "*"),
    (400, "yfx", "/"),
    (400, "yfx", "//"),
    (400, "yfx", "<<"),
    (400, "yfx", ">>"),
    (400, "yfx", "div"),
    (400, "yfx", "mod"),
    (400, "yfx", "rem"),
    (400, "yfx", "rdiv"),
    (200, "xfx", "**"),
    (200, "xfy", "^"),
    (200, "fy", "+"),
    (200, "fy", "-"),
    (200, "fy", "\\"),
]

__all__ = ["DEFAULT_OPERATORS"]
