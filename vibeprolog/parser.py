"""Prolog parser using Lark."""

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError, UnexpectedCharacters, UnexpectedToken

from vibeprolog.exceptions import PrologError, PrologThrow
from vibeprolog.operator_defaults import DEFAULT_OPERATORS
from vibeprolog.terms import Atom, Variable, Number, Compound


@dataclass(frozen=True)
class List:
    """A list."""

    elements: tuple[Any, ...]
    tail: Any = None  # For [H|T] syntax

    def __repr__(self):
        if not self.elements and self.tail is None:
            return "[]"
        if self.tail is not None:
            elements_str = ", ".join(str(e) for e in self.elements)
            return f"[{elements_str}|{self.tail}]"
        elements_str = ", ".join(str(e) for e in self.elements)
        return f"[{elements_str}]"


@dataclass(frozen=True)
class Cut:
    """The cut operator (!)."""

    def __repr__(self):
        return "!"


@dataclass(frozen=True)
class ParenthesizedComma(Compound):
    """Marker type for comma terms wrapped in parentheses to prevent flattening."""


@dataclass
class Clause:
    """A Prolog clause (fact or rule)."""

    head: Compound
    body: list[Compound] | None = None  # None for facts
    doc: str | None = None  # PlDoc documentation
    meta: Any = None  # Lark meta information
    dcg: bool = False  # True for DCG rules

    def is_fact(self):
        return self.body is None

    def is_rule(self):
        return self.body is not None


@dataclass
class Directive:
    """A Prolog directive (e.g., :- initialization(goal).)."""

    goal: Any  # The directive term, e.g., initialization(goal)
    doc: str | None = None  # PlDoc documentation
    meta: Any = None  # Lark meta information


@dataclass
class PredicateIndicator:
    """A predicate indicator Name/Arity."""

    name: Any
    arity: Any


@dataclass
class PredicatePropertyDirective:
    """Directive declaring predicate properties such as dynamic/1."""

    property: str
    indicators: tuple[PredicateIndicator, ...]


# Lark grammar for Prolog
PROLOG_GRAMMAR = r"""
    start: (clause | directive)+

    clause: rule | dcg_rule | fact
    fact: term "."
    rule: term ":-" goals "."
    dcg_rule: term DCG_ARROW goals "."
    atom_or_compound: atom
        | atom "(" args ")"

    directive: ":-" (op_directive | prefix_directive | property_directive | term) "."

    prefix_directive: "dynamic" predicate_indicators -> dynamic_directive
        | "multifile" predicate_indicators -> multifile_directive
        | "discontiguous" predicate_indicators -> discontiguous_directive

    property_directive: "dynamic" "(" predicate_indicators ")"    -> dynamic_directive
        | "multifile" "(" predicate_indicators ")"   -> multifile_directive
        | "discontiguous" "(" predicate_indicators ")" -> discontiguous_directive

    op_directive: "op" "(" number "," ATOM "," op_arg_list ")" -> op_directive

    op_arg_list: op_symbol_or_atom
        | "[" op_symbol_or_atom ("," op_symbol_or_atom)* "]" -> op_arg_list_items

    // operator symbol or atom for op/3 - avoid parsing as expressions
    op_symbol_or_atom: OP_SYMBOL_DIRECTIVE | OP_SYMBOL | ATOM | SPECIAL_ATOM | OPERATOR_ATOM

    // Operator symbols - must match complete sequences before breaking into component operators
    // Priority set to ensure special atoms like -$ are recognized, but still below SPECIAL_ATOM_OPS
    OP_SYMBOL_DIRECTIVE.25: /[+\-*\/<>=\\@#$&!~:?^.]+/
    OP_SYMBOL: /[+\-*\/<>=\\@#$&!~:?^.]+/

    predicate_indicators: term ("," term)*

    goals: term ("," term)*

__OPERATOR_GRAMMAR__

    primary: SPECIAL_ATOM_OPS -> special_atom_token
        | operator_atom
        | operator_compound
        | compound
        | curly_braces
        | string
        | cut
        | char_code
        | number
        | "-" number -> negative_number
        | atom
        | variable
        | list
        | "(" operator_as_atom ")"          -> parenthesized_operator_atom
        | "(" term ")"                     -> parenthesized_term

    compound: atom "(" args ")"
    // Allow operator symbols as functors: ;(a,b), |(a,b), ,(a,b), ->(a,b), etc.
    operator_compound: operator_functor "(" args ")" -> operator_compound
    // Operators that can be used as functors when followed by (
    operator_functor: INFIX_OP_FUNCTOR | CONTROL_OP_FUNCTOR | COMPARISON_OP_FUNCTOR | ARITH_OP_FUNCTOR | OP_SYMBOL
    // Infix operators like ;, |, ,, ->, etc.
    INFIX_OP_FUNCTOR.30: /;/ | /\|/ | /,/ | /->/ | /:/ | /=/ 
    // Control operators
    CONTROL_OP_FUNCTOR.30: /\\+/
    // Comparison operators - but not < and > alone as they're in OP_SYMBOL
    COMPARISON_OP_FUNCTOR.30: /=:=/ | /=\\=/ | /=</ | />=/ | /=@=/ | /\\=@=/ | /==/ | /\\==/
    // Arithmetic operators that can also be prefix/postfix - must be followed by ( for functor use
    ARITH_OP_FUNCTOR.30: /\+/ | /-/ | /\*/ | /\//
    // Parenthesized operator as atom: (;), (|), (,), (->), etc.
    operator_as_atom: INFIX_OP_FUNCTOR | CONTROL_OP_FUNCTOR | COMPARISON_OP_FUNCTOR | ARITH_OP_FUNCTOR | OP_SYMBOL
    operator_atom: OPERATOR_ATOM
    args: term ("," term)*

    curly_braces: "{" term "}"

    DCG_ARROW.35: "-->"
    OPERATOR_ATOM.35: ":-"

    list: "[" "]"                          -> empty_list
        | "[" list_items "]"               -> list_items_only
        | "[" list_items "|" term "]"      -> list_with_tail

    list_items: term ("," term)*

    string: STRING
    atom: ATOM | SPECIAL_ATOM | SPECIAL_ATOM_OPS | OP_SYMBOL
    variable: VARIABLE
    char_code: CHAR_CODE
    number: NUMBER
    cut: "!"

    // Character codes: 0'X where X is any character (must come before NUMBER)
    // Patterns: 0'a (simple char), 0'\\ (backslash), 0'\' (quote), 0''' (doubled quote), 0'\xHH (hex)
    // Allow trailing quote (e.g., 0'\\') while keeping legacy forms without it; allow broader alphanumerics after \\x so lexer does not reject malformed hex sequences that should become syntax errors
    CHAR_CODE.5: /0'(\\x[0-9a-zA-Z]+\\?|\\\\|\\\\['tnr]|''|[^'\\])'?/ | /[1-9]\d*'.'/

    STRING: /"([^"\\]|\\.*)*"/ | /'([^'\\]|\\.*|'')*'/
    SPECIAL_ATOM: /'([^'\\]|\\.)+'/

    // Special atom operators must have HIGHEST priority to prevent being parsed as prefix operators
    SPECIAL_ATOM_OPS.12: /-\$/ | /\$-/

    // Scientific notation, hex, octal, binary, Edinburgh <radix>'<number>
    NUMBER.4: /-?0x[0-9a-fA-F]+/i
            | /-?0o[0-7]+/i
            | /-?0b[01]+/i
            | /-?[\d_]+\.?[\d_]*[eE][+-]?[\d_]+/
            | /-?[\d_]+\.[\d_]+/
            | /-?\.[\d_]+/
            | /-?\d+['][a-zA-Z0-9_]+/
            | /-?(?=[\d_]*\d)[\d_]+/

    ATOM: /[a-z][a-zA-Z0-9_]*/ | /\{\}/ | /\$[a-zA-Z0-9_-]*/ | /[+\-*\/]/

    VARIABLE: /[A-Z_][a-zA-Z0-9_]*/

    %import common.WS
    %ignore WS
    %ignore /%.*/  // Line comments
"""


class PrologTransformer(Transformer):
    """Transform parse tree into AST."""

    def __init__(self):
        super().__init__()
        self._anon_counter = 0

    def start(self, items):
        return items

    def clause(self, items):
        return items[0]

    def atom_or_compound(self, items):
        if len(items) == 1:
            return items[0]  # Just an atom
        else:
            # atom "(" args ")"
            atom = items[0]
            args = items[1]
            return Compound(atom.name, tuple(args))

    @v_args(meta=True)
    def directive(self, meta, items):
        return Directive(goal=items[0], meta=meta)

    def predicate_indicators(self, items):
        return items

    def dynamic_directive(self, items):
        indicators = self._flatten_comma_separated(items[0])
        return PredicatePropertyDirective("dynamic", tuple(indicators))

    def multifile_directive(self, items):
        indicators = self._flatten_comma_separated(items[0])
        return PredicatePropertyDirective("multifile", tuple(indicators))

    def discontiguous_directive(self, items):
        indicators = self._flatten_comma_separated(items[0])
        return PredicatePropertyDirective("discontiguous", tuple(indicators))

    def op_directive(self, items):
        """Handle op/3 directive: op(Precedence, Type, Name).
        
        Creates a Compound term op(Prec, Type, Name) that the engine will process.
        """
        # items[0] = number (precedence)
        # items[1] = atom (type: xfx, yfx, etc.) - raw token
        # items[2] = op_arg_list (either single atom or list of atoms)
        precedence = items[0]
        op_type_token = items[1]
        op_names = items[2]
        
        # Convert operator type token to Atom
        op_type = Atom(str(op_type_token))
        
        # op_names is either a single Atom or a list of Atoms
        if isinstance(op_names, list):
            # op_arg_list_items case - convert to list representation
            return Compound("op", (precedence, op_type, List(elements=tuple(op_names))))
        else:
            # Single op_symbol_or_atom case
            return Compound("op", (precedence, op_type, op_names))

    def op_arg_list(self, items):
        """Handle operator argument list - either single or bracketed list."""
        return items[0]

    def op_arg_list_items(self, items):
        """Handle list of operators: [op1, op2, ...]"""
        return items

    def op_symbol_or_atom(self, items):
        """Operator symbol or atom - convert raw token to Atom."""
        token = items[0]
        if isinstance(token, Atom):
            return token
        else:
            # Raw token from OP_SYMBOL, ATOM, SPECIAL_ATOM, or OPERATOR_ATOM
            s = str(token)
            # Remove quotes if present (for SPECIAL_ATOM)
            if (s.startswith("'") and s.endswith("'")):
                s = s[1:-1]
                # In Prolog, single quotes are escaped by doubling them
                s = s.replace("''", "'")
            return Atom(s)

    def _flatten_comma_separated(self, items):
        """Flatten comma-separated predicates into a list.

        If items is a list with a single Compound with functor ',',
        unwrap it into a flat list of indicators.
        """
        if isinstance(items, ParenthesizedComma):
            items = Compound(items.functor, items.args)
        if isinstance(items, Compound) and items.functor == ',':
            return self._collect_comma_terms(items)
        if isinstance(items, (list, tuple)) and len(items) == 1:
            return self._flatten_comma_separated(items[0])
        if isinstance(items, (list, tuple)):
            return items
        return [items]

    def _collect_comma_terms(self, compound):
        """Recursively collect terms from a comma compound."""
        if isinstance(compound, ParenthesizedComma):
            return [Compound(compound.functor, compound.args)]
        if isinstance(compound, Compound) and compound.functor == ',':
            left = self._collect_comma_terms(compound.args[0])
            right = self._collect_comma_terms(compound.args[1])
            return left + right
        else:
            return [compound]

    @v_args(meta=True)
    def fact(self, meta, items):
        return Clause(head=items[0], body=None, meta=meta)

    @v_args(meta=True)
    def rule(self, meta, items):
        head, body = items
        return Clause(head=head, body=body, meta=meta)

    @v_args(meta=True)
    def dcg_rule(self, meta, items):
        head = items[0]
        body = items[-1]
        return Clause(head=head, body=body, dcg=True, meta=meta)

    def goals(self, items):
        # Flatten any comma compounds in the goal list
        # This handles cases where ambiguous parsing creates comma compounds
        result = []
        for item in items:
            if isinstance(item, ParenthesizedComma):
                item = Compound(item.functor, item.args)
            if isinstance(item, Compound) and item.functor == ',':
                result.extend(self._collect_comma_terms(item))
            else:
                result.append(item)
        return result

    def term(self, items):
        return items[0]

    def or_term(self, items):
        if len(items) == 1:
            return items[0]
        # Build right-associative tree for disjunction
        result = items[-1]
        for i in range(len(items) - 2, -1, -1):
            result = Compound(";", (items[i], result))
        return result

    def if_then_term(self, items):
        if len(items) == 1:
            return items[0]
        # items[0] -> items[1]
        return Compound("->", (items[0], items[1]))

    def and_term(self, items):
        if len(items) == 1:
            return items[0]
        # Build right-associative tree for conjunction
        result = items[-1]
        for i in range(len(items) - 2, -1, -1):
            result = Compound(",", (items[i], result))
        return result

    def comparison_term(self, items):
        if len(items) == 1:
            return items[0]
        left, op, right = items
        return Compound(str(op), (left, right))

    def prefix_term(self, items):
        return items[0]

    def prefix_op(self, items):
        # items can be [op, term] or just [term] depending on the rule
        if len(items) == 2:
            op, term = items
            return self._apply_prefix_operator(op, term)
        else:
            # For "-" prefix_term rule, items is just [term]
            # The "-" is implicit in the rule
            term = items[0]
            return self._apply_prefix_operator("-", term)

    def _apply_prefix_operator(self, op, term):
        op_str = str(op)
        if op_str == "-":
            if isinstance(term, Number):
                return Number(-term.value)
            if isinstance(term, Compound) and term.functor == "-" and len(term.args) == 1:
                inner = term.args[0]
                if isinstance(inner, Number):
                    return inner
        return Compound(op_str, (term,))

    def module_term(self, items):
        # Module qualification: left:right (right-associative)
        if len(items) == 1:
            return items[0]
        left = items[0]
        right = items[1]
        return Compound(":", (left, right))

    def expr(self, items):
        return items[0]

    def add_expr(self, items):
        if len(items) == 1:
            return items[0]
        # Build left-associative tree
        result = items[0]
        for i in range(1, len(items), 2):
            op = items[i]
            right = items[i + 1]
            result = Compound(str(op), (result, right))
        return result

    def infix_xfx(self, items):
        left, op, right = items
        return Compound(str(op), (left, right))

    def infix_yfx(self, items):
        left, op, right = items
        return Compound(str(op), (left, right))

    def infix_xfy(self, items):
        left, op, right = items
        return Compound(str(op), (left, right))

    def infix_yfy(self, items):
        left, op, right = items
        return Compound(str(op), (left, right))

    def prefix_fx(self, items):
        op, term = items
        return self._apply_prefix_operator(op, term)

    def prefix_fy(self, items):
        op, term = items
        return self._apply_prefix_operator(op, term)

    def postfix_xf(self, items):
        term, op = items
        return Compound(str(op), (term,))

    def postfix_yf(self, items):
        term, op = items
        return Compound(str(op), (term,))

    def mul_expr(self, items):
        if len(items) == 1:
            return items[0]
        # Build left-associative tree
        result = items[0]
        for i in range(1, len(items), 2):
            op = items[i]
            right = items[i + 1]
            result = Compound(str(op), (result, right))
        return result

    def pow_expr(self, items):
        if len(items) == 1:
            return items[0]
        # Build right-associative tree for exponentiation
        result = items[-1]
        for i in range(len(items) - 2, -1, -2):
            if i > 0:
                result = Compound(str(items[i]), (items[i - 1], result))
        if len(items) % 2 == 0:
            # If even number of items, first item hasn't been added yet
            result = Compound(str(items[1]), (items[0], result))
        return result

    def unary_expr(self, items):
        return items[0]

    def primary(self, items):
        return items[0]

    def parenthesized_term(self, items):
        term = items[0]
        if isinstance(term, Compound) and term.functor == ',':
            return ParenthesizedComma(term.functor, term.args)
        return term

    def special_atom_token(self, items):
        """Convert SPECIAL_ATOM_OPS token to an Atom."""
        token_str = str(items[0])
        return Atom(token_str)

    def parenthesized_operator_atom(self, items):
        """Handle parenthesized operator as atom: (;), (|), (,), (->), etc."""
        token_str = str(items[0])
        return Atom(token_str)

    def operator_as_atom(self, items):
        """Convert operator token to Atom."""
        token_str = str(items[0])
        return Atom(token_str)

    def operator_functor(self, items):
        """Convert operator token to Atom for use as functor."""
        token_str = str(items[0])
        return Atom(token_str)

    def operator_compound(self, items):
        """Handle operator as functor: ;(a, b), |(a, b), etc."""
        functor = items[0]
        args = items[1] if len(items) > 1 else []
        if isinstance(functor, Atom):
            return Compound(functor.name, tuple(args))
        return Compound(str(functor), tuple(args))

    def compound(self, items):
        functor = items[0]
        args = items[1] if len(items) > 1 else []
        return Compound(functor.name, tuple(args))

    def args(self, items):
        expanded: list[Any] = []
        for item in items:
            if isinstance(item, ParenthesizedComma):
                expanded.append(Compound(item.functor, item.args))
                continue

            if isinstance(item, Compound) and item.functor == ',':
                expanded.extend(self._collect_comma_terms(item))
                continue

            if isinstance(item, Compound):
                normalized_args = tuple(
                    Compound(arg.functor, arg.args)
                    if isinstance(arg, ParenthesizedComma)
                    else arg
                    for arg in item.args
                )
                item = Compound(item.functor, normalized_args)
            expanded.append(item)
        return expanded

    def empty_list(self, items):
        return List(elements=())

    def list_items_only(self, items):
        return List(elements=tuple(items[0]))

    def list_with_tail(self, items):
        elements = items[0]
        tail = items[1]
        return List(elements=tuple(elements), tail=tail)

    def list_items(self, items):
        expanded: list[Any] = []
        for item in items:
            if isinstance(item, Compound) and item.functor == ',':
                expanded.extend(self._collect_comma_terms(item))
            else:
                expanded.append(item)
        return expanded

    def string(self, items):
        # Remove quotes from the string (both double and single quotes)
        s = str(items[0])
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
            # Handle escape sequences in double-quoted strings
            s = self._unescape_string(s)
        elif s.startswith("'") and s.endswith("'"):
            s = s[1:-1]
            # In Prolog, single quotes are escaped by doubling them
            s = s.replace("''", "'")
            # Also handle backslash escapes
            s = self._unescape_string(s)
        return Atom(s, quoted=True)

    def _parse_octal_escape(self, match):
        """Parse octal escape sequence like \101\ into character."""
        inner = match.group(1)
        try:
            value = int(inner, 8)
            if value > 255:
                raise PrologThrow(PrologError.syntax_error("octal escape overflow", "escape_sequence/1"))
            return chr(value)
        except ValueError:
            raise PrologThrow(PrologError.syntax_error("invalid octal escape", "escape_sequence/1"))

    def _unescape_string(self, s):
        """Handle backslash escape sequences."""
        # Process escape sequences in the correct order
        # Double backslash must be processed LAST to avoid interfering with other escapes
        # We use a placeholder to preserve \\

        # First, handle octal escapes
        s = re.sub(r'\\(\d{1,3})\\', self._parse_octal_escape, s)

        # Then, temporarily replace \\ with a placeholder
        placeholder = "\x00BACKSLASH\x00"
        s = s.replace(r"\\", placeholder)

        # Now handle other escape sequences
        replacements = {
            r"\'": "'",
            r"\"": '"',
            r"\n": "\n",
            r"\t": "\t",
            r"\r": "\r",
        }
        for escaped, unescaped in replacements.items():
            s = s.replace(escaped, unescaped)

        # Finally, replace placeholder with single backslash
        s = s.replace(placeholder, "\\")

        return s

    def atom(self, items):
        atom_str = str(items[0])
        # Handle SPECIAL_ATOM (quoted atoms like ';', '|', etc.)
        if atom_str.startswith("'") and atom_str.endswith("'") and len(atom_str) >= 2:
            # Strip the quotes and handle escape sequences
            atom_str = atom_str[1:-1]
            # In Prolog, single quotes are escaped by doubling them
            atom_str = atom_str.replace("''", "'")
            # Handle backslash escapes
            atom_str = self._unescape_string(atom_str)
        return Atom(atom_str)

    def operator_atom(self, items):
        return Atom(str(items[0]))

    def variable(self, items):
        var_name = str(items[0])
        # Each anonymous variable _ should be unique
        if var_name == "_":
            unique_name = f"_G{self._anon_counter}"
            self._anon_counter += 1
            return Variable(unique_name)
        return Variable(var_name)

    def number(self, items):
        value = str(items[0])
        # Handle hex, octal, binary
        if value.startswith(("-0x", "0x")) or value.startswith(("-0X", "0X")):
            # Hex number
            return Number(int(value, 16))
        elif value.startswith(("-0o", "0o")) or value.startswith(("-0O", "0O")):
            # Octal number
            return Number(int(value, 8))
        elif value.startswith(("-0b", "0b")) or value.startswith(("-0B", "0B")):
            # Binary number
            return Number(int(value, 2))
        elif "'" in value:
            # Base'digits syntax
            return self._parse_base_number(value)
        # Validate underscores and strip them for numeric conversion
        self._validate_underscore_placement(value)
        clean_value = value.replace('_', '')
        if "e" in value.lower() or "." in value:
            # Scientific notation or float
            return Number(float(clean_value))
        else:
            # Regular integer
            return Number(int(clean_value))

    def negative_number(self, items):
        # The grammar rule `primary: "-" number -> negative_number` ensures
        # that the number has already been transformed into a Number object.
        num = items[-1]
        assert isinstance(num, Number), f"Expected Number, got {type(num).__name__}"
        return Number(-num.value)

    def _validate_underscore_placement(self, value: str, special_chars: str = ".eE+-") -> None:
        """Validate underscore placement in number strings."""
        if '_' not in value:
            return
        # No leading or trailing underscores
        if value.startswith('_') or value.endswith('_'):
            raise PrologThrow(PrologError.syntax_error("invalid underscore placement", "number/1"))
        # No double underscores
        if '__' in value:
            raise PrologThrow(PrologError.syntax_error("invalid underscore placement", "number/1"))
        # No underscores adjacent to special characters
        for char in special_chars:
            if f'_{char}' in value or f'{char}_' in value:
                raise PrologThrow(PrologError.syntax_error("invalid underscore placement", "number/1"))

    def _parse_base_number(self, value):
        """Parse Edinburgh <radix>'<number> syntax like 16'ff or -2'abcd.

        Edinburgh syntax: <radix>'<number> where:
        - <radix> is the base (2-36)
        - <number> is the digits in that base

        Examples: 16'ff' (hex), 2'1010' (binary), 36'ZZZ' (base-36)
        """
        # Validate underscores in Edinburgh-style base numbers
        self._validate_underscore_placement(value, special_chars="'")
        # Handle negative sign
        negative = value.startswith('-')
        if negative:
            value = value[1:]

        # Split by '
        parts = value.split("'", 1)
        base_str, digits_str = parts
        # Base must be a valid integer; token regex guarantees digits for base
        base = int(base_str)
        if not (2 <= base <= 36):
            raise ValueError(f"Base must be between 2 and 36, got {base}")

        # Remove underscores from digits
        digits_clean = digits_str.replace('_', '')

        if not digits_clean:
            raise ValueError(f"Empty digits in {value}")

        # Validate and accumulate value
        result = 0
        for digit in digits_clean.lower():
            # Convert single digit in base up to 36
            digit_val = int(digit, 36)
            if digit_val >= base:
                raise ValueError(f"Invalid digit '{digit}' for radix {base} in Edinburgh syntax: {value}")
            result = result * base + digit_val

        if negative:
            result = -result

        return Number(result)

    def char_code(self, items):
        """Handle character code notation like 0'X.

        Note: base'char'number syntax (e.g., 16'mod'2) is intentionally not implemented.
        """
        code_str = str(items[0])

        # Check for base'char format (e.g., 16'mod'2)
        if "'" in code_str and not code_str.startswith("0'"):
            # This is base'char format - extract just the character
            parts = code_str.split("'")
            if len(parts) >= 2:
                if not parts[1]:
                    # Empty character code - reject as syntax error
                    raise ValueError("unexpected_char")
                char = parts[1][0]
                return Number(ord(char))

        # Standard 0'X format
        if code_str.startswith("0'"):
            char_part = code_str[2:]

            # Strip a trailing quote used as a closing delimiter, but keep escapes that
            # intentionally include a quote character ('' or \\').
            if (
                len(char_part) > 1
                and char_part.endswith("'")
                and char_part not in {"''", "\\'"}
            ):
                char_part = char_part[:-1]

            # Reject empty character codes, including 0''
            if not char_part or char_part == "'" or char_part == "''":
                raise ValueError("unexpected_char")

            # Handle backslash escape sequences
            if char_part.startswith("\\"):
                if char_part.startswith("\\x"):
                    match = re.fullmatch(r"\\x([0-9a-fA-F]*)\\?", char_part)
                    if not match:
                        raise ValueError("unexpected_char")

                    hex_digits = match.group(1)
                    if len(hex_digits) < 2:
                        raise ValueError("incomplete_reduction")

                    try:
                        return Number(int(hex_digits, 16))
                    except ValueError as exc:
                        raise ValueError("unexpected_char") from exc

                if char_part == "\\\\":
                    # Escaped backslash
                    return Number(ord("\\"))
                if char_part == "\\'":
                    # Escaped single quote
                    return Number(ord("'"))

                if len(char_part) >= 2:
                    # Other escape like \t, \n, etc - just use the second char
                    return Number(ord(char_part[1]))

                raise ValueError("unexpected_char")

            # Regular character
            if char_part:
                return Number(ord(char_part[0]))

        raise ValueError("unexpected_char")

    def curly_braces(self, items):
        """Handle curly braces {X} which is syntax sugar for {}(X)"""
        return Compound("{}", (items[0],))

    def cut(self, items):
        return Cut()


def tokenize_prolog_statements(prolog_code: str) -> list[str]:
    """Split Prolog code into individual clause/directive strings.

    Handles quoted strings, comments, and decimal points in numbers to avoid
    splitting valid clauses. Each returned string ends with a period.
    """
    chunks = []
    current: list[str] = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = 0
    escape_next = False
    has_code = False
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0

    while i < len(prolog_code):
        char = prolog_code[i]

        # Handle line comments
        if in_line_comment:
            current.append(char)
            if char == '\n':
                in_line_comment = False
            i += 1
            continue

        # Handle block comments
        if in_block_comment > 0:
            current.append(char)
            if prolog_code[i:i+2] == '/*':
                in_block_comment += 1
                current.append(prolog_code[i+1])
                i += 2
                continue
            if prolog_code[i:i+2] == '*/':
                in_block_comment -= 1
                current.append(prolog_code[i+1])
                i += 2
                continue
            i += 1
            continue

        # Handle escape sequences
        if escape_next:
            current.append(char)
            escape_next = False
            i += 1
            continue

        if char == '\\' and (in_single_quote or in_double_quote):
            current.append(char)
            escape_next = True
            i += 1
            continue

        # Handle entering/exiting quotes
        if char == "'" and not in_double_quote:
            has_code = True
            # Check for doubled quote
            if in_single_quote and i + 1 < len(prolog_code) and prolog_code[i + 1] == "'":
                current.append(char)
                current.append(prolog_code[i + 1])
                i += 2
                continue
            in_single_quote = not in_single_quote
            current.append(char)
            i += 1
            continue

        if char == '"' and not in_single_quote:
            has_code = True
            in_double_quote = not in_double_quote
            current.append(char)
            i += 1
            continue

        # Check for comment starts
        if not in_single_quote and not in_double_quote:
            if char == '%':
                in_line_comment = True
                current.append(char)
                i += 1
                continue
            if prolog_code[i:i+2] == '/*':
                in_block_comment = 1
                current.append(char)
                current.append(prolog_code[i+1])
                i += 2
                continue

        # Track nesting depth for parentheses, brackets, braces
        if not in_single_quote and not in_double_quote:
            if char == '(':
                paren_depth += 1
            elif char == ')' and paren_depth > 0:
                paren_depth -= 1
            elif char == '[':
                bracket_depth += 1
            elif char == ']' and bracket_depth > 0:
                bracket_depth -= 1
            elif char == '{':
                brace_depth += 1
            elif char == '}' and brace_depth > 0:
                brace_depth -= 1

        # Handle period (end of clause)
        if char == '.' and not in_single_quote and not in_double_quote and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            # Check for ... (ellipsis) or .. (range operator)
            if prolog_code[i:i+3] == '...':
                current.append('.')
                current.append('.')
                current.append('.')
                has_code = True
                i += 3
                continue
            if prolog_code[i:i+2] == '..':
                current.append('.')
                current.append('.')
                has_code = True
                i += 2
                continue
            current.append(char)
            # Heuristic to check if this period is part of a number (e.g., 1.2 or 1.)
            # to avoid splitting clauses incorrectly.
            is_decimal_point = (i > 0 and prolog_code[i-1].isdigit()) or \
                                (i + 1 < len(prolog_code) and prolog_code[i+1].isdigit())
            if is_decimal_point:
                i += 1
                continue
            # End of clause
            if has_code:
                chunks.append(''.join(current))
            current = []
            has_code = False
            i += 1
            continue

        if not char.isspace():
            has_code = True

        current.append(char)
        i += 1

    # Check for unclosed comments or strings at end of code
    if in_block_comment > 0:
        raise ValueError("Unterminated block comment")
    if in_single_quote:
        raise ValueError("Unterminated quoted atom")
    if in_double_quote:
        raise ValueError("Unterminated string")
    
    # Add any remaining content (should not happen in well-formed code)
    if current:
        remainder = ''.join(current).strip()
        if remainder and has_code:
            chunks.append(remainder)
    
    return chunks


def _strip_quotes(token: str) -> str:
    if token.startswith("'") and token.endswith("'"):
        inner = token[1:-1]
        return inner.replace("''", "'")
    elif token.startswith('"') and token.endswith('"'):
        inner = token[1:-1]
        return inner.replace('\\"', '"').replace('\\\\', '\\')
    return token


def _split_top_level_commas(text: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    in_single = False
    in_double = False
    escape_next = False

    for ch in text:
        if escape_next:
            current.append(ch)
            escape_next = False
            continue

        if ch == "\\" and (in_single or in_double):
            current.append(ch)
            escape_next = True
            continue

        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
            continue

        if ch in "([{" and not in_single and not in_double:
            depth += 1
        elif ch in ")]}" and not in_single and not in_double and depth > 0:
            depth -= 1

        if ch == "," and not in_single and not in_double and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue

        current.append(ch)

    if current:
        parts.append("".join(current).strip())
    return parts


def _parse_operator_name_list(raw: str) -> list[str]:
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        entries = _split_top_level_commas(inner)
    else:
        entries = [raw]

    operators: list[str] = []
    for entry in entries:
        if not entry:
            continue
        operators.append(_strip_quotes(entry))
    return operators


def _strip_comments(text: str) -> str:
    """Strip line and block comments from text, preserving content inside quoted strings.
    
    Args:
        text: Prolog source code that may contain comments
        
    Returns:
        Text with comments removed
    """
    result = []
    i = 0
    in_single_quote = False
    in_double_quote = False
    escape_next = False
    block_depth = 0
    
    while i < len(text):
        char = text[i]
        
        if escape_next:
            if block_depth == 0:
                result.append(char)
            escape_next = False
            i += 1
            continue
        
        if char == '\\' and (in_single_quote or in_double_quote):
            if block_depth == 0:
                result.append(char)
            escape_next = True
            i += 1
            continue
        
        # Handle block comments
        if block_depth > 0:
            if text[i:i+2] == '/*':
                block_depth += 1
                i += 2
                continue
            if text[i:i+2] == '*/':
                block_depth -= 1
                i += 2
                continue
            i += 1
            continue
        
        if char == "'" and not in_double_quote:
            # Check for doubled quote escape inside single-quoted strings
            if in_single_quote and i + 1 < len(text) and text[i + 1] == "'":
                result.append(char)
                result.append(text[i + 1])
                i += 2
                continue
            in_single_quote = not in_single_quote
            result.append(char)
            i += 1
            continue
        
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            result.append(char)
            i += 1
            continue
        
        # Check for comment starts outside quoted strings
        if not in_single_quote and not in_double_quote:
            # Check for block comment start
            if text[i:i+2] == '/*':
                block_depth = 1
                i += 2
                continue
            # Check for line comment
            if char == '%':
                # Skip until end of line
                while i < len(text) and text[i] != '\n':
                    i += 1
                # Skip the newline if present
                if i < len(text) and text[i] == '\n':
                    result.append('\n')
                    i += 1
                continue
        
        result.append(char)
        i += 1
    
    return ''.join(result)


def extract_op_directives(source: str) -> list[tuple[int, str, str]]:
    """Extract op/3 directives from source code, including operators in module export lists.

    Args:
        source: Prolog source code string

    Returns:
        List of (precedence, type, operator) tuples, in order of appearance
    """

    operators: list[tuple[int, str, str]] = []
    directive_pattern = re.compile(r"^\s*:-\s*op\s*\((.*)\)\s*\.$", re.DOTALL)
    module_pattern = re.compile(r"^\s*:-\s*module\s*\(\s*([^,]+)\s*,\s*\[(.*)\]\s*\)\s*\.$", re.DOTALL)

    def _try_parse_op(op_args_str: str):
        """Helper to parse op/3 arguments and add to operators list."""
        args = _split_top_level_commas(op_args_str)
        if len(args) != 3:
            return
        try:
            precedence = int(args[0].strip())
        except ValueError:
            return
        op_type = _strip_quotes(args[1].strip())
        operator_names = _parse_operator_name_list(args[2].strip())
        for op_name in operator_names:
            operators.append((precedence, op_type, op_name))

    for statement in tokenize_prolog_statements(source):
        # Strip comments before matching to handle block comments at start of statement
        stripped = _strip_comments(statement).strip()
        
        # Check for op/3 directives
        match = directive_pattern.match(stripped)
        if match:
            _try_parse_op(match.group(1))
            continue

        # Check for module/2 with op/3 in export list
        match = module_pattern.match(stripped)
        if match:
            exports_str = match.group(2)
            export_items = _split_top_level_commas(exports_str)
            for item in export_items:
                item = item.strip()
                if item.startswith("op(") and item.endswith(")"):
                    op_content = item[3:-1]  # Remove "op(" and ")"
                    _try_parse_op(op_content)

    return operators


def escape_for_lark(s: str) -> str:
    """Escape special characters for use in Lark grammar.
    
    Args:
        s: String to escape
        
    Returns:
        Escaped string safe for Lark grammar
    """
    # Escape backslashes and quotes
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    return s


VALID_OPERATOR_SPECS = {"xfx", "xfy", "yfx", "yfy", "fx", "fy", "xf", "yf"}


def _format_operator_literals(ops: Iterable[str]) -> str:
    # Sort longest operators first so sequences like "\\+" take precedence over
    # shorter prefixes such as "\\".
    formatted: list[str] = []
    for op in sorted(set(ops), key=lambda value: (-len(value), value)):
        if re.match(r"^[A-Za-z0-9_]+$", op):
            formatted.append(f"/(?<![A-Za-z0-9_]){re.escape(op)}(?![A-Za-z0-9_])/")
        else:
            formatted.append(f'"{escape_for_lark(op)}"')
    return " | ".join(formatted)


def _merge_operators(
    base_ops: Iterable[tuple[int, str, str]], directives: list[tuple[int, str, str]]
) -> list[tuple[int, str, str]]:
    table: dict[tuple[str, str], int] = {}
    for precedence, spec, name in base_ops:
        if spec not in VALID_OPERATOR_SPECS:
            continue
        table[(name, spec)] = precedence

    for precedence, spec, name in directives:
        if spec not in VALID_OPERATOR_SPECS:
            continue
        key = (name, spec)
        if precedence == 0:
            table.pop(key, None)
        else:
            table[key] = precedence

    merged: list[tuple[int, str, str]] = []
    for (name, spec), precedence in table.items():
        merged.append((precedence, spec, name))
    merged.sort(key=lambda item: (item[0], item[1], item[2]))
    return merged


def generate_operator_rules(operators: list[tuple[int, str, str]]) -> str:
    """Generate grammar rules for operators ordered by precedence.

    ISO Prolog uses 1 as highest precedence. The generated rules build from
    highest binding (small number) to lowest (large number) so the resulting
    ``term`` rule respects the intended precedence tree.
    """

    if not operators:
        return "    ?term: primary\n"

    grouped: dict[int, dict[str, list[str]]] = defaultdict(
        lambda: {"prefix": defaultdict(list), "infix": defaultdict(list), "postfix": defaultdict(list)}
    )

    for precedence, spec, name in operators:
        if spec in {"fx", "fy"}:
            grouped[precedence]["prefix"][spec].append(name)
        elif spec in {"xf", "yf"}:
            grouped[precedence]["postfix"][spec].append(name)
        else:
            grouped[precedence]["infix"][spec].append(name)

    rules: list[str] = []
    tokens: list[str] = []

    lower_rule = "primary"
    precedence_levels = sorted(grouped.keys())

    token_counter = 0

    for precedence in precedence_levels:
        rule_name = f"level_{precedence}"
        parts = [lower_rule]
        infix_specs = grouped[precedence]["infix"]
        prefix_specs = grouped[precedence]["prefix"]
        postfix_specs = grouped[precedence]["postfix"]

        if infix_specs.get("xfx"):
            for name in sorted(infix_specs["xfx"]):
                token_counter += 1
                token = f"INFIX_XFX_{precedence}_{token_counter}"
                priority = len(name)
                token_def = f"{token}.{priority}" if priority else token
                tokens.append(f"    {token_def}: {_format_operator_literals([name])}")
                parts.append(f"{lower_rule} {token} {lower_rule} -> infix_xfx")
        if infix_specs.get("yfx"):
            for name in sorted(infix_specs["yfx"]):
                token_counter += 1
                token = f"INFIX_YFX_{precedence}_{token_counter}"
                priority = len(name)
                token_def = f"{token}.{priority}" if priority else token
                tokens.append(f"    {token_def}: {_format_operator_literals([name])}")
                parts.append(f"{rule_name} {token} {lower_rule} -> infix_yfx")
        if infix_specs.get("xfy"):
            for name in sorted(infix_specs["xfy"]):
                token_counter += 1
                token = f"INFIX_XFY_{precedence}_{token_counter}"
                priority = len(name)
                token_def = f"{token}.{priority}" if priority else token
                tokens.append(f"    {token_def}: {_format_operator_literals([name])}")
                parts.append(f"{lower_rule} {token} {rule_name} -> infix_xfy")
        if infix_specs.get("yfy"):
            for name in sorted(infix_specs["yfy"]):
                token_counter += 1
                token = f"INFIX_YFY_{precedence}_{token_counter}"
                priority = len(name)
                token_def = f"{token}.{priority}" if priority else token
                tokens.append(f"    {token_def}: {_format_operator_literals([name])}")
                parts.append(f"{rule_name} {token} {rule_name} -> infix_yfy")

        if prefix_specs.get("fx"):
            for name in sorted(prefix_specs["fx"]):
                token_counter += 1
                token = f"PREFIX_FX_{precedence}_{token_counter}"
                priority = len(name)
                token_def = f"{token}.{priority}" if priority else token
                tokens.append(f"    {token_def}: {_format_operator_literals([name])}")
                parts.append(f"{token} {lower_rule} -> prefix_fx")
        if prefix_specs.get("fy"):
            for name in sorted(prefix_specs["fy"]):
                token_counter += 1
                token = f"PREFIX_FY_{precedence}_{token_counter}"
                priority = len(name)
                token_def = f"{token}.{priority}" if priority else token
                tokens.append(f"    {token_def}: {_format_operator_literals([name])}")
                parts.append(f"{token} {rule_name} -> prefix_fy")

        if postfix_specs.get("xf"):
            for name in sorted(postfix_specs["xf"]):
                token_counter += 1
                token = f"POSTFIX_XF_{precedence}_{token_counter}"
                priority = len(name)
                token_def = f"{token}.{priority}" if priority else token
                tokens.append(f"    {token_def}: {_format_operator_literals([name])}")
                parts.append(f"{lower_rule} {token} -> postfix_xf")
        if postfix_specs.get("yf"):
            for name in sorted(postfix_specs["yf"]):
                token_counter += 1
                token = f"POSTFIX_YF_{precedence}_{token_counter}"
                priority = len(name)
                token_def = f"{token}.{priority}" if priority else token
                tokens.append(f"    {token_def}: {_format_operator_literals([name])}")
                parts.append(f"{rule_name} {token} -> postfix_yf")

        rule_body = "\n        | ".join(parts)
        rules.append(f"?{rule_name}: {rule_body}")
        lower_rule = rule_name

    rules.append(f"?term: {lower_rule}")
    rules.extend(tokens)

    return "\n".join(rules) + "\n"


class PrologParser:
    """Parse Prolog source code with support for dynamic operators."""

    def __init__(self, operator_table=None):
        self.operator_table = operator_table
        # Character conversion table: maps single chars to single chars
        # Initially identity (no conversions active)
        self._char_conversions: dict[str, str] = {}
        self._grammar_cache = {}  # Cache compiled grammars by operator set
        self.parser = None

    def set_char_conversion(self, from_char: str, to_char: str) -> None:
        """Set a character conversion.
        
        If from_char == to_char, removes the conversion (identity mapping).
        Otherwise, adds/updates the conversion.
        """
        if from_char == to_char:
            # Identity conversion: remove from table
            self._char_conversions.pop(from_char, None)
        else:
            self._char_conversions[from_char] = to_char

    def get_char_conversions(self) -> dict[str, str]:
        """Return copy of current character conversion table."""
        return dict(self._char_conversions)

    def convert_atom_name(self, name: str) -> str:
        """Apply character conversions to an atom/functor name."""
        if not self._char_conversions:
            return name
        return ''.join(self._char_conversions.get(ch, ch) for ch in name)

    def _apply_char_conversions(self, text: str) -> str:
        """Apply character conversions to text, excluding quoted strings.
        
        Per ISO Prolog, character conversions apply to source text but NOT
        to the contents of quoted atoms or strings.
        """
        if not self._char_conversions:
            return text
        
        result = []
        i = 0
        in_single_quote = False
        in_double_quote = False
        escape_next = False
        
        while i < len(text):
            char = text[i]
            
            if escape_next:
                result.append(char)
                escape_next = False
                i += 1
                continue
            
            if char == '\\' and (in_single_quote or in_double_quote):
                result.append(char)
                escape_next = True
                i += 1
                continue
            
            if char == "'" and not in_double_quote:
                # Check for doubled quote escape inside single-quoted strings
                if in_single_quote and i + 1 < len(text) and text[i + 1] == "'":
                    result.append(char)
                    result.append(text[i + 1])
                    i += 2
                    continue
                in_single_quote = not in_single_quote
                result.append(char)
                i += 1
                continue
            
            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                result.append(char)
                i += 1
                continue
            
            # Apply conversion only outside quoted strings
            if not in_single_quote and not in_double_quote:
                char = self._char_conversions.get(char, char)
            
            result.append(char)
            i += 1
        
        return ''.join(result)

    def _create_parser(self, grammar: str):
        return Lark(
            grammar, parser="earley", propagate_positions=True, ambiguity='resolve'
        )

    def _base_operator_definitions(
        self, module_name: str | None = None
    ) -> list[tuple[int, str, str]]:
        if self.operator_table is None:
            return list(DEFAULT_OPERATORS)
        # Use module-aware operator iteration to include shadowed operators
        return [
            (info.precedence, info.spec, name)
            for name, info in self.operator_table.iter_operators_for_module(module_name)
        ]

    def _build_grammar(self, operators: list[tuple[int, str, str]]) -> str:
        operator_rules = generate_operator_rules(operators)
        return PROLOG_GRAMMAR.replace("__OPERATOR_GRAMMAR__", operator_rules)

    def _ensure_parser(
        self,
        cleaned_text: str,
        directive_ops: list[tuple[int, str, str]] | None = None,
        module_name: str | None = None,
    ) -> None:
        if directive_ops is None:
            try:
                directive_ops = extract_op_directives(cleaned_text)
            except ValueError:
                directive_ops = []
        operators = _merge_operators(
            self._base_operator_definitions(module_name), directive_ops
        )
        grammar = self._build_grammar(operators)
        key = grammar
        if key not in self._grammar_cache:
            self._grammar_cache[key] = self._create_parser(grammar)
        self.parser = self._grammar_cache[key]

    def _strip_block_comments(self, text: str) -> tuple[str, list[tuple[int, str]]]:
        """Strip block comments from text, handling nesting and quoted strings.
        Returns cleaned text and list of (position, pldoc_comment) tuples."""
        result = []
        pldoc_comments = []
        i = 0
        in_single_quote = False
        in_double_quote = False
        escape_next = False
        while i < len(text):
            if not in_single_quote and not in_double_quote and (text.startswith('/*', i) or text.startswith('/**', i) or text.startswith('/*!', i)):
                comment_start = i
                depth = 1
                if text.startswith('/**', i) or text.startswith('/*!', i):
                    i += 3  # Skip /** or /*!
                    is_pldoc = True
                else:
                    i += 2  # Skip /*
                    is_pldoc = False
                comment_content = []
                while i < len(text) and depth > 0:
                    if text.startswith('/*', i):
                        depth += 1
                        i += 2
                    elif text.startswith('*/', i):
                        depth -= 1
                        if depth == 0:
                            # End of comment
                            if is_pldoc:
                                pldoc_comments.append((comment_start, ''.join(comment_content)))
                            i += 2
                            break
                        else:
                            i += 2
                    else:
                        if is_pldoc:
                            comment_content.append(text[i])
                        i += 1
                if depth > 0:
                    raise ValueError("Unterminated block comment")
                continue  # Skip the comment

            char = text[i]
            result.append(char)

            if escape_next:
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote

            i += 1
        return ''.join(result), pldoc_comments

    def _collect_pldoc_comments(self, text: str) -> tuple[str, list[tuple[int, str]]]:
        """Collect PlDoc comments and return cleaned text with positions in cleaned text."""
        pldoc_comments = []
        cleaned = []
        i = 0
        in_single_quote = False
        in_double_quote = False
        escape_next = False
        while i < len(text):
            if not in_single_quote and not in_double_quote:
                if text.startswith('%%', i):
                    # Line comment
                    pos = len(''.join(cleaned))  # position in cleaned text
                    # Find end of line
                    end = text.find('\n', i)
                    if end == -1:
                        end = len(text)
                    comment = text[i+2:end].rstrip('\n')
                    pldoc_comments.append((pos, comment))
                    i = end + 1 if end < len(text) else len(text)
                    continue
                elif text.startswith('/*', i):
                    # Block comment
                    pos = len(''.join(cleaned))
                    is_pldoc = text.startswith('/**', i) or text.startswith('/*!', i)
                    i += 3 if is_pldoc else 2
                    comment_content = []
                    depth = 1
                    while i < len(text) and depth > 0:
                        if text.startswith('/*', i):
                            depth += 1
                            i += 2
                        elif text.startswith('*/', i):
                            depth -= 1
                            if depth == 0:
                                if is_pldoc:
                                    pldoc_comments.append((pos, ''.join(comment_content)))
                                i += 2
                                break
                            else:
                                i += 2
                        else:
                            if is_pldoc:
                                comment_content.append(text[i])
                            i += 1
                    if depth > 0:
                        raise ValueError("Unterminated block comment")
                    continue
            # Not in comment, add char
            cleaned.append(text[i])
            if escape_next:
                escape_next = False
            elif text[i] == '\\':
                escape_next = True
            elif text[i] == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif text[i] == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            i += 1
        cleaned_text = ''.join(cleaned)
        pldoc_comments.sort(key=lambda x: x[0])
        return cleaned_text, pldoc_comments

    def _associate_pldoc_comments(self, items: list, comments: list[tuple[int, str]]):
        """Associate PlDoc comments with clauses/directives."""
        if not comments:
            return

        # Robust association: attach each comment to the next item by source position.
        # We rely on Lark's propagate_positions to furnish item.meta.start_pos where available.
        entities: list[tuple[int, str, object]] = []
        for pos, text in comments:
            entities.append((pos, 'comment', text))
        for item in items:
            start_pos = getattr(item.meta, 'start_pos', None) if hasattr(item, 'meta') else None
            if start_pos is not None:
                entities.append((start_pos, 'item', item))

        entities.sort(key=lambda x: x[0])
        last_comment_text: str | None = None
        for _, entity_type, payload in entities:
            if entity_type == 'comment':
                last_comment_text = payload
            elif entity_type == 'item':
                if last_comment_text is not None:
                    payload.doc = last_comment_text
                last_comment_text = None

    def parse(
        self,
        text: str,
        context: str = "parse/1",
        *,
        apply_char_conversions: bool = True,
        directive_ops: list[tuple[int, str, str]] | None = None,
        module_name: str | None = None,
    ) -> list[Clause | Directive]:
        """Parse Prolog source code and return list of clauses.

        Args:
            text: The Prolog source code to parse
            context: Context string for error messages
            apply_char_conversions: Whether to apply character conversions
            directive_ops: Pre-extracted operator directives
            module_name: Current module context for module-scoped operators
        """
        try:
            # Apply character conversions before parsing
            if apply_char_conversions:
                text = self._apply_char_conversions(text)
            cleaned_text, pldoc_comments = self._collect_pldoc_comments(text)
            self._ensure_parser(cleaned_text, directive_ops, module_name)
            tree = self.parser.parse(cleaned_text)
            transformer = PrologTransformer()
            parsed_items = [self._fold_numeric_unary_minus(item) for item in transformer.transform(tree)]
            # Associate PlDoc comments with items
            self._associate_pldoc_comments(parsed_items, pldoc_comments)
            return parsed_items
        except (UnexpectedToken, UnexpectedCharacters) as e:
            # If the lexer/parser choked inside a char code hex escape like 0'\x4G,
            # surface the ISO-style unexpected_char error rather than the raw Lark token message.
            last_token = getattr(e, "token_history", None)
            if last_token:
                last_token = last_token[-1]
                if getattr(last_token, "type", None) == "CHAR_CODE" and str(last_token).startswith(
                    "0'\\x"
                ):
                    error_term = PrologError.syntax_error("unexpected_char", context)
                    raise PrologThrow(error_term)
            error_term = PrologError.syntax_error(str(e), context)
            # We handle these specific Lark errors here so they are normalized to
            # `PrologThrow` before control leaves the try; otherwise the outer
            # `LarkError` handler never runs and tests break.
            raise PrologThrow(error_term)
        except LarkError as e:
            # Convert Lark parse error to Prolog syntax_error
            error_term = PrologError.syntax_error(str(e), context)
            raise PrologThrow(error_term)
        except ValueError as e:
            # Unterminated comment
            error_term = PrologError.syntax_error(str(e), context)
            raise PrologThrow(error_term)

    def _fold_numeric_unary_minus(self, term):
        """Normalize unary minus applications to numeric literals."""

        if isinstance(term, Clause):
            head = self._fold_numeric_unary_minus(term.head)
            body = None
            if term.body is not None:
                body = [self._fold_numeric_unary_minus(goal) for goal in term.body]
            return Clause(head, body, term.doc, term.meta, term.dcg)

        if isinstance(term, Directive):
            goal = self._fold_numeric_unary_minus(term.goal)
            return Directive(goal, term.doc, term.meta)

        if isinstance(term, List):
            elements = tuple(self._fold_numeric_unary_minus(e) for e in term.elements)
            tail = None if term.tail is None else self._fold_numeric_unary_minus(term.tail)
            return List(elements, tail)

        if isinstance(term, Compound):
            args = tuple(self._fold_numeric_unary_minus(arg) for arg in term.args)
            if term.functor == "-" and len(args) == 1 and isinstance(args[0], Number):
                return Number(-args[0].value)
            return Compound(term.functor, args)

        return term

    def parse_term(
        self,
        text: str,
        context: str = "parse_term/1",
        *,
        apply_char_conversions: bool = True,
    ) -> Any:
        """Parse a single Prolog term."""
        try:
            # Add a period to make it a valid clause
            clause_text = f"dummy({text})."
            if apply_char_conversions:
                clause_text = self._apply_char_conversions(clause_text)
            cleaned_text, _ = self._collect_pldoc_comments(clause_text)
            self._ensure_parser(cleaned_text)
            tree = self.parser.parse(cleaned_text)
            transformer = PrologTransformer()
            result = transformer.transform(tree)
            if result and isinstance(result[0], Clause):
                compound = result[0].head
                if isinstance(compound, Compound) and compound.args:
                    return compound.args[0]
            raise ValueError(f"Failed to parse term: {text}")
        except LarkError as e:
            # Convert Lark parse error to Prolog syntax_error
            error_term = PrologError.syntax_error(str(e), context)
            raise PrologThrow(error_term)
        except ValueError as e:
            # Unterminated comment or parse error
            error_term = PrologError.syntax_error(str(e), context)
            raise PrologThrow(error_term)
