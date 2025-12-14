"""Tests for cut operator (!) behavior in module predicates."""

import pytest
from vibeprolog import PrologInterpreter


class TestModuleCut:
    """Test that cut operator works correctly in module predicates."""

    @pytest.mark.larl_exclude
    def test_cut_in_module_predicate(self):
        """Test that cut prevents backtracking in module predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(test_mod, [choice/1]).

            choice(first) :- !.
            choice(second).
            choice(third).
        """)

        # Query the module predicate - should only get first solution due to cut
        results = list(prolog.query("test_mod:choice(X)"))
        assert len(results) == 1
        assert results[0]["X"] == "first"

    @pytest.mark.larl_exclude
    def test_cut_in_module_predicate_with_condition(self):
        """Test cut in module predicate with conditional logic."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(test_mod, [classify/2]).

            classify(X, positive) :- X > 0, !.
            classify(0, zero) :- !.
            classify(X, negative).
        """)

        # Test positive number
        result = prolog.query_once("test_mod:classify(5, Class)")
        assert result["Class"] == "positive"

        # Test zero
        result = prolog.query_once("test_mod:classify(0, Class)")
        assert result["Class"] == "zero"

        # Test negative number
        result = prolog.query_once("test_mod:classify(-3, Class)")
        assert result["Class"] == "negative"

        # Verify no backtracking occurs (should get exactly one solution each)
        results = list(prolog.query("test_mod:classify(5, Class)"))
        assert len(results) == 1

    @pytest.mark.larl_exclude
    def test_cut_in_module_nested_calls(self):
        """Test that cut in module predicate doesn't affect other predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(test_mod, [process/2]).

            helper(a) :- !.
            helper(b).

            process(X, Y) :-
                helper(Y),
                X = Y.
        """)

        # Should only get one solution due to cut in helper
        results = list(prolog.query("test_mod:process(X, Y)"))
        assert len(results) == 1
        assert results[0]["X"] == "a"
        assert results[0]["Y"] == "a"

    @pytest.mark.larl_exclude
    def test_cut_combined_with_module_qualified_calls(self):
        """Test cut behavior with multiple module-qualified calls."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(mod1, [pred1/1]).
            :- module(mod2, [pred2/1]).

            :- module(mod1, [pred1/1]).
            pred1(X) :- X = a, !.
            pred1(X) :- X = b.

            :- module(mod2, [pred2/1]).
            pred2(X) :- mod1:pred1(X).
        """)

        # Cut in mod1:pred1 should prevent backtracking
        results = list(prolog.query("mod2:pred2(X)"))
        assert len(results) == 1
        assert results[0]["X"] == "a"

    @pytest.mark.larl_exclude
    def test_cut_doesnt_leak_between_modules(self):
        """Test that cut in one module doesn't affect another module."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(mod1, [test/1]).
            :- module(mod2, [test/1]).

            :- module(mod1, [test/1]).
            test(a) :- !.
            test(b).

            :- module(mod2, [test/1]).
            test(x).
            test(y).
        """)

        # mod1:test should be cut after first solution
        results = list(prolog.query("mod1:test(X)"))
        assert len(results) == 1
        assert results[0]["X"] == "a"

        # mod2:test should have all solutions (no cut)
        results = list(prolog.query("mod2:test(X)"))
        assert len(results) == 2
        assert results[0]["X"] == "x"
        assert results[1]["X"] == "y"
