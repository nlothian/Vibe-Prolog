"""Tests for the Prolog parser."""

import pytest
from vibeprolog.parser import (
    PrologParser, Clause, Compound, Atom, Variable, Number, List, Cut
)
from vibeprolog.exceptions import PrologThrow


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
        # The body should be a conjunction (,)
        assert isinstance(clause.body[0], Compound)
        assert clause.body[0].functor == ","

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
        assert len(clause.body) == 1
        conj = clause.body[0]
        assert isinstance(conj, Compound)
        assert conj.functor == ","

    def test_parse_parenthesized_conjunction(self):
        """Test parsing parenthesized conjunction."""
        parser = PrologParser()
        clauses = parser.parse("test(A, B) :- (A, B).")
        clause = clauses[0]
        assert len(clause.body) == 1
        body = clause.body[0]
        assert isinstance(body, Compound)
        assert body.functor == ","

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


class TestBaseDigits:
    """Tests for parsing base'digits syntax."""

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

    def test_parse_negative_base_digits(self):
        """Test parsing negative base'digits."""
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
        with pytest.raises(PrologThrow, match="Invalid digit '3' for base 2"):
            parser.parse("num(2'13).")

    def test_invalid_digit_letter_for_base(self):
        """Test letter digit >= base."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="Invalid digit 'g' for base 16"):
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


class TestCharacterCodes:
    r"""Tests for parsing character code literals like 0'X and 0'\xHH."""

    def test_parse_simple_char_code(self):
        """Test parsing simple character codes like 0'a."""
        parser = PrologParser()
        clauses = parser.parse("test(0'a).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == ord('a')

    def test_parse_backslash_escape(self):
        """Test parsing backslash escape 0'\\."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\\\).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == ord('\\')

    def test_parse_quote_escape_doubled(self):
        """Test parsing doubled quote escape 0'''."""
        parser = PrologParser()
        clauses = parser.parse("test(0''').")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == ord("'")

    def test_parse_quote_escape_backslash(self):
        """Test parsing backslash quote escape 0'\\'."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\').")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == ord("'")

    def test_parse_hex_escape_two_digits(self):
        r"""Test parsing hex escape 0'\x41 (two digits)."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x41).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 65  # 'A'

    def test_parse_hex_escape_four_digits(self):
        r"""Test parsing hex escape 0'\x0041 (four digits)."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x0041).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 65  # 'A'

    def test_parse_hex_escape_uppercase(self):
        r"""Test parsing hex escape with uppercase digits 0'\xFF."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\xFF).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 255

    def test_parse_hex_escape_mixed_case(self):
        r"""Test parsing hex escape with mixed case digits 0'\xAbCd."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\xAbCd).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        # A=10, b=11, C=12, d=13: 10*4096 + 11*256 + 12*16 + 13 = 43981
        assert clause.head.args[0].value == 10*4096 + 11*256 + 12*16 + 13

    def test_parse_hex_escape_single_digit(self):
        r"""Test parsing hex escape with single digit 0'\x1."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x1).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 1

    def test_parse_hex_escape_zero(self):
        r"""Test parsing hex escape 0'\x00."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x00).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 0

    def test_parse_hex_escape_max_unicode(self):
        r"""Test parsing hex escape for a high Unicode code point."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x10FFFF).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 0x10FFFF

    def test_invalid_hex_escape_empty(self):
        r"""Test invalid empty hex escape 0'\x."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="empty hex sequence"):
            parser.parse("test(0'\\x).")

    def test_invalid_hex_escape_non_hex_digit(self):
        r"""Test invalid hex escape with non-hex digit 0'\xGG."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="invalid literal for int"):
            parser.parse("test(0'\\xGG).")

    def test_invalid_hex_escape_mixed_invalid(self):
        r"""Test invalid hex escape with mixed valid/invalid digits 0'\xAG."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="invalid literal for int"):
            parser.parse("test(0'\\xAG).")

    def test_parse_hex_escape_with_trailing_backslash(self):
        r"""Test parsing hex escape with trailing backslash 0'\x41\."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x41\\\\).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 65  # 'A'

    def test_parse_hex_escape_four_digits_with_backslash(self):
        r"""Test parsing hex escape 0'\x0041\ with trailing backslash."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x0041\\\\).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 65  # 'A'

    def test_parse_hex_escape_uppercase_with_backslash(self):
        r"""Test parsing hex escape with uppercase digits and trailing backslash 0'\xFF\."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\xFF\\\\).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 255

    def test_parse_hex_escape_mixed_case_with_backslash(self):
        r"""Test parsing hex escape with mixed case digits and trailing backslash 0'\xAbCd\."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\xAbCd\\\\).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        # A=10, b=11, C=12, d=13: 10*4096 + 11*256 + 12*16 + 13 = 43981
        assert clause.head.args[0].value == 10*4096 + 11*256 + 12*16 + 13

    def test_parse_hex_escape_single_digit_with_backslash(self):
        r"""Test parsing hex escape with single digit and trailing backslash 0'\x1\."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x1\\\\).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 1

    def test_parse_hex_escape_zero_with_backslash(self):
        r"""Test parsing hex escape 0'\x00\ with trailing backslash."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x00\\\\).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 0

    def test_parse_hex_escape_max_unicode_with_backslash(self):
        r"""Test parsing hex escape for a high Unicode code point with trailing backslash."""
        parser = PrologParser()
        clauses = parser.parse("test(0'\\x10FFFF\\\\).")
        clause = clauses[0]
        assert isinstance(clause.head.args[0], Number)
        assert clause.head.args[0].value == 0x10FFFF

    def test_invalid_hex_escape_empty_with_backslash(self):
        r"""Test invalid empty hex escape 0'\x\."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="empty hex sequence"):
            parser.parse("test(0'\\x\\\\).")

    def test_invalid_hex_escape_non_hex_digit_with_backslash(self):
        r"""Test invalid hex escape with non-hex digit and trailing backslash 0'\xGG\."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="invalid literal for int"):
            parser.parse("test(0'\\xGG\\\\).")

    def test_invalid_hex_escape_mixed_invalid_with_backslash(self):
        r"""Test invalid hex escape with mixed valid/invalid digits and trailing backslash 0'\xAG\."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="invalid literal for int"):
            parser.parse("test(0'\\xAG\\\\).")


class TestComplexExamples:
    """Tests for parsing complex real-world examples."""

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
