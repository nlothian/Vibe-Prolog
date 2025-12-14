"""Tests for recursion depth limit enforcement."""

import pytest
from vibeprolog import PrologInterpreter


class TestRecursionDepthLimits:
    """Test that recursion depth is enforced."""

    def test_infinite_recursion_raises_error(self):
        """Infinite recursion raises resource_error."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            infinite :- infinite.
        """)

        with pytest.raises(Exception) as exc_info:
            prolog.query_once("infinite")

        # Should be resource_error, not Python RecursionError
        assert "resource_error" in str(exc_info.value)
        assert "recursion_depth" in str(exc_info.value).lower()

    @pytest.mark.larl_exclude
    def test_deep_but_finite_recursion_works(self):
        """Recursion within limit should work."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            count_down(0) :- !.
            count_down(N) :- N > 0, N1 is N - 1, count_down(N1).
        """)

        # Should work - only 100 deep
        assert prolog.has_solution("count_down(100)")

    def test_exactly_at_limit(self):
        """Recursion exactly at limit should be allowed (limit is exclusive)."""
        prolog = PrologInterpreter(max_recursion_depth=201)
        prolog.consult_string("""
            count(0).
            count(N) :- N > 0, N1 is N - 1, count(N1).
        """)

        # Should work within limit: 200 recursion depth
        assert prolog.has_solution("count(200)")

    def test_over_limit_raises_error(self):
        """Recursion depth exceeded should raise resource_error."""
        prolog = PrologInterpreter(max_recursion_depth=200)
        prolog.consult_string("""
            count(0).
            count(N) :- N > 0, N1 is N - 1, count(N1).
        """)
        with pytest.raises(Exception) as exc_info:
            prolog.query_once("count(201)")
        assert "resource_error" in str(exc_info.value).lower()
        assert "recursion_depth" in str(exc_info.value).lower()

    def test_one_over_limit_fails(self):
        """Recursion one over limit should raise error."""
        prolog = PrologInterpreter(max_recursion_depth=100)
        prolog.consult_string("""
            count(0).
            count(N) :- N > 0, N1 is N - 1, count(N1).
        """)

        # One over limit should fail
        with pytest.raises(Exception) as exc_info:
            prolog.query_once("count(101)")
        assert "resource_error" in str(exc_info.value)

    def test_configurable_depth_limit(self):
        """Depth limit should be configurable."""
        # Small limit
        prolog_small = PrologInterpreter(max_recursion_depth=10)
        prolog_small.consult_string("count(0). count(N) :- N > 0, N1 is N - 1, count(N1).")

        with pytest.raises(Exception):
            prolog_small.query_once("count(11)")

        # Larger limit
        prolog_large = PrologInterpreter(max_recursion_depth=200)
        prolog_large.consult_string("count(0). count(N) :- N > 0, N1 is N - 1, count(N1).")

        assert prolog_large.has_solution("count(5)")

    def test_mutual_recursion_depth(self):
        """Mutual recursion should count depth correctly."""
        prolog = PrologInterpreter(max_recursion_depth=30)
        prolog.consult_string("""
            even(0).
            even(N) :- N > 0, N1 is N - 1, odd(N1).
            odd(N) :- N > 0, N1 is N - 1, even(N1).
        """)

        # Should work within limit
        assert prolog.has_solution("even(10)")

        # Should fail over limit
        with pytest.raises(Exception) as exc_info:
            prolog.query_once("even(30)")
        assert "resource_error" in str(exc_info.value)

    def test_error_includes_context(self):
        """Error should include predicate context."""
        prolog = PrologInterpreter(max_recursion_depth=10)
        prolog.consult_string("""
            loop :- loop.
        """)

        with pytest.raises(Exception) as exc_info:
            prolog.query_once("loop")

        error_msg = str(exc_info.value)
        assert "resource_error" in error_msg
        # Should mention the predicate
        assert "loop" in error_msg or "context" in error_msg

    def test_depth_reset_between_queries(self):
        """Depth should reset for each query."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            count(0).
            count(N) :- N > 0, N1 is N - 1, count(N1).
        """)

        # First query
        assert prolog.has_solution("count(100)")

        # Second query - should not count from previous depth
        assert prolog.has_solution("count(100)")

    def test_backtracking_with_depth_check(self):
        """Backtracking should work with depth checking."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            gen(0, 0).
            gen(N, N) :- N > 0.
            gen(N, X) :- N > 0, N1 is N - 1, gen(N1, X).
        """)

        # Should get all solutions despite depth checking
        results = list(prolog.query("gen(3, X)"))
        assert len(results) == 4
        values = [r['X'] for r in results]
        assert set(values) == {0, 1, 2, 3}


class TestNonRecursiveQueriesUnaffected:
    """Test that normal queries aren't affected."""

    def test_simple_query(self):
        """Simple non-recursive query works."""
        prolog = PrologInterpreter()
        prolog.consult_string("fact(a, 1). fact(b, 2).")
        result = prolog.query_once("fact(a, X)")
        assert result is not None
        assert result['X'] == 1

    def test_moderate_nesting(self):
        """Moderate nesting in rules works."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            a :- b, c.
            b :- d, e.
            c :- f.
            d.
            e.
            f.
        """)
        assert prolog.has_solution("a")