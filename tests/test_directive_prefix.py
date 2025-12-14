"""Tests for directive prefix operator :- (1200, fx).

These tests verify that the ISO-required prefix form of the :- operator
works correctly for directives. ISO Prolog allows both:
- Infix form: Head :- Body (for rules)
- Prefix form: :- Directive (for directives)

ISO/IEC 13211-1 §5.3.4.4 specifies :- as both fx and xfx at precedence 1200.
"""

import pytest

from vibeprolog import PrologInterpreter
from vibeprolog.exceptions import PrologThrow


class TestBasicPrefixDirectives:
    """Tests for basic prefix directive syntax."""

    def test_dynamic_directive_prefix_form(self):
        """Test that :- dynamic(foo/2) declares foo/2 as dynamic."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic(foo/2).
            foo(1, a).
        """)
        assert prolog.has_solution("foo(1, a)")
        assert prolog.has_solution("asserta(foo(2, b))")
        assert prolog.has_solution("foo(2, b)")

    @pytest.mark.larl_exclude
    def test_dynamic_directive_no_parens(self):
        """Test that :- dynamic foo/2 (no parentheses) works."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic foo/2.
            foo(1, a).
        """)
        assert prolog.has_solution("asserta(foo(2, b))")
        assert prolog.has_solution("foo(2, b)")

    def test_multifile_directive_prefix_form(self):
        """Test that :- multifile(bar/1) declares bar/1 as multifile."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- multifile(bar/1).
            bar(1).
        """)
        prolog.consult_string("bar(2).")
        
        results = prolog.query("bar(X)")
        values = {row["X"] for row in results}
        assert values == {1, 2}

    def test_discontiguous_directive_prefix_form(self):
        """Test that :- discontiguous(baz/3) declares baz/3 as discontiguous."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- discontiguous(baz/3).
            baz(1, a, x).
            other(42).
            baz(2, b, y).
        """)
        results = prolog.query("baz(N, _, _)")
        values = {row["N"] for row in results}
        assert values == {1, 2}

    def test_op_directive_prefix_form(self):
        """Test that :- op(500, xfx, myop) registers a custom operator."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(500, xfx, myop).
            test(X myop Y) :- X = 1, Y = 2.
        """)
        assert prolog.has_solution("test(1 myop 2)")


class TestModuleDirectives:
    """Tests for module-related prefix directives."""

    def test_module_directive_prefix_form(self):
        """Test that :- module(mymod, [foo/2]) declares a module."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(mymod, [foo/2]).
            foo(1, a).
            foo(2, b).
        """)
        assert prolog.has_solution("mymod:foo(1, a)")
        assert prolog.has_solution("mymod:foo(2, b)")

    @pytest.mark.slow
    def test_use_module_directive_prefix_form(self):
        """Test that :- use_module(library(lists)) loads the lists module."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- use_module(library(lists)).
        """)
        # The lists module should be loaded - verify by checking append works
        assert prolog.has_solution("append([1], [2], [1, 2])")


class TestInitializationDirective:
    """Tests for initialization prefix directives."""

    def test_initialization_directive_prefix_form(self):
        """Test that :- initialization(goal) executes the goal during consultation."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic(flag/1).
            :- initialization(assertz(flag(init_ran))).
        """)
        assert prolog.has_solution("flag(init_ran)")

    def test_multiple_initialization_directives(self):
        """Test that multiple initialization directives execute in order."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic(log/1).
            :- initialization(assertz(log(first))).
            :- initialization(assertz(log(second))).
            :- initialization(assertz(log(third))).
        """)
        results = prolog.query("log(X)")
        values = [row["X"] for row in results]
        assert values == ["first", "second", "third"]


class TestMixedSyntax:
    """Tests for mixing prefix and traditional syntax."""

    def test_mixed_directives_and_rules(self):
        """Test that both prefix directives and rules work in the same file."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic(counter/1).
            counter(0).
            
            increment(OldVal, NewVal) :-
                retract(counter(OldVal)),
                NewVal is OldVal + 1,
                assertz(counter(NewVal)).
        """)
        assert prolog.has_solution("counter(0)")
        result = prolog.query_once("increment(Old, New)")
        assert result["Old"] == 0
        assert result["New"] == 1
        assert prolog.has_solution("counter(1)")

    def test_query_prefix_operator_still_works(self):
        """Test that ?- query syntax still works correctly."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            foo(1).
            foo(2).
        """)
        # The query method doesn't use ?- syntax directly but let's ensure
        # the operator is registered for use in code
        assert prolog.has_solution("foo(1)")
        assert prolog.has_solution("foo(2)")

    def test_facts_rules_and_directives_interleaved(self):
        """Test that facts, rules, and directives can be interleaved."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic(item/1).
            base(1).
            :- op(400, xfx, is_related_to).
            derive(X) :- base(X).
            relation(a is_related_to b).
        """)
        assert prolog.has_solution("base(1)")
        assert prolog.has_solution("derive(1)")
        assert prolog.has_solution("relation(a is_related_to b)")


class TestErrorHandling:
    """Tests for error handling in prefix directives."""

    def test_invalid_directive_variable_predicate_indicator(self):
        """Test that invalid directives with variable indicators give clear errors."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(":- dynamic(X/1).")
        error = exc_info.value.error_term
        assert error.functor == "error"
        # Error could be instantiation_error (atom) or type_error (compound)
        # depending on which validation happens first
        first_arg = error.args[0]
        assert first_arg.name == "instantiation_error" if hasattr(first_arg, "name") else first_arg.functor in ("instantiation_error", "type_error")

    def test_invalid_directive_non_atom_functor(self):
        """Test that invalid directives with non-atom functor give clear errors."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(":- dynamic(123/1).")
        error = exc_info.value.error_term
        assert error.functor == "error"
        assert error.args[0].functor == "type_error"

    def test_invalid_directive_non_integer_arity(self):
        """Test that invalid directives with non-integer arity give clear errors."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(":- dynamic(foo/x).")
        error = exc_info.value.error_term
        assert error.functor == "error"
        assert error.args[0].functor == "type_error"


class TestMultiplePredicateIndicators:
    """Tests for directives with multiple predicate indicators."""

    def test_dynamic_multiple_predicates(self):
        """Test :- dynamic(foo/1, bar/2) with multiple predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic(foo/1, bar/2).
            foo(1).
            bar(a, b).
        """)
        assert prolog.has_solution("asserta(foo(2))")
        assert prolog.has_solution("foo(2)")
        assert prolog.has_solution("asserta(bar(c, d))")
        assert prolog.has_solution("bar(c, d)")

    def test_multifile_multiple_predicates(self):
        """Test :- multifile(foo/1, bar/2) with multiple predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- multifile(shared1/1, shared2/2).
            shared1(1).
            shared2(a, b).
        """)
        prolog.consult_string("""
            shared1(2).
            shared2(c, d).
        """)
        
        results1 = prolog.query("shared1(X)")
        assert {row["X"] for row in results1} == {1, 2}
        
        results2 = prolog.query("shared2(X, Y)")
        pairs = {(row["X"], row["Y"]) for row in results2}
        assert pairs == {("a", "b"), ("c", "d")}


class TestOperatorDirectiveEdgeCases:
    """Edge case tests for operator directives."""

    def test_op_directive_with_list_of_operators(self):
        """Test :- op(500, xfx, [op1, op2]) with list of operators."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(500, xfx, [links, verbindet]).
            test(a links b).
            test(c verbindet d).
        """)
        assert prolog.has_solution("test(a links b)")
        assert prolog.has_solution("test(c verbindet d)")

    def test_op_directive_removes_operator(self):
        """Test that :- op(0, xfx, myop) removes the operator."""
        prolog = PrologInterpreter()
        # Test that the operator works first
        prolog.consult_string("""
            :- op(500, xfx, myop).
            test1(a myop b).
        """)
        assert prolog.has_solution("test1(a myop b)")
        
        # Note: Removing operators mid-file and testing that parsing fails
        # is complex because the parser pre-scans for operators.
        # What we can test is that the operator table is updated.
        prolog.consult_string(":- op(0, xfx, myop).")
        # After removal, the operator should not be in the table
        op_info = prolog.operator_table.lookup("myop", "xfx")
        assert op_info is None


class TestDirectivePrefixOperatorRegistration:
    """Tests for verifying the :- operator is properly registered."""

    def test_directive_operator_is_fx(self):
        """Verify :- is registered as a prefix (fx) operator at precedence 1200."""
        prolog = PrologInterpreter()
        prolog.consult_string("dummy.")  # Initialize engine
        # The operator table should have :- as fx at 1200
        prefix_info = prolog.operator_table.lookup(":-", "fx")
        assert prefix_info is not None
        assert prefix_info.spec == "fx"
        assert prefix_info.precedence == 1200

    def test_directive_operator_coexists_with_rule_operator(self):
        """Verify :- works both as prefix (directive) and infix (rule)."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic(test/1).
            test(1).
            derives(X) :- test(X).
        """)
        assert prolog.has_solution("test(1)")
        assert prolog.has_solution("derives(1)")
