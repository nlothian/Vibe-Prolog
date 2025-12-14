"""Tests for operators used as functor names in compound terms.

According to ISO Prolog, when an operator symbol appears in a position where an 
atom is expected (such as the functor of a compound term), it should be 
interpreted as an atom. This is needed for Scryer-Prolog compatibility.
"""

import pytest

from vibeprolog import PrologInterpreter


class TestQuotedOperatorAsFunctor:
    """Test quoted operators as functor names (already supported)."""

    def test_semicolon_quoted_as_functor(self):
        """Parse ';'(A, B) as compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(';'(a, b)).")
        assert prolog.has_solution("test(';'(a, b))")

    def test_pipe_quoted_as_functor(self):
        """Parse '|'(A, B) as compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("test('|'(a, b)).")
        assert prolog.has_solution("test('|'(a, b))")

    def test_colon_quoted_as_functor(self):
        """Parse ':'(A, B) as compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(':'(a, b)).")
        assert prolog.has_solution("test(':'(a, b))")

    def test_quoted_colon_in_functor_check(self):
        """functor/3 with quoted colon."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("functor(a:b, ':', 2)")

    def test_comma_quoted_as_functor(self):
        """Parse ','(A, B) as compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(','(a, b)).")
        assert prolog.has_solution("test(','(a, b))")

    def test_arrow_quoted_as_functor(self):
        """Parse '->'(A, B) as compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("test('->'(a, b)).")
        assert prolog.has_solution("test('->'(a, b))")


class TestUnquotedOperatorAsFunctor:
    """Test unquoted operators as functor names in compound terms.
    
    When an operator symbol appears immediately followed by '(' it should be
    parsed as a functor, not as an operator.
    """

    def test_semicolon_unquoted_as_functor(self):
        """Parse ;(A, B) as compound term with functor ';'."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(;(a, b)).")
        assert prolog.has_solution("test(;(a, b))")
        # Should be equivalent to quoted form
        assert prolog.has_solution("test(';'(a, b))")

    def test_pipe_unquoted_as_functor(self):
        """Parse |(A, B) as compound term with functor '|'."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(|(a, b)).")
        assert prolog.has_solution("test(|(a, b))")
        assert prolog.has_solution("test('|'(a, b))")

    def test_colon_unquoted_as_functor(self):
        """Parse :(A, B) as compound term with functor ':'."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(:(a, b)).")
        assert prolog.has_solution("test(:(a, b))")
        assert prolog.has_solution("test(':'(a, b))")

    def test_comma_unquoted_as_functor(self):
        """Parse ,(A, B) as compound term with functor ','."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(,(a, b)).")
        assert prolog.has_solution("test(,(a, b))")
        assert prolog.has_solution("test(','(a, b))")

    def test_arrow_unquoted_as_functor(self):
        """Parse ->(A, B) as compound term with functor '->'."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(->(a, b)).")
        assert prolog.has_solution("test(->(a, b))")
        assert prolog.has_solution("test('->'(a, b))")

    def test_plus_unquoted_as_functor(self):
        """Parse +(A, B) as compound term with functor '+'."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(+(a, b)).")
        assert prolog.has_solution("test(+(a, b))")
        assert prolog.has_solution("test('+'(a, b))")

    def test_minus_unquoted_as_functor(self):
        """Parse -(A, B) as compound term with functor '-'."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(-(a, b)).")
        assert prolog.has_solution("test(-(a, b))")
        assert prolog.has_solution("test('-'(a, b))")

    def test_multiply_unquoted_as_functor(self):
        """Parse *(A, B) as compound term with functor '*'."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(*(a, b)).")
        assert prolog.has_solution("test(*(a, b))")
        assert prolog.has_solution("test('*'(a, b))")

    def test_slash_unquoted_as_functor(self):
        """Parse /(A, B) as compound term with functor '/'."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(/(a, b)).")
        assert prolog.has_solution("test(/(a, b))")
        assert prolog.has_solution("test('/'(a, b))")


class TestParenthesizedOperatorAtom:
    """Test parenthesized operators as atoms like (:), (;), etc."""

    def test_parenthesized_colon(self):
        """Parse (:) as atom ':'."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("functor(a:b, (:), 2)")

    def test_parenthesized_semicolon(self):
        """Parse (;) as atom ';'."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("X = (;), X == ';'")

    def test_parenthesized_pipe(self):
        """Parse (|) as atom '|'."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("X = (|), X == '|'")

    def test_parenthesized_comma(self):
        """Parse (,) as atom ','."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("X = (,), X == ','")

    def test_parenthesized_arrow(self):
        """Parse (->) as atom '->'."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("X = (->), X == '->'")

    def test_parenthesized_plus(self):
        """Parse (+) as atom '+'."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("X = (+), X == '+'")

    def test_parenthesized_minus(self):
        """Parse (-) as atom '-'."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("X = (-), X == '-'")

    def test_parenthesized_star(self):
        """Parse (*) as atom '*'."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("X = (*), X == '*'")


class TestMetaPredicateWithOperator:
    """Test meta_predicate directive with operator as functor."""

    @pytest.mark.larl_exclude
    def test_meta_predicate_with_quoted_semicolon(self):
        """meta_predicate directive with quoted operator."""
        prolog = PrologInterpreter()
        # Should at least parse (directive is ignored in vibe-prolog)
        prolog.consult_string(":- meta_predicate(';'(2, 2, ?, ?)).")

    @pytest.mark.larl_exclude
    def test_meta_predicate_with_unquoted_semicolon(self):
        """meta_predicate directive with unquoted operator as functor."""
        prolog = PrologInterpreter()
        # Should parse without error
        prolog.consult_string(":- meta_predicate(;(2, 2, ?, ?)).")


class TestNestedOperatorFunctors:
    """Test nested use of operator symbols as functors."""

    def test_nested_semicolons(self):
        """Nested semicolon functors."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(;(;(a, b), c)).")
        assert prolog.has_solution("test(;(;(a, b), c))")

    def test_mixed_operator_functors(self):
        """Mixed operator symbols as functors."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(;(|(a, b), ,(c, d))).")
        assert prolog.has_solution("test(;(|(a, b), ,(c, d))).")

    def test_operator_functor_with_variables(self):
        """Operator functor with variable arguments."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            test_match(;(X, Y)) :- X = a, Y = b.
        """)
        assert prolog.has_solution("test_match(;(a, b))")


class TestComparisonOperatorAsFunctor:
    """Test comparison operators used as functors."""

    def test_equal_as_functor(self):
        """Parse =(A, B) as compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(=(a, b)).")
        assert prolog.has_solution("test(=(a, b))")
        assert prolog.has_solution("test('='(a, b))")

    def test_less_than_as_functor(self):
        """Parse <(A, B) as compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(<(1, 2)).")
        assert prolog.has_solution("test(<(1, 2))")

    def test_greater_than_as_functor(self):
        """Parse >(A, B) as compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(>(1, 2)).")
        assert prolog.has_solution("test(>(1, 2))")

    def test_unify_with_occurs_check_as_functor(self):
        """Parse =@=(A, B) as compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(=@=(a, a)).")
        assert prolog.has_solution("test(=@=(a, a))")
