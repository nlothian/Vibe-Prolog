"""Tests for retractall/1 predicate."""

import pytest

from vibeprolog import PrologInterpreter
from vibeprolog.exceptions import PrologThrow


class TestRetractallBasic:
    """Basic functionality tests for retractall/1."""

    @pytest.mark.larl_exclude
    def test_retract_all_matching_facts(self):
        """Retract all clauses matching a pattern."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic fact/1.
            fact(a).
            fact(b).
            fact(c).
        """)
        assert prolog.has_solution("fact(a)")
        assert prolog.has_solution("fact(b)")
        assert prolog.has_solution("fact(c)")

        assert prolog.has_solution("retractall(fact(_))")

        assert not prolog.has_solution("fact(a)")
        assert not prolog.has_solution("fact(b)")
        assert not prolog.has_solution("fact(c)")

    @pytest.mark.larl_exclude
    def test_retract_with_specific_pattern(self):
        """Retract only clauses matching a specific pattern."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic item/2.
            item(apple, fruit).
            item(banana, fruit).
            item(carrot, vegetable).
            item(potato, vegetable).
        """)

        assert prolog.has_solution("retractall(item(_, fruit))")

        assert not prolog.has_solution("item(apple, fruit)")
        assert not prolog.has_solution("item(banana, fruit)")
        assert prolog.has_solution("item(carrot, vegetable)")
        assert prolog.has_solution("item(potato, vegetable)")

    @pytest.mark.larl_exclude
    def test_retract_from_empty_database_succeeds(self):
        """Retracting when no clauses exist should still succeed."""
        prolog = PrologInterpreter()
        prolog.consult_string(":- dynamic nonexistent/1.")
        assert prolog.has_solution("retractall(nonexistent(_))")

    @pytest.mark.larl_exclude
    def test_retract_no_matching_clauses_succeeds(self):
        """Retracting when no clauses match should still succeed."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic fact/1.
            fact(a).
            fact(b).
        """)
        # Try to retract with a pattern that matches nothing
        assert prolog.has_solution("retractall(fact(x))")
        # Original facts should still exist
        assert prolog.has_solution("fact(a)")
        assert prolog.has_solution("fact(b)")


class TestRetractallPermissions:
    """Permission checks for retractall/1."""

    def test_retract_static_predicate_raises_error(self):
        """Attempting to retract from a static predicate should raise permission error."""
        prolog = PrologInterpreter()
        prolog.consult_string("static_fact(a).")

        with pytest.raises(PrologThrow) as exc_info:
            list(prolog.query("retractall(static_fact(_))"))

        error = exc_info.value.term
        assert error.functor == "error"
        assert error.args[0].functor == "permission_error"

    @pytest.mark.larl_exclude
    def test_retract_dynamic_predicate_succeeds(self):
        """Retracting from a dynamic predicate should succeed."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic dyn_fact/1.
            dyn_fact(x).
        """)
        assert prolog.has_solution("retractall(dyn_fact(_))")
        assert not prolog.has_solution("dyn_fact(_)")


class TestRetractallDeterminism:
    """Tests for deterministic behavior of retractall/1."""

    @pytest.mark.larl_exclude
    def test_succeeds_exactly_once(self):
        """retractall/1 should succeed exactly once (no backtracking)."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic fact/1.
            fact(a).
            fact(b).
            fact(c).
        """)
        results = list(prolog.query("retractall(fact(_))"))
        assert len(results) == 1

    @pytest.mark.larl_exclude
    def test_returns_original_substitution(self):
        """retractall/1 should return the original substitution unchanged."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic fact/1.
            fact(a).
        """)
        results = list(prolog.query("X = 5, retractall(fact(_)), Y = X"))
        assert len(results) == 1
        assert results[0]['X'] == 5
        assert results[0]['Y'] == 5


class TestRetractallComplexPatterns:
    """Tests for complex pattern matching in retractall/1."""

    @pytest.mark.larl_exclude
    def test_partial_instantiation(self):
        """Retract with partial instantiation."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic rel/3.
            rel(a, b, c).
            rel(a, x, y).
            rel(b, c, d).
        """)

        assert prolog.has_solution("retractall(rel(a, _, _))")

        assert not prolog.has_solution("rel(a, _, _)")
        assert prolog.has_solution("rel(b, c, d)")

    @pytest.mark.larl_exclude
    def test_retract_facts_vs_rules(self):
        """Retract should handle both facts and rules by head unification."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic pred/1.
            pred(a).
            pred(b).
            pred(X) :- X = computed.
        """)

        # retractall(pred(a)) unifies with pred(a) fact AND pred(X) rule
        # because pred(a) unifies with pred(X) where X=a
        # This is ISO-correct behavior
        assert prolog.has_solution("retractall(pred(a))")
        assert not prolog.has_solution("pred(a)")
        # The pred(b) fact should still exist
        assert prolog.has_solution("pred(b)")
        # The rule was also retracted because pred(a) unifies with pred(X)
        assert not prolog.has_solution("pred(computed)")

    @pytest.mark.larl_exclude
    def test_retract_all_clauses_including_rules(self):
        """Retract all clauses including rules with variable pattern."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic pred/1.
            pred(a).
            pred(b).
            pred(X) :- X = computed.
        """)

        # Use a pattern that matches everything
        assert prolog.has_solution("retractall(pred(_))")
        assert not prolog.has_solution("pred(_)")

    @pytest.mark.larl_exclude
    def test_multiple_arities(self):
        """Retract from predicates with different arities."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic foo/1.
            :- dynamic foo/2.
            foo(a).
            foo(b).
            foo(x, y).
            foo(p, q).
        """)

        # Retract only foo/1
        assert prolog.has_solution("retractall(foo(_))")
        assert not prolog.has_solution("foo(a)")
        assert not prolog.has_solution("foo(b)")
        # foo/2 should still exist
        assert prolog.has_solution("foo(x, y)")
        assert prolog.has_solution("foo(p, q)")


class TestRetractallIntegration:
    """Integration tests with other predicates."""

    @pytest.mark.larl_exclude
    def test_retractall_then_clause(self):
        """Verify clauses are gone using clause/2."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic fact/1.
            fact(a).
            fact(b).
        """)
        assert prolog.has_solution("clause(fact(a), true)")
        assert prolog.has_solution("retractall(fact(_))")
        assert not prolog.has_solution("clause(fact(_), _)")

    @pytest.mark.larl_exclude
    def test_retractall_with_assert(self):
        """Use retractall in combination with assert predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string(":- dynamic counter/1.")

        assert prolog.has_solution("assertz(counter(0))")
        result = prolog.query_once("counter(X)")
        assert result['X'] == 0

        assert prolog.has_solution("retractall(counter(_)), assertz(counter(5))")
        result = prolog.query_once("counter(X)")
        assert result['X'] == 5

    @pytest.mark.larl_exclude
    def test_retractall_multiple_times(self):
        """Multiple retractall calls should all succeed."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic fact/1.
            fact(a).
        """)
        assert prolog.has_solution("retractall(fact(_))")
        # Second call should also succeed even with empty database
        assert prolog.has_solution("retractall(fact(_))")


class TestRetractallIndexMaintenance:
    """Tests for first-argument index maintenance."""

    @pytest.mark.larl_exclude
    def test_index_updated_after_retractall(self):
        """Verify first-argument index is properly updated."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic indexed/1.
            indexed(alpha).
            indexed(beta).
            indexed(gamma).
        """)
        # Retract all
        assert prolog.has_solution("retractall(indexed(_))")
        # Add new facts
        assert prolog.has_solution("assertz(indexed(new1))")
        assert prolog.has_solution("assertz(indexed(new2))")
        # Verify new facts work
        assert prolog.has_solution("indexed(new1)")
        assert prolog.has_solution("indexed(new2)")
        assert not prolog.has_solution("indexed(alpha)")

    @pytest.mark.larl_exclude
    def test_partial_retractall_preserves_other_clauses(self):
        """Partial retraction should preserve other clauses correctly."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic data/2.
            data(1, a).
            data(2, a).
            data(1, b).
            data(2, b).
        """)
        # Retract only data(1, _)
        assert prolog.has_solution("retractall(data(1, _))")
        # Verify remaining clauses
        assert not prolog.has_solution("data(1, _)")
        assert prolog.has_solution("data(2, a)")
        assert prolog.has_solution("data(2, b)")


class TestRetractallPredicateIndicator:
    """Tests for predicate indicator form of retractall/1."""

    @pytest.mark.larl_exclude
    def test_retract_by_predicate_indicator(self):
        """Retract all clauses using Name/Arity form."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic foo/1.
            foo(a).
            foo(b).
            foo(c).
        """)
        assert prolog.has_solution("foo(_)")
        assert prolog.has_solution("retractall(foo/1)")
        assert not prolog.has_solution("foo(_)")

    @pytest.mark.larl_exclude
    def test_retract_zero_arity_by_indicator(self):
        """Retract zero-arity predicates using Name/0 form."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic flag/0.
            flag.
        """)
        assert prolog.has_solution("flag")
        assert prolog.has_solution("retractall(flag/0)")
        assert not prolog.has_solution("flag")

    @pytest.mark.larl_exclude
    def test_retract_multi_arity_by_indicator(self):
        """Retract multi-arity predicates using Name/N form."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic rel/3.
            rel(a, b, c).
            rel(x, y, z).
        """)
        assert prolog.has_solution("rel(_, _, _)")
        assert prolog.has_solution("retractall(rel/3)")
        assert not prolog.has_solution("rel(_, _, _)")


class TestRetractallModules:
    """Tests for module interaction."""

    @pytest.mark.larl_exclude
    def test_retractall_in_module(self):
        """Test retractall with module predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(test_mod, [test_pred/1]).
            :- dynamic test_pred/1.
            test_pred(a).
            test_pred(b).
        """)
        # Retract using module-qualified name
        assert prolog.has_solution("retractall(test_mod:test_pred(_))")
        assert not prolog.has_solution("test_mod:test_pred(_)")
