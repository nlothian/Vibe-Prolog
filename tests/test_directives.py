"""Tests for Prolog directives, particularly initialization/1."""

import pytest
from vibeprolog import PrologInterpreter
from vibeprolog.exceptions import PrologThrow
from vibeprolog.terms import Atom, Compound


class TestInitializationDirective:
    """Tests for the :- initialization/1 directive."""

    def test_single_initialization_simple_goal(self):
        """Test single initialization directive with simple goal."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- initialization(write('Hello World')).
            test_predicate.
        """)

        # The initialization goal should have executed during consult
        # We can't easily test the output, but we can check that consult completed
        assert len(prolog.clauses) == 1
        assert prolog.clauses[0].head.name == "test_predicate"

    def test_multiple_initialization_goals_order(self):
        """Test multiple initialization directives execute in order."""
        prolog = PrologInterpreter()

        # We'll use asserta/assertz to create side effects we can check
        prolog.consult_string("""
            :- initialization(assertz(initialized(first))).
            :- initialization(assertz(initialized(second))).
            :- initialization(assertz(initialized(third))).

            base_fact.
        """)

        # Check that all initialization goals executed in order
        results = prolog.query("initialized(X)")
        values = [result['X'] for result in results]
        assert values == ['first', 'second', 'third']

    def test_initialization_with_side_effects(self):
        """Test initialization that performs side effects visible after consult."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- initialization(assertz(side_effect_fact)).
            :- initialization(assertz(another_fact(X))).

            base_clause.
        """)

        # Check that the side effects are visible
        assert prolog.has_solution("side_effect_fact")
        assert prolog.has_solution("another_fact(X)")

    def test_initialization_accessing_facts_in_same_file(self):
        """Test initialization accessing facts defined in the same file."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            data(fact1).
            data(fact2).

            :- initialization((data(X), assertz(processed(X)))).
        """)

        # Check that initialization processed the data
        results = prolog.query("processed(X)")
        values = sorted([result['X'] for result in results])
        assert values == ['fact1', 'fact2']

    def test_empty_initialization(self):
        """Test initialization with true (empty goal)."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- initialization(true).
            test_fact.
        """)

        # Should complete without error
        assert len(prolog.clauses) == 1

    def test_initialization_with_complex_goals(self):
        """Test initialization with conjunctions and disjunctions."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- initialization((assertz(complex1), assertz(complex2))).
            test_fact.
        """)

        assert prolog.has_solution("complex1")
        assert prolog.has_solution("complex2")

    def test_initialization_with_io(self):
        """Test initialization that performs I/O operations."""
        prolog = PrologInterpreter()
        # This should not raise an exception
        prolog.consult_string("""
            :- initialization(write('Init message')).
            test_fact.
        """)

        assert len(prolog.clauses) == 1

    def test_initialization_in_multiple_consults(self):
        """Test initialization in multiple consulted files/strings."""
        prolog = PrologInterpreter()

        prolog.consult_string("""
            :- initialization(assertz(from_first)).
            first_fact.
        """)

        prolog.consult_string("""
            :- initialization(assertz(from_second)).
            second_fact.
        """)

        assert prolog.has_solution("from_first")
        assert prolog.has_solution("from_second")
        assert prolog.has_solution("first_fact")
        assert prolog.has_solution("second_fact")

    # Error handling tests

    def test_non_callable_goal_number(self):
        """Test error when goal is a number."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(":- initialization(42).")

        error = exc_info.value.term
        assert error.functor == "error"
        assert error.args[0].functor == "type_error"
        assert error.args[0].args[0].name == "callable"

    def test_non_callable_goal_variable(self):
        """Test error when goal is an unbound variable."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(":- initialization(X).")

        error = exc_info.value.term
        assert error.functor == "error"
        assert error.args[0].name == "instantiation_error"

    def test_initialization_goal_failure(self):
        """Test initialization goal that fails."""
        prolog = PrologInterpreter()
        # fail/0 should fail but not prevent consult completion
        prolog.consult_string("""
            :- initialization(fail).
            test_fact.
        """)

        # Consult should complete despite failed initialization
        assert len(prolog.clauses) == 1

    def test_initialization_goal_exception(self):
        """Test initialization goal that throws an exception."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow):
            prolog.consult_string("""
                :- initialization(throw(test_error)).
                test_fact.
            """)

    def test_initialization_wrong_arity(self):
        """Test initialization with wrong number of arguments."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(":- initialization(goal1, goal2).")

        error = exc_info.value.term
        assert error.functor == "error"
        assert error.args[0].functor == "type_error"
        assert error.args[0].args[0].name == "callable"

    def test_initialization_non_callable_list(self):
        """Test error when goal is an empty list."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(":- initialization([]).")

        error = exc_info.value.term
        assert error.functor == "error"
        assert error.args[0].functor == "type_error"
        assert error.args[0].args[0].name == "callable"


class TestDirectiveParsing:
    """Tests for directive parsing in general."""

    def test_directive_syntax(self):
        """Test that directives are parsed correctly."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- initialization(true).
            normal_fact.
        """)

        # Should parse without error
        assert len(prolog.clauses) == 1

    def test_mixed_clauses_and_directives(self):
        """Test mixing clauses and directives."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            fact1.
            :- initialization(assertz(init_done)).
            fact2.
            :- initialization(assertz(init_done2)).
            fact3.
        """)

        assert len(prolog.clauses) == 5  # 3 original facts + 2 added by initialization
        assert prolog.has_solution("init_done")
        assert prolog.has_solution("init_done2")