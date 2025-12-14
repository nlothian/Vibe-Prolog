"""Tests for once/1 built-in predicate."""

import pytest
from vibeprolog import PrologInterpreter


class TestOnce:
    """Tests for once/1 predicate."""

    def test_once_with_single_solution(self):
        """once/1 should succeed once when goal has single solution."""
        prolog = PrologInterpreter()
        prolog.consult_string("fact(a).")

        # Should succeed with single solution
        result = prolog.query_once("once(fact(X))")
        assert result is not None
        assert result['X'] == 'a'

    def test_once_with_multiple_solutions(self):
        """once/1 should return only first solution when goal has multiple solutions."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            fact(a).
            fact(b).
            fact(c).
        """)

        # Should only get the first solution
        result = prolog.query_once("once(fact(X))")
        assert result is not None
        assert result['X'] == 'a'  # Should be first one

        # Verify that without once, we get all solutions
        results = list(prolog.query("fact(X)"))
        assert len(results) == 3

    def test_once_fails_when_goal_fails(self):
        """once/1 should fail when the goal fails."""
        prolog = PrologInterpreter()
        prolog.consult_string("fact(a).")

        # Should fail because fact(z) doesn't exist
        result = prolog.query_once("once(fact(z))")
        assert result is None

    def test_once_with_member(self):
        """once/1 should return only first member of a list."""
        prolog = PrologInterpreter()

        # member/2 would normally backtrack through all elements
        result = prolog.query_once("once(member(X, [1, 2, 3]))")
        assert result is not None
        assert result['X'] == 1

        # Without once, should get all three
        results = list(prolog.query("member(X, [1, 2, 3])"))
        assert len(results) == 3

    def test_once_with_side_effects(self):
        """once/1 should execute side effects only once."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            test(X) :- member(X, [1, 2, 3]), format('X=~w ', [X]).
        """)

        import io
        import sys

        # Test with once - should print only once
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        result = prolog.query_once("once(test(X))")
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        assert result is not None
        assert result['X'] == 1
        assert output == 'X=1 '  # Should only print once

        # Test without once - should print three times
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        results = list(prolog.query("test(X)"))
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        assert len(results) == 3
        assert output == 'X=1 X=2 X=3 '  # Should print three times

    def test_once_with_conjunction(self):
        """once/1 should work with conjunctions."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            person(alice).
            person(bob).
            age(alice, 30).
            age(bob, 25).
        """)

        # Should get first person with their age
        result = prolog.query_once("once((person(X), age(X, Y)))")
        assert result is not None
        assert result['X'] == 'alice'
        assert result['Y'] == 30

    def test_once_with_disjunction(self):
        """once/1 should work with disjunctions."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            cat(fluffy).
            dog(rover).
        """)

        # Should get first solution from disjunction
        result = prolog.query_once("once((cat(X) ; dog(X)))")
        assert result is not None
        assert result['X'] == 'fluffy'  # cat comes first

    def test_once_nested(self):
        """once/1 should work when nested."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            outer(a).
            outer(b).
            inner(1).
            inner(2).
        """)

        # Nested once: should get first outer and first inner
        result = prolog.query_once("once((outer(X), once(inner(Y))))")
        assert result is not None
        assert result['X'] == 'a'
        assert result['Y'] == 1

    @pytest.mark.larl_exclude
    def test_once_with_cut(self):
        """once/1 should be similar to (Goal, !) in behavior."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            fact(a).
            fact(b).
            fact(c).
        """)

        # once(fact(X)) should behave like (fact(X), !)
        result_once = prolog.query_once("once(fact(X))")

        # This should also give just one solution due to cut
        result_cut = prolog.query_once("fact(X), !")

        assert result_once == result_cut

    def test_once_with_arithmetic(self):
        """once/1 should work with arithmetic goals."""
        prolog = PrologInterpreter()

        # Should succeed once
        result = prolog.query_once("once(X is 2 + 3)")
        assert result is not None
        assert result['X'] == 5

    def test_once_with_unification(self):
        """once/1 should work with unification."""
        prolog = PrologInterpreter()

        # Should succeed once
        result = prolog.query_once("once(X = hello)")
        assert result is not None
        assert result['X'] == 'hello'

    def test_once_with_findall(self):
        """once/1 should collect all solutions within findall, but findall itself runs once."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            num(1).
            num(2).
            num(3).
        """)

        # findall inside once - should run findall once (which collects all)
        result = prolog.query_once("once(findall(X, num(X), L))")
        assert result is not None
        assert result['L'] == [1, 2, 3]

    def test_once_true(self):
        """once/1 should succeed once with true."""
        prolog = PrologInterpreter()

        result = prolog.query_once("once(true)")
        assert result == {}  # Empty substitution (success)

    def test_once_fail(self):
        """once/1 should fail with fail."""
        prolog = PrologInterpreter()

        result = prolog.query_once("once(fail)")
        assert result is None

    def test_once_all_solutions(self):
        """Test that once/1 truly limits to one solution even when querying all."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            fact(a).
            fact(b).
            fact(c).
        """)

        # Even when asking for all solutions, once should give only one
        results = list(prolog.query("once(fact(X))"))
        assert len(results) == 1
        assert results[0]['X'] == 'a'

    def test_once_with_variables(self):
        """once/1 should properly handle variable bindings."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            choice(1).
            choice(2).
            choice(3).
        """)

        # Should get first solution
        result = prolog.query_once("once(choice(X))")
        assert result is not None
        assert result['X'] == 1

        # Without once, should get multiple solutions
        results = list(prolog.query("choice(X)"))
        assert len(results) == 3

        # Test with member to verify variable binding
        result = prolog.query_once("once(member(X, [a, b, c]))")
        assert result is not None
        assert result['X'] == 'a'
