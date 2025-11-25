"""Prolog parser using Lark."""

from lark import Lark, Transformer
from lark.exceptions import LarkError
from dataclasses import dataclass
from typing import Any

from vibeprolog.exceptions import PrologError, PrologThrow
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


@dataclass
class Clause:
    """A Prolog clause (fact or rule)."""

    head: Compound
    body: list[Compound] | None = None  # None for facts

    def is_fact(self):
        return self.body is None

    def is_rule(self):
        return self.body is not None


@dataclass
class Directive:
    """A Prolog directive (e.g., :- initialization(goal).)."""

    goal: Any  # The goal term of the directive


# Lark grammar for Prolog
PROLOG_GRAMMAR = r"""
    start: (directive | clause)+

    clause: fact | rule
    fact: term "."
    rule: term RULE_OP goals "."
    directive: DIRECTIVE_OP term "."

    goals: term ("," term)*

    // Operator precedence (lowest to highest):
    // ; (or/semicolon) < -> (if-then) < , (and/comma) < comparisons < arithmetic

    term: or_term

    or_term: if_then_term (";" if_then_term)*

    if_then_term: and_term ("->" and_term)?

    and_term: comparison_term ("," comparison_term)*

    comparison_term: prefix_term (COMP_OP prefix_term)?

    prefix_term: PREFIX_OP prefix_term  -> prefix_op
        | expr

    expr: add_expr

    add_expr: mul_expr (ADD_OP mul_expr)*

    mul_expr: pow_expr (MUL_OP pow_expr)*

    pow_expr: primary (POW_OP primary)*

    primary: compound
        | curly_braces
        | string
        | cut
        | number
        | char_code
        | atom
        | variable
        | list
        | "(" term ")"

    compound: atom "(" args ")"
    args: comparison_term ("," comparison_term)*

    curly_braces: "{" term "}"

    COMP_OP: "=.." | "is" | "=" | "\\=" | "=:=" | "=\=" | "<" | ">" | "=<" | ">=" | "==" | "\\==" | "@<" | "@=<" | "@>" | "@>="
    PREFIX_OP.3: "\\+" | "+" | "-"
    ADD_OP: "+" | "-"
    POW_OP.2: "**"
    MUL_OP: "*" | "/" | "//" | "mod"

    list: "[" "]"                          -> empty_list
        | "[" list_items "]"               -> list_items_only
        | "[" list_items "|" comparison_term "]"      -> list_with_tail

    list_items: comparison_term ("," comparison_term)*

    string: STRING
    atom: ATOM | SPECIAL_ATOM | SPECIAL_ATOM_OPS
    variable: VARIABLE
    char_code: CHAR_CODE
    number: NUMBER
    cut: "!"

    // Character codes: 0'X where X is any character (must come before NUMBER)
    // Patterns: 0'a (simple char), 0'\\ (backslash), 0'\' (quote), 0''' (doubled quote), 0'\xHH (hex)
    CHAR_CODE.0: /0'\\x[0-9a-fA-F]+\\?/ | /0'./

    // Scientific notation, hex, octal, binary, base'digits
    NUMBER.4: /-?0x[0-9a-fA-F]+/i
             | /-?0o[0-7]+/i
             | /-?0b[01]+/i
             | /-?\d+\.?\d*[eE][+-]?\d+/
             | /-?\d+\.\d+/
             | /-?\.\d+/
             | /-?\d+'[a-zA-Z0-9_]+/
             | /-?\d+/

    STRING: /"([^"\\]|\\.)*"/ | /'(\\.|''|[^'\\])*'/
    SPECIAL_ATOM: /'([^'\\]|\\.)+'/
    SPECIAL_ATOM_OPS.5: /-\$/
    DIRECTIVE_OP: /:-/
    RULE_OP: /:-/
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

    def directive(self, items):
        return Directive(goal=items[1])

    def fact(self, items):
        return Clause(head=items[0], body=None)

    def rule(self, items):
        head, _, body = items
        return Clause(head=head, body=body)

    def goals(self, items):
        return items

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
        # items[0] is the operator, items[1] is the term
        op, term = items
        return Compound(str(op), (term,))

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

    def primary(self, items):
        return items[0]

    def compound(self, items):
        functor = items[0]
        args = items[1] if len(items) > 1 else []
        return Compound(functor.name, tuple(args))

    def args(self, items):
        return items

    def empty_list(self, items):
        return List(elements=())

    def list_items_only(self, items):
        return List(elements=tuple(items[0]))

    def list_with_tail(self, items):
        elements = items[0]
        tail = items[1]
        return List(elements=tuple(elements), tail=tail)

    def list_items(self, items):
        return items

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
        return Atom(s)

    def _unescape_string(self, s):
        """Handle backslash escape sequences."""
        # Process escape sequences in the correct order
        # Double backslash must be processed LAST to avoid interfering with other escapes
        # We use a placeholder to preserve \\

        # First, temporarily replace \\ with a placeholder
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
        elif "e" in value.lower() or "." in value:
            # Scientific notation or float
            return Number(float(value))
        else:
            # Regular integer
            return Number(int(value))

    def _parse_base_number(self, value):
        """Parse base'digits syntax like 16'ff or -2'abcd."""
        # Handle negative sign
        negative = value.startswith('-')
        if negative:
            value = value[1:]

        # Split by '
        parts = value.split("'", 1)
        base_str, digits_str = parts
        # Base must be a valid integer; token regex guarantees digits for base
        base = int(base_str)
        if base == 0:
            # This is 0'char syntax, treat as character code
            # Reconstruct the full string and call char_code
            full_value = ('-' if negative else '') + value
            return self.char_code([full_value])
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
                raise ValueError(f"Invalid digit '{digit}' for base {base} in {value}")
            result = result * base + digit_val

        if negative:
            result = -result

        return Number(result)

    def char_code(self, items):
        """Handle character code notation like 0'X or base'char"""
        code_str = str(items[0])

        # Check for base'char format (e.g., 16'mod'2)
        if "'" in code_str and not code_str.startswith("0'"):
            # This is base'char format - extract just the character
            parts = code_str.split("'")
            if len(parts) >= 2:
                if not parts[1]:
                    # This case, e.g., from `16''`, would cause `ord('')` to crash.
                    # Treating as an invalid char code for now to prevent a crash.
                    return Number(0)
                char = parts[1][0]
                return Number(ord(char))

        # Standard 0'X format
        if code_str.startswith("0'"):
            char_part = code_str[2:]

            # Handle doubled quote escape ''
            if char_part == "''":
                return Number(ord("'"))

            # Handle backslash escape sequences
            if char_part.startswith("\\"):
                if char_part.startswith("\\x"):
                    # Hex escape: \x41 or \x41\
                    if char_part.endswith("\\"):
                        hex_part = char_part[2:-1]  # Remove \x and trailing \
                    else:
                        hex_part = char_part[2:]  # Just remove \x

                    # Validate hex digits
                    if not hex_part:
                        from vibeprolog.errors import raise_syntax_error
                        raise_syntax_error("char_code/1", ValueError("empty hex sequence in character code"))

                    # Check for invalid hex digits
                    try:
                        # This will raise ValueError for invalid hex digits
                        int(hex_part, 16)
                    except ValueError as e:
                        from vibeprolog.errors import raise_syntax_error
                        raise_syntax_error("char_code/1", e)

                    return Number(int(hex_part, 16))
                elif char_part == "\\\\":
                    # Escaped backslash
                    return Number(ord("\\"))
                elif char_part == "\\'":
                    # Escaped single quote
                    return Number(ord("'"))
                elif len(char_part) >= 2:
                    # Other escape like \t, \n, etc - just use the second char
                    return Number(ord(char_part[1]))

            # Regular character
            if char_part:
                return Number(ord(char_part[0]))

        return Number(0)

    def curly_braces(self, items):
        """Handle curly braces {X} which is syntax sugar for {}(X)"""
        return Compound("{}", (items[0],))

    def cut(self, items):
        return Cut()


class PrologParser:
    """Parse Prolog source code."""

    def __init__(self):
        self.parser = Lark(
            PROLOG_GRAMMAR, parser="lalr", transformer=PrologTransformer()
        )

    def _strip_block_comments(self, text: str) -> str:
        """Strip block comments from text, handling nesting and quoted strings."""
        result = []
        i = 0
        in_single_quote = False
        in_double_quote = False
        escape_next = False
        while i < len(text):
            if not in_single_quote and not in_double_quote and text.startswith('/*', i):
                depth = 1
                i += 2
                while i < len(text) and depth > 0:
                    if text.startswith('/*', i):
                        depth += 1
                        i += 2
                    elif text.startswith('*/', i):
                        depth -= 1
                        i += 2
                    else:
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
        return ''.join(result)

    def parse(self, text: str, context: str = "parse/1") -> list[Clause | Directive]:
        """Parse Prolog source code and return list of clauses and directives."""
        try:
            text = self._strip_block_comments(text)
            return self.parser.parse(text)
        except LarkError as e:
            # Convert Lark parse error to Prolog syntax_error
            error_term = PrologError.syntax_error(str(e), context)
            raise PrologThrow(error_term)
        except ValueError as e:
            # Unterminated comment
            error_term = PrologError.syntax_error(str(e), context)
            raise PrologThrow(error_term)

    def parse_term(self, text: str, context: str = "parse_term/1") -> Any:
        """Parse a single Prolog term."""
        try:
            # Add a period to make it a valid clause
            text = self._strip_block_comments(f"dummy({text}).")
            result = self.parser.parse(text)
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
