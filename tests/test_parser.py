"""Tests for the Prolog parser."""

import pytest
from vibeprolog.parser import (
    PrologParser, Clause, Compound, Atom, Variable, Number, List, Cut, tokenize_prolog_statements
)
from vibeprolog.exceptions import PrologThrow
from vibeprolog import PrologInterpreter


class TestBasicParsing:
    """Tests for basic parsing of atoms, variables, and numbers."""

    def test_parse_fact_with_atom(self):
        """Test parsing a simple fact."""
        parser = PrologParser()
        clauses = parser.parse("foo.")
        assert len(clauses) == 1
        assert isinstance(clauses[0], Clause)
        assert clauses[0].is_fact()
        assert isinstance(clauses[0].head, Atom)
        assert clauses[0].head.name == "foo"

    def test_parse_fact_with_compound(self):
        """Test parsing a fact with compound term."""
        parser = PrologParser()
        clauses = parser.parse("person(john, 25).")
        assert len(clauses) == 1
        clause = clauses[0]
        assert clause.is_fact()
        assert isinstance(clause.head, Compound)
        assert clause.head.functor == "person"
        assert len(clause.head.args) == 2
        assert isinstance(clause.head.args[0], Atom)
        assert clause.head.args[0].name == "john"
        assert isinstance(clause.head.args[1], Number)
        assert clause.head.args[1].value == 25

    def test_parse_variable(self):
        """Test parsing variables."""
        parser = PrologParser()
        clauses = parser.parse("test(X, Y).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Variable)
        assert clause.head.args[0].name == "X"
        assert isinstance(clause.head.args[1], Variable)
        assert clause.head.args[1].name == "Y"

    def test_parse_integer(self):
        """Test parsing integers."""
        parser = PrologParser()
        clauses = parser.parse("num(42).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 42

    def test_parse_float(self):
        """Test parsing floats."""
        parser = PrologParser()
        clauses = parser.parse("pi(3.14).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 3.14

    def test_parse_negative_number(self):
        """Test parsing negative numbers."""
        parser = PrologParser()
        clauses = parser.parse("neg(-42).")
        clause = clauses[0]
        # -42 is parsed as a unary minus operation
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == -42

    def test_parse_spaced_negative_number(self):
        """Ensure unary minus folds numbers even when spaced."""
        parser = PrologParser()
        clauses = parser.parse("neg(- 42).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == -42

    def test_parse_double_negation(self):
        """Double unary minus should fold to a positive number."""
        parser = PrologParser()
        clauses = parser.parse("test(- - 42).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 42

    def test_parse_decimal_starting_with_dot(self):
        """Test parsing numbers starting with decimal point (e.g., .5, .10)."""
        parser = PrologParser()
        # Test positive decimal starting with dot
        clauses = parser.parse("test(.5).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 0.5

        # Test in arithmetic expression
        clauses = parser.parse("test(X) :- X is .25 + .75.")
        clause = clauses[0]
        is_expr = clause.body[0]
        assert is_expr.functor == "is"
        # Check that the arithmetic expression contains the decimal numbers
        add_expr = is_expr.args[1]
        assert add_expr.functor == "+"
        assert isinstance(add_expr.args[0], Number)
        assert add_expr.args[0].value == 0.25
        assert isinstance(add_expr.args[1], Number)
        assert add_expr.args[1].value == 0.75


class TestRules:
    """Tests for parsing rules."""

    def test_parse_simple_rule(self):
        """Test parsing a simple rule."""
        parser = PrologParser()
        clauses = parser.parse("parent(X) :- father(X).")
        assert len(clauses) == 1
        clause = clauses[0]
        assert clause.is_rule()
        assert isinstance(clause.head, Compound)
        assert clause.head.functor == "parent"
        assert len(clause.body) == 1
        assert isinstance(clause.body[0], Compound)
        assert clause.body[0].functor == "father"

    def test_parse_rule_with_multiple_goals(self):
        """Test parsing a rule with multiple goals."""
        parser = PrologParser()
        clauses = parser.parse("grandparent(X, Z) :- parent(X, Y), parent(Y, Z).")
        clause = clauses[0]
        assert clause.is_rule()
        # The body is a list of goals (flattened, not a conjunction tree)
        assert len(clause.body) == 2
        assert isinstance(clause.body[0], Compound)
        assert clause.body[0].functor == "parent"
        assert isinstance(clause.body[1], Compound)
        assert clause.body[1].functor == "parent"

    def test_parse_rule_with_arithmetic(self):
        """Test parsing a rule with arithmetic."""
        parser = PrologParser()
        clauses = parser.parse("double(X, Y) :- Y is X * 2.")
        clause = clauses[0]
        assert clause.is_rule()
        assert len(clause.body) == 1
        body_goal = clause.body[0]
        assert isinstance(body_goal, Compound)
        assert body_goal.functor == "is"


class TestLists:
    """Tests for parsing lists."""

    def test_parse_empty_list(self):
        """Test parsing an empty list."""
        parser = PrologParser()
        clauses = parser.parse("empty([]).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], List)
        assert len(clause.head.args[0].elements) == 0

    def test_parse_list_with_elements(self):
        """Test parsing a list with elements."""
        parser = PrologParser()
        clauses = parser.parse("nums([1, 2, 3]).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], List)
        assert len(clause.head.args[0].elements) == 3
        assert all(isinstance(e, Number) for e in clause.head.args[0].elements)

    def test_parse_list_with_head_tail(self):
        """Test parsing list with head|tail syntax."""
        parser = PrologParser()
        clauses = parser.parse("split([H|T]).")
        clause = clauses[0]
        lst = clause.head.args[0]
        assert isinstance(lst, List)
        assert len(lst.elements) == 1
        assert isinstance(lst.elements[0], Variable)
        assert lst.elements[0].name == "H"
        assert isinstance(lst.tail, Variable)
        assert lst.tail.name == "T"

    def test_parse_list_mixed_types(self):
        """Test parsing a list with mixed types."""
        parser = PrologParser()
        clauses = parser.parse("mixed([1, foo, X]).")
        clause = clauses[0]
        lst = clause.head.args[0]
        assert isinstance(lst.elements[0], Number)
        assert isinstance(lst.elements[1], Atom)
        assert isinstance(lst.elements[2], Variable)


class TestArithmetic:
    """Tests for parsing arithmetic expressions."""

    def test_parse_addition(self):
        """Test parsing addition."""
        parser = PrologParser()
        clauses = parser.parse("test(X) :- X is 2 + 3.")
        clause = clauses[0]
        is_expr = clause.body[0]
        assert is_expr.functor == "is"
        rhs = is_expr.args[1]
        assert isinstance(rhs, Compound)
        assert rhs.functor == "+"

    def test_parse_multiplication(self):
        """Test parsing multiplication."""
        parser = PrologParser()
        clauses = parser.parse("test(X) :- X is 4 * 5.")
        clause = clauses[0]
        is_expr = clause.body[0]
        rhs = is_expr.args[1]
        assert rhs.functor == "*"

    def test_parse_division(self):
        """Test parsing division."""
        parser = PrologParser()
        clauses = parser.parse("test(X) :- X is 10 / 2.")
        clause = clauses[0]
        is_expr = clause.body[0]
        rhs = is_expr.args[1]
        assert rhs.functor == "/"

    def test_parse_complex_arithmetic(self):
        """Test parsing complex arithmetic expression."""
        parser = PrologParser()
        clauses = parser.parse("test(X) :- X is (2 + 3) * 4.")
        clause = clauses[0]
        is_expr = clause.body[0]
        rhs = is_expr.args[1]
        # Should parse as multiplication with addition as left operand
        assert isinstance(rhs, Compound)


class TestComparisons:
    """Tests for parsing comparison operators."""

    def test_parse_equals(self):
        """Test parsing = operator."""
        parser = PrologParser()
        clauses = parser.parse("test :- X = 5.")
        clause = clauses[0]
        assert clause.body[0].functor == "="

    def test_parse_arithmetic_equal(self):
        """Test parsing =:= operator."""
        parser = PrologParser()
        clauses = parser.parse("test :- 5 =:= 5.")
        clause = clauses[0]
        assert clause.body[0].functor == "=:="

    def test_parse_less_than(self):
        """Test parsing < operator."""
        parser = PrologParser()
        clauses = parser.parse("test :- 3 < 5.")
        clause = clauses[0]
        assert clause.body[0].functor == "<"

    def test_parse_greater_than(self):
        """Test parsing > operator."""
        parser = PrologParser()
        clauses = parser.parse("test :- 5 > 3.")
        clause = clauses[0]
        assert clause.body[0].functor == ">"


class TestControlStructures:
    """Tests for parsing control structures."""

    @pytest.mark.larl_exclude
    def test_parse_cut(self):
        """Test parsing the cut operator."""
        parser = PrologParser()
        clauses = parser.parse("test :- !.")
        clause = clauses[0]
        assert isinstance(clause.body[0], Cut)

    def test_parse_conjunction(self):
        """Test parsing conjunction (comma)."""
        parser = PrologParser()
        clauses = parser.parse("test :- foo, bar.")
        clause = clauses[0]
        # Body is a list of flattened goals
        assert len(clause.body) == 2
        assert isinstance(clause.body[0], Atom)
        assert clause.body[0].name == "foo"
        assert isinstance(clause.body[1], Atom)
        assert clause.body[1].name == "bar"

    def test_parse_parenthesized_conjunction(self):
        """Test parsing parenthesized conjunction."""
        parser = PrologParser()
        clauses = parser.parse("test(A, B) :- (A, B).")
        clause = clauses[0]
        # Parenthesized conjunction is flattened (syntactically equivalent)
        assert len(clause.body) == 2
        assert isinstance(clause.body[0], Variable)
        assert clause.body[0].name == 'A'
        assert isinstance(clause.body[1], Variable)
        assert clause.body[1].name == 'B'

    def test_parse_if_then(self):
        """Test parsing if-then (->)."""
        parser = PrologParser()
        clauses = parser.parse("test :- foo -> bar.")
        clause = clauses[0]
        assert len(clause.body) == 1
        if_then = clause.body[0]
        assert isinstance(if_then, Compound)
        assert if_then.functor == "->"

    def test_parse_if_then_else(self):
        """Test parsing if-then-else (-> and ;)."""
        parser = PrologParser()
        clauses = parser.parse("test :- (foo -> bar ; baz).")
        clause = clauses[0]
        assert len(clause.body) == 1
        or_expr = clause.body[0]
        assert isinstance(or_expr, Compound)
        assert or_expr.functor == ";"

    def test_parse_disjunction(self):
        """Test parsing disjunction (;)."""
        parser = PrologParser()
        clauses = parser.parse("test :- foo ; bar.")
        clause = clauses[0]
        assert len(clause.body) == 1
        disj = clause.body[0]
        assert isinstance(disj, Compound)
        assert disj.functor == ";"


class TestMultipleClauses:
    """Tests for parsing multiple clauses."""

    def test_parse_multiple_facts(self):
        """Test parsing multiple facts."""
        parser = PrologParser()
        clauses = parser.parse("""
            parent(john, mary).
            parent(john, tom).
            parent(susan, mary).
        """)
        assert len(clauses) == 3
        assert all(c.is_fact() for c in clauses)
        assert all(c.head.functor == "parent" for c in clauses)

    def test_parse_facts_and_rules(self):
        """Test parsing a mix of facts and rules."""
        parser = PrologParser()
        clauses = parser.parse("""
            father(john).
            mother(mary).
            parent(X) :- father(X).
            parent(X) :- mother(X).
        """)
        assert len(clauses) == 4
        assert clauses[0].is_fact()
        assert clauses[1].is_fact()
        assert clauses[2].is_rule()
        assert clauses[3].is_rule()


class TestComments:
    """Tests for parsing comments."""

    def test_ignore_line_comments(self):
        """Test that line comments are ignored."""
        parser = PrologParser()
        clauses = parser.parse("""
            % This is a comment
            parent(john, mary).
            % Another comment
        """)
        assert len(clauses) == 1
        assert clauses[0].head.functor == "parent"

    def test_inline_comments(self):
        """Test inline comments."""
        parser = PrologParser()
        clauses = parser.parse("parent(john, mary). % This is Mary's parent")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "parent"

    def test_ignore_block_comments(self):
        """Test that block comments are ignored."""
        parser = PrologParser()
        clauses = parser.parse("""
            /* This is a block comment */
            parent(john, mary).
        """)
        assert len(clauses) == 1
        assert clauses[0].head.functor == "parent"

    def test_block_comments_adjacent_to_tokens(self):
        """Test block comments adjacent to tokens."""
        parser = PrologParser()
        clauses = parser.parse("parent/*comment*/(john, mary).")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "parent"

    def test_nested_block_comments(self):
        """Test nested block comments."""
        parser = PrologParser()
        clauses = parser.parse("""
            /* /* nested */ comment */
            parent(john, mary).
        """)
        assert len(clauses) == 1
        assert clauses[0].head.functor == "parent"

    def test_deeply_nested_block_comments(self):
        """Test deeply nested block comments."""
        parser = PrologParser()
        clauses = parser.parse("""
            /* /* /* deep */ nested */ comment */
            parent(john, mary).
        """)
        assert len(clauses) == 1
        assert clauses[0].head.functor == "parent"

    def test_unterminated_block_comment(self):
        """Test unterminated block comment raises error."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="Unterminated block comment"):
            parser.parse("/* unterminated parent(john, mary).")

    def test_block_comment_with_newlines(self):
        """Test block comments spanning multiple lines."""
        parser = PrologParser()
        clauses = parser.parse("""
            /*
             * Multi-line
             * block comment
             */
            parent(john, mary).
        """)
        assert len(clauses) == 1
        assert clauses[0].head.functor == "parent"

    def test_block_comment_in_string(self):
        parser = PrologParser()
        clauses = parser.parse("write('/* not comment */').")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "write"
        # Further assert the atom argument contains '/* not comment */'
        assert clauses[0].head.args[0].name == "/* not comment */"

    def test_block_comment_touching_atom_start(self):
        """Block comment immediately after atom start."""
        parser = PrologParser()
        clauses = parser.parse("atom/*comment*/.")
        assert len(clauses) == 1
        assert clauses[0].head.name == "atom"

    def test_block_comment_touching_atom_end(self):
        """Block comment immediately before atom end."""
        parser = PrologParser()
        clauses = parser.parse("/*comment*/atom.")
        assert len(clauses) == 1
        assert clauses[0].head.name == "atom"

    def test_block_comment_touching_operator(self):
        """Block comment adjacent to operator - needs space before graphic operators.
        
        Per ISO Prolog, '=/*' forms a graphic token because '=' is a graphic char.
        Use spaces between operators and comments for portability.
        """
        parser = PrologParser()
        # With spaces around operator - this works correctly
        clauses = parser.parse("X /* comment */ = /* comment */ 5.")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "="
        assert clauses[0].head.args[0].name == "X"
        assert clauses[0].head.args[1] == Number(5)

    def test_block_comment_touching_eof(self):
        """Block comment at end of input - needs space after period.
        
        Per ISO Prolog, '.' followed directly by '/*' forms a graphic token './'.
        A space is required between the clause terminator and the comment.
        """
        parser = PrologParser()
        # With space between period and comment - this works
        clauses = parser.parse("fact. /*comment*/")
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"

    def test_block_comment_with_quotes_and_operators(self):
        """Block comment containing quotes and operators."""
        parser = PrologParser()
        clauses = parser.parse("/* 'quote' + - */fact.")
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"


class TestStrings:
    """Tests for parsing strings."""

    def test_parse_string(self):
        """Test parsing a string."""
        parser = PrologParser()
        clauses = parser.parse('greeting("Hello, World!").')
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Atom)
        assert clause.head.args[0].name == "Hello, World!"

    def test_parse_empty_string(self):
        """Test parsing an empty string."""
        parser = PrologParser()
        clauses = parser.parse('empty("").')
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Atom)
        assert clause.head.args[0].name == ""


class TestEdinburghRadixNumber:
    """Tests for parsing Edinburgh <radix>'<number> syntax.

    Edinburgh syntax allows arbitrary base numbers: <radix>'<number>
    Examples: 16'ff' (hex), 2'1010' (binary), 36'ZZZ' (base-36)
    """

    def test_parse_hex_base16(self):
        """Test parsing hexadecimal with base 16."""
        parser = PrologParser()
        clauses = parser.parse("num(16'ff).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 255

    def test_parse_binary_base2(self):
        """Test parsing binary with base 2."""
        parser = PrologParser()
        clauses = parser.parse("num(2'1010).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 10

    def test_parse_decimal_base10(self):
        """Test parsing decimal with base 10."""
        parser = PrologParser()
        clauses = parser.parse("num(10'123).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 123

    def test_parse_base36_max(self):
        """Test parsing with maximum base 36."""
        parser = PrologParser()
        clauses = parser.parse("num(36'z).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 35

    def test_parse_negative_edinburgh_syntax(self):
        """Test parsing negative Edinburgh <radix>'<number> syntax."""
        parser = PrologParser()
        clauses = parser.parse("num(-16'ff).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == -255

    def test_parse_with_underscores(self):
        """Test parsing with underscores for readability."""
        parser = PrologParser()
        clauses = parser.parse("num(16'f_f).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 255

    def test_parse_case_insensitive_digits(self):
        """Test that digits are case insensitive."""
        parser = PrologParser()
        clauses = parser.parse("num(16'FF).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 255

    def test_parse_mixed_case_digits(self):
        """Test mixed case digits."""
        parser = PrologParser()
        clauses = parser.parse("num(16'AbCd).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        # A=10, b=11, C=12, d=13: 10*16^3 + 11*16^2 + 12*16 + 13 = 40960 + 2816 + 192 + 13 = 43981
        assert clause.head.args[0].value == 10*4096 + 11*256 + 12*16 + 13

    def test_invalid_base_too_low(self):
        """Test invalid base below 2."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="Base must be between 2 and 36"):
            parser.parse("num(1'1).")

    def test_invalid_base_too_high(self):
        """Test invalid base above 36."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="Base must be between 2 and 36"):
            parser.parse("num(37'1).")

    def test_invalid_digit_for_base(self):
        """Test digit value >= base."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="Invalid digit '3' for radix 2"):
            parser.parse("num(2'13).")

    def test_invalid_digit_letter_for_base(self):
        """Test letter digit >= base."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="Invalid digit 'g' for radix 16"):
            parser.parse("num(16'fg).")

    def test_empty_digits(self):
        """Test empty digits after base'."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="syntax_error"):
            parser.parse("num(16').")

    def test_invalid_base_not_integer(self):
        """Test non-integer base."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="syntax_error"):
            parser.parse("num(a'1).")

    def test_invalid_digit_character(self):
        """Test invalid digit character."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="syntax_error"):
            parser.parse("num(16'@).")


class TestScientificNotation:
    """Tests for scientific notation number parsing."""

    def test_basic_scientific_forms(self):
        parser = PrologParser()

        clauses = parser.parse("num(1e5).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == 1e5

        clauses = parser.parse("num(1.5e10).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == 1.5e10

        clauses = parser.parse("num(2.5E-3).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == pytest.approx(0.0025)

    def test_negative_exponents(self):
        parser = PrologParser()

        clauses = parser.parse("num(1e-10).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == pytest.approx(1e-10)

        clauses = parser.parse("num(1.23e-45).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == pytest.approx(1.23e-45)

    def test_positive_exponents(self):
        parser = PrologParser()

        clauses = parser.parse("num(1e+5).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == 1e5

        clauses = parser.parse("num(1.0E+10).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == 1.0e10

    def test_invalid_scientific_notation(self):
        parser = PrologParser()

        with pytest.raises(PrologThrow):
            parser.parse("num(1e).")
        with pytest.raises(PrologThrow):
            parser.parse("num(1.5e).")
        with pytest.raises(PrologThrow):
            parser.parse("num(1.5e+).")

        # Ensure non-numeric tokens are not misinterpreted as scientific notation
        clauses = parser.parse("num(e5).")
        assert isinstance(clauses[0].head.args[0], Atom)


class TestStandardPrefixes:
    """Tests for standard number prefixes (hex, octal, binary)."""

    @pytest.mark.parametrize("literal, expected", [
        ("0xFF", 255),
        ("0x10", 16),
        ("0xABC", 0xABC),
        ("-0x1A", -0x1A),
        ("0xAbC", 0xABC),  # Mixed case
        ("0xabcdef", 0xabcdef),  # Lowercase
        ("0xABCDEF", 0xABCDEF),  # Uppercase
    ])
    def test_hexadecimal_numbers(self, literal, expected):
        parser = PrologParser()
        clauses = parser.parse(f"num({literal}).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == expected

    def test_octal_numbers(self):
        parser = PrologParser()

        clauses = parser.parse("num(0o77).")
        assert clauses[0].head.args[0].value == 0o77

        clauses = parser.parse("num(0o123).")
        assert clauses[0].head.args[0].value == 0o123

        clauses = parser.parse("num(0o7).")
        assert clauses[0].head.args[0].value == 0o7

        clauses = parser.parse("num(-0o10).")
        assert clauses[0].head.args[0].value == -0o10

    def test_binary_numbers(self):
        parser = PrologParser()

        clauses = parser.parse("num(0b1010).")
        assert clauses[0].head.args[0].value == 0b1010

        clauses = parser.parse("num(0b11111111).")
        assert clauses[0].head.args[0].value == 0b11111111

        clauses = parser.parse("num(0b1).")
        assert clauses[0].head.args[0].value == 1

        clauses = parser.parse("num(-0b101).")
        assert clauses[0].head.args[0].value == -0b101

    def test_case_insensitive_prefixes(self):
        parser = PrologParser()

        clauses = parser.parse("num(0XFF).")
        assert clauses[0].head.args[0].value == 255

        clauses = parser.parse("num(0O77).")
        assert clauses[0].head.args[0].value == 0o77

        clauses = parser.parse("num(0B1010).")
        assert clauses[0].head.args[0].value == 0b1010

    def test_invalid_standard_prefixes(self):
        parser = PrologParser()

        with pytest.raises(PrologThrow):
            parser.parse("num(0xZZ).")
        with pytest.raises(PrologThrow):
            parser.parse("num(0o99).")
        with pytest.raises(PrologThrow):
            parser.parse("num(0b22).")
        with pytest.raises(PrologThrow):
            parser.parse("num(0xG).")


class TestFloatEdgeCases:
    """Tests for float parsing edge cases."""

    def test_extreme_float_ranges(self):
        parser = PrologParser()

        clauses = parser.parse("num(1.79e308).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == pytest.approx(1.79e308)

        clauses = parser.parse("num(5e-324).")
        assert isinstance(clauses[0].head.args[0], Number)
        assert clauses[0].head.args[0].value == pytest.approx(5e-324)

    def test_leading_dot_notation(self):
        parser = PrologParser()

        for literal, expected in [(".5", 0.5), (".123", 0.123), (".999", 0.999)]:
            clauses = parser.parse(f"num({literal}).")
            assert isinstance(clauses[0].head.args[0], Number)
            assert clauses[0].head.args[0].value == pytest.approx(expected)

    def test_trailing_zeros(self):
        parser = PrologParser()

        for literal, expected in [("1.0", 1.0), ("2.00", 2.0), ("3.140000", 3.14)]:
            clauses = parser.parse(f"num({literal}).")
            assert isinstance(clauses[0].head.args[0], Number)
            assert clauses[0].head.args[0].value == pytest.approx(expected)

    def test_invalid_float_formats(self):
        parser = PrologParser()

        with pytest.raises(PrologThrow):
            parser.parse("num(1.2.3).")
        # Note: num(.). is valid - '.' is parsed as an atom argument


class TestNumericContexts:
    """Tests that numbers work correctly in various Prolog contexts."""

    def test_numbers_in_arithmetic_expression(self):
        prolog = PrologInterpreter()
        result = prolog.query_once("X is 5 + 3.14.")
        assert result is not None
        assert result["X"] == pytest.approx(8.14)

    def test_numbers_in_lists(self):
        parser = PrologParser()
        clauses = parser.parse("nums([1, 2.5, 0xFF, 1e5]).")
        lst = clauses[0].head.args[0]
        assert isinstance(lst, List)
        values = [element.value for element in lst.elements]
        assert values == [1, 2.5, 255, 100000.0]

    def test_numbers_in_compound_terms(self):
        parser = PrologParser()
        clauses = parser.parse("foo(42, 3.14, 0x10).")
        args = clauses[0].head.args
        assert [arg.value for arg in args] == [42, pytest.approx(3.14), 16]

    def test_numbers_in_comparisons(self):
        prolog = PrologInterpreter()
        assert prolog.has_solution("5 < 10.")
        assert prolog.has_solution("3.14 =:= 3.14.")

    def test_numbers_with_variables(self):
        parser = PrologParser()
        clauses = parser.parse("calc(X, 5).")
        assert isinstance(clauses[0].head.args[0], Variable)
        assert isinstance(clauses[0].head.args[1], Number)
        assert clauses[0].head.args[1].value == 5

        prolog = PrologInterpreter()
        bindings = prolog.query_once("[H|T] = [1,2,3].")
        assert bindings is not None
        assert bindings["H"] == 1
        assert bindings["T"] == [2, 3]

class TestCharacterCodeHexEscapes:
    """Tests for ISO/SWI-style 0'\\xHH character code escapes."""

    def test_hex_escape_two_digits(self):
        parser = PrologParser()
        clauses = parser.parse("code(0'\\x41).")
        number = clauses[0].head.args[0]
        assert isinstance(number, Number)
        assert number.value == 65

    def test_hex_escape_longer_sequence(self):
        parser = PrologParser()
        clauses = parser.parse("code(0'\\x0041).")
        number = clauses[0].head.args[0]
        assert isinstance(number, Number)
        assert number.value == 65

    def test_hex_escape_optional_trailing_backslash(self):
        parser = PrologParser()
        clauses = parser.parse("code(0'\\x41\\).")
        number = clauses[0].head.args[0]
        assert isinstance(number, Number)
        assert number.value == 65

    def test_hex_escape_lower_and_uppercase_digits(self):
        prolog = PrologInterpreter()
        result_lower = prolog.query_once("X is 0'\\x6a.")
        assert result_lower is not None
        assert result_lower['X'] == ord('j')

        result_upper = prolog.query_once("X is 0'\\x4A.")
        assert result_upper is not None
        assert result_upper['X'] == ord('J')

    def test_hex_escape_respects_token_boundaries(self):
        parser = PrologParser()
        clauses = parser.parse("pair(0'\\x41, 0'B).")
        left, right = clauses[0].head.args
        assert isinstance(left, Number)
        assert left.value == 65
        assert isinstance(right, Number)
        assert right.value == ord('B')

    def test_hex_escape_rejects_short_sequence(self):
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="incomplete_reduction"):
            parser.parse("code(0'\\x4).")

    def test_hex_escape_rejects_non_hex_digit(self):
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="syntax_error"):
            parser.parse("code(0'\\x4G).")


class TestISOConformityBlockComments:
    """Tests for ISO conformity with block comments as whitespace."""

    def test_block_comment_inside_arg(self):
        """Test block comment between argument tokens parses correctly.
        
        Block comments act as whitespace, so writeq(a/* */). becomes writeq(a ).
        which is valid Prolog.
        """
        parser = PrologParser()
        clauses = parser.parse("writeq(a/* */).")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "writeq"
        assert clauses[0].head.args[0].name == "a"

    def test_block_comment_between_args(self):
        """Test block comment between arguments parses correctly.
        
        The comment acts as whitespace between tokens.
        """
        parser = PrologParser()
        clauses = parser.parse("foo(a/* . */,b).")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "foo"
        assert clauses[0].head.args[0].name == "a"
        assert clauses[0].head.args[1].name == "b"

    def test_floating_literal_with_block_comment(self):
        """Test floating literal with block comment."""
        parser = PrologParser()
        clauses = parser.parse("X/**/is/**/3.14.")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "is"
        assert clauses[0].head.args[1] == Number(3.14)

    def test_unary_minus_with_block_comment(self):
        """Test unary minus with block comment."""
        parser = PrologParser()
        clauses = parser.parse("X/**/is/**/-42.")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "is"
        assert clauses[0].head.args[1] == Number(-42)

    def test_list_with_block_comment(self):
        """Test list starting with block comment."""
        parser = PrologParser()
        clauses = parser.parse("/**/ [1,2,3].")
        assert len(clauses) == 1
        assert isinstance(clauses[0].head, List)
        assert len(clauses[0].head.elements) == 3

    def test_toplevel_with_block_comment(self):
        """Test toplevel clause starting with block comment."""
        parser = PrologParser()
        clauses = parser.parse("/**/ fact.")
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"


class TestISOConformityGraphicOperators:
    """Tests for ISO conformity with graphic operators containing /*, */.
    
    ISO tests #48-49 require that graphic tokens like //* are not split
    and treated as block comment starts.
    """

    @pytest.mark.larl_exclude
    def test_double_slash_star_operator(self):
        """ISO test #48: writeq(//*). should parse without 'Unterminated block comment'.
        
        The key requirement is that /* after / does NOT start a comment because
        the / is a graphic character. The actual parsing of //* may vary by
        implementation (could be atom //* or expression /(/, *)).
        """
        parser = PrologParser()
        clauses = parser.parse("writeq(//*).") 
        assert len(clauses) == 1
        assert clauses[0].head.functor == "writeq"
        # The argument may be parsed as atom or as binary / applied to / and *

    @pytest.mark.larl_exclude
    def test_nested_graphic_operator(self):
        """ISO test #49: writeq(//*./*/).  should parse as two graphic tokens.
        
        Both //* and /*/ are graphic operator tokens.
        """
        parser = PrologParser()
        clauses = parser.parse("writeq(//*./*/).")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "writeq"

    def test_single_slash_comment_start(self):
        """A single / followed by /* should recognize the comment.
        
        Unlike //* where // is already a graphic prefix, a lone / followed by 
        a space and then /* should recognize the comment.
        """
        parser = PrologParser()
        # foo(/ /* comment */) - the / is an operator, /* starts comment
        clauses = parser.parse("foo(/ /* comment */).")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "foo"


class TestComplexExamples:
    """Tests for parsing complex real-world examples."""

    @pytest.mark.larl_exclude
    def test_parse_cans_example(self):
        """Test parsing the cans.pl example."""
        parser = PrologParser()
        code = """
            cans_needed(TotalCans, PeopleServed, PercentFewer, CansForFewer) :-
                Ratio is TotalCans / PeopleServed,
                FewerPeople is PeopleServed * (1 - PercentFewer / 100),
                CansForFewer is Ratio * FewerPeople.

            solve(Cans) :- cans_needed(600, 40, 30, Cans).

            mi(true, Expl, Expl) :- !.
        """
        clauses = parser.parse(code)
        assert len(clauses) == 3
        assert clauses[0].head.functor == "cans_needed"
        assert clauses[1].head.functor == "solve"
        assert clauses[2].head.functor == "mi"
        # Third clause has cut in body
        assert isinstance(clauses[2].body[0], Cut)

    def test_parse_meta_interpreter(self):
        """Test parsing meta-interpreter with if-then-else."""
        parser = PrologParser()
        code = """
            mi(Goal, ExplIn, ExplOut) :-
                (   clause(Goal, Body)
                ->  mi(Body, ExplIn, ExplOut)
                ;   call(Goal),
                    ExplOut = ExplIn
                ).
        """
        clauses = parser.parse(code)
        assert len(clauses) == 1
        clause = clauses[0]
        assert clause.head.functor == "mi"
        # Body should contain if-then-else structure
        assert len(clause.body) == 1
        assert isinstance(clause.body[0], Compound)


class TestTokenizePrologStatements:
    """Tests for tokenize_prolog_statements function."""

    def test_tokenize_simple_clauses(self):
        """Test tokenizing simple clauses."""
        code = "fact.fact2."
        chunks = tokenize_prolog_statements(code)
        assert chunks == ["fact.", "fact2."]

    def test_tokenize_with_decimals(self):
        """Test tokenizing clauses containing decimal numbers."""
        code = "p(1.0). q(2.3). r(.5)."
        chunks = tokenize_prolog_statements(code)
        assert chunks == ["p(1.0).", " q(2.3).", " r(.5)."]

    def test_tokenize_with_quotes(self):
        """Test tokenizing with quoted strings."""
        code = "write('hello. world'). fact."
        chunks = tokenize_prolog_statements(code)
        assert chunks == ["write('hello. world').", " fact."]

    def test_tokenize_with_quotes(self):
        """Test tokenizing with quoted strings."""
        code = "write('hello. world'). fact."
        chunks = tokenize_prolog_statements(code)
        assert chunks == ["write('hello. world').", " fact."]

    def test_tokenize_mixed_decimals_and_clauses(self):
        """Test tokenizing code with decimals in clauses and multiple clauses."""
        code = "p(1.). q(2.3). r(a)."
        chunks = tokenize_prolog_statements(code)
        assert chunks == ["p(1.).", " q(2.3).", " r(a)."]

    def test_tokenize_decimal_boundary_cases(self):
        """Test decimal points at clause boundaries."""
        # Test trailing decimal
        code = "p(1.)."
        chunks = tokenize_prolog_statements(code)
        assert chunks == ["p(1.)."]

        # Test decimal with following clause
        code = "p(1.). q(2)."
        chunks = tokenize_prolog_statements(code)
        assert chunks == ["p(1.).", " q(2)."]

        # Test decimal starting with dot
        code = "p(.5)."
        chunks = tokenize_prolog_statements(code)
        assert chunks == ["p(.5)."]


class TestDotInParentheses:
    """Test that dots inside parentheses are not clause terminators."""

    def test_dot_as_atom_argument(self):
        """Dot used as an atom argument inside compound term."""
        code = 'phrase(upto_what(Bs0, .), Cs0, Ds).'
        statements = list(tokenize_prolog_statements(code))
        assert statements == ['phrase(upto_what(Bs0, .), Cs0, Ds).']

    def test_dot_in_list(self):
        """Dot used as element in a list."""
        code = 'test([., a, b]).'
        statements = list(tokenize_prolog_statements(code))
        assert statements == ['test([., a, b]).']

    def test_multiple_dots_in_term(self):
        """Multiple dots in complex term."""
        code = 'foo(bar(., X), baz(Y, .)).'
        statements = list(tokenize_prolog_statements(code))
        assert statements == ['foo(bar(., X), baz(Y, .)).']

    def test_dot_at_end_is_terminator(self):
        """Dot at end of clause is still a terminator."""
        code = 'foo(a, b). bar(c, d).'
        statements = list(tokenize_prolog_statements(code))
        assert statements == ['foo(a, b).', ' bar(c, d).']


class TestDotAndRangeOperator:
    """Test parsing of single dot as atom and .. as range operator.
    
    These tests address the issue where:
    1. A single '.' used as an atom argument (e.g., in DCG rules) was incorrectly rejected
    2. The '..' range operator must be correctly parsed in expressions like '1..9'
    """

    def test_dot_as_atom_parses_correctly(self):
        """Single dot should be valid as an atom in functor arguments."""
        parser = PrologParser()
        clauses = parser.parse('test :- phrase(upto_what(Bs0, .), Cs0, Ds).')
        assert len(clauses) == 1
        clause = clauses[0]
        assert isinstance(clause.body[0], Compound)
        assert clause.body[0].functor == 'phrase'

    def test_quoted_dot_as_atom(self):
        """Quoted dot should work as an atom."""
        parser = PrologParser()
        clauses = parser.parse("test :- foo('.').")
        assert len(clauses) == 1
        clause = clauses[0]
        assert isinstance(clause.body[0].args[0], Atom)
        assert clause.body[0].args[0].name == '.'

    def test_dot_in_list(self):
        """Dot should be valid as a list element."""
        parser = PrologParser()
        clauses = parser.parse('test :- X = [., a, .].')
        assert len(clauses) == 1
        clause = clauses[0]
        # The list should contain dots as atoms
        assert isinstance(clause.body[0], Compound)
        assert clause.body[0].functor == '='
        list_term = clause.body[0].args[1]
        assert isinstance(list_term, List)
        assert list_term.elements == (Atom('.'), Atom('a'), Atom('.'))

    def test_range_operator_basic(self):
        """Range operator 1..9 should parse correctly."""
        parser = PrologParser()
        clauses = parser.parse('test :- X in 1..9.')
        assert len(clauses) == 1
        clause = clauses[0]
        # The body should be in(X, ..(1, 9))
        assert isinstance(clause.body[0], Compound)
        assert clause.body[0].functor == 'in'
        range_term = clause.body[0].args[1]
        assert isinstance(range_term, Compound)
        assert range_term.functor == '..'
        assert range_term.args[0] == Number(1)
        assert range_term.args[1] == Number(9)

    def test_range_operator_with_variables(self):
        """Range operator with variables X..Y."""
        parser = PrologParser()
        clauses = parser.parse('test :- X in A..B.')
        assert len(clauses) == 1
        clause = clauses[0]
        range_term = clause.body[0].args[1]
        assert isinstance(range_term, Compound)
        assert range_term.functor == '..'
        assert isinstance(range_term.args[0], Variable)
        assert isinstance(range_term.args[1], Variable)

    def test_range_operator_with_spaces(self):
        """Range operator with spaces around it."""
        parser = PrologParser()
        clauses = parser.parse('test :- X in 1 .. 9.')
        assert len(clauses) == 1
        clause = clauses[0]
        range_term = clause.body[0].args[1]
        assert isinstance(range_term, Compound)
        assert range_term.functor == '..'
        assert range_term.args[0] == Number(1)
        assert range_term.args[1] == Number(9)

    def test_range_operator_with_zero(self):
        """Range operator 0..100."""
        parser = PrologParser()
        clauses = parser.parse('test :- X in 0..100.')
        assert len(clauses) == 1
        clause = clauses[0]
        range_term = clause.body[0].args[1]
        assert isinstance(range_term, Compound)
        assert range_term.functor == '..'
        assert range_term.args[0] == Number(0)
        assert range_term.args[1] == Number(100)

    def test_range_operator_negative_numbers(self):
        """Range operator with negative numbers -5..5."""
        parser = PrologParser()
        clauses = parser.parse('test :- X in -5..5.')
        assert len(clauses) == 1
        clause = clauses[0]
        range_term = clause.body[0].args[1]
        assert isinstance(range_term, Compound)
        assert range_term.functor == '..'
        assert range_term.args[0] == Number(-5)
        assert range_term.args[1] == Number(5)

    def test_range_operator_in_parentheses(self):
        """Range operator in parentheses (1..9)."""
        parser = PrologParser()
        clauses = parser.parse('test :- X = (1..9).')
        assert len(clauses) == 1
        clause = clauses[0]
        # X = (1..9) -> =(X, ..(1, 9))
        assert isinstance(clause.body[0], Compound)
        assert clause.body[0].functor == '='
        range_term = clause.body[0].args[1]
        assert isinstance(range_term, Compound)
        assert range_term.functor == '..'

    def test_range_operator_in_list(self):
        """Range operator inside a list [1..5, 6..10]."""
        parser = PrologParser()
        clauses = parser.parse('test :- X = [1..5, 6..10].')
        assert len(clauses) == 1
        clause = clauses[0]
        # The list should have two range terms
        list_term = clause.body[0].args[1]
        assert isinstance(list_term, List)
        assert len(list_term.elements) == 2
        assert list_term.elements[0] == Compound('..', (Number(1), Number(5)))
        assert list_term.elements[1] == Compound('..', (Number(6), Number(10)))

    def test_range_operator_as_predicate_argument(self):
        """Range operator as argument foo(1..3)."""
        parser = PrologParser()
        clauses = parser.parse('test :- foo(1..3).')
        assert len(clauses) == 1
        clause = clauses[0]
        foo_call = clause.body[0]
        assert isinstance(foo_call, Compound)
        assert foo_call.functor == 'foo'
        range_term = foo_call.args[0]
        assert isinstance(range_term, Compound)
        assert range_term.functor == '..'

    def test_range_with_trailing_float(self):
        """Regression test: 1..2.3 should be parsed correctly without splitting clauses.
        
        The regex pattern for detecting clause terminators must not incorrectly
        treat 1..2. (from 1..2.3) as a clause terminator when followed by a digit.
        This test ensures the clause is not split into two tokens.
        """
        from vibeprolog.parser import tokenize_prolog_statements
        
        # Test tokenization first
        code = 'test :- X = 1..2.3.'
        statements = list(tokenize_prolog_statements(code))
        assert len(statements) == 1, f"Expected 1 statement, got {len(statements)}: {statements}"
        assert statements[0] == code
        
        # Now test parsing
        parser = PrologParser()
        clauses = parser.parse('test :- X = 1..2.3.')
        assert len(clauses) == 1
        clause = clauses[0]
        # Head should be the atom 'test'
        assert isinstance(clause.head, Atom)
        assert clause.head.name == 'test'
        assert len(clause.body) == 1
        
        # The body should be X = 1..2.3 where 1..2.3 is parsed as part of the expression
        goal = clause.body[0]
        assert isinstance(goal, Compound)
        assert goal.functor == '='
        # The RHS should be a range expression with a float: ..(1, 2.3)
        rhs = goal.args[1]
        assert isinstance(rhs, Compound)
        assert rhs.functor == '..'
        assert rhs.args[0] == Number(1)
        assert rhs.args[1] == Number(2.3)

    @pytest.mark.larl_exclude
    def test_ellipsis_pattern(self):
        """Ellipsis ... pattern in DCG rules."""
        parser = PrologParser()
        clauses = parser.parse('test :- phrase((...,[Last]), Ls).')
        assert len(clauses) == 1
        clause = clauses[0]
        assert isinstance(clause.body[0], Compound)
        assert clause.body[0].functor == 'phrase'

    def test_float_parsing_not_affected(self):
        """Float parsing should still work correctly."""
        parser = PrologParser()
        clauses = parser.parse('test :- X is 3.14.')
        assert len(clauses) == 1
        clause = clauses[0]
        is_expr = clause.body[0]
        assert isinstance(is_expr, Compound)
        assert is_expr.functor == 'is'
        assert is_expr.args[1] == Number(3.14)

    def test_integer_with_terminator(self):
        """Integer followed by clause terminator."""
        parser = PrologParser()
        clauses = parser.parse('test :- X = 1.')
        assert len(clauses) == 1
        clause = clauses[0]
        eq_expr = clause.body[0]
        assert eq_expr.args[1] == Number(1)

    def test_full_clause_with_range_and_terminator(self):
        """Complete clause with range and proper termination."""
        parser = PrologParser()
        clauses = parser.parse('sudoku :- Vars in 1..9, label(Vars).')
        assert len(clauses) == 1
        clause = clauses[0]
        assert len(clause.body) == 2
        # First goal: Vars in 1..9
        in_goal = clause.body[0]
        assert in_goal.functor == 'in'
        # Second goal: label(Vars)
        label_goal = clause.body[1]
        assert label_goal.functor == 'label'

    def test_clpz_style_constraint(self):
        """CLP(Z) style constraint with range operator."""
        parser = PrologParser()
        clauses = parser.parse('test :- [X,Y] ins 0..9.')
        assert len(clauses) == 1
        clause = clauses[0]
        ins_goal = clause.body[0]
        assert ins_goal.functor == 'ins'
        range_term = ins_goal.args[1]
        assert range_term.functor == '..'

    def test_tokenizer_range_operator(self):
        """Tokenizer correctly handles range operator in clauses."""
        code = 'test :- X in 1..9. test2 :- Y in 0..10.'
        statements = list(tokenize_prolog_statements(code))
        assert len(statements) == 2
        assert '1..9' in statements[0]
        assert '0..10' in statements[1]

    def test_tokenizer_ellipsis(self):
        """Tokenizer correctly handles ellipsis in clauses."""
        code = 'test :- phrase((...,X), L). test2.'
        statements = list(tokenize_prolog_statements(code))
        assert len(statements) == 2
        assert '...' in statements[0]
