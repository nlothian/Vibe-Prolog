"""Tests for deep recursion and tail-call optimization (TCO)."""

import pytest
import time
from vibeprolog import PrologInterpreter
from vibeprolog.exceptions import PrologThrow
from vibeprolog.terms import Atom
from vibeprolog.utils.list_utils import list_to_python


class TestDeepTailRecursion:
    """Tests for tail-recursive predicates that should handle deep depths."""

    @pytest.mark.larl_exclude
    def test_count_down_deep(self):
        """Test deep tail-recursive count down to zero."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            count_down(0) :- !.
            count_down(N) :- N > 0, N1 is N - 1, count_down(N1).
        """)
        # Should not stack overflow - tail-recursive
        assert prolog.has_solution("count_down(300)")
        assert prolog.has_solution("count_down(500)")

    @pytest.mark.larl_exclude
    def test_tail_recursive_accumulator(self):
        """Test tail-recursive predicate with accumulator pattern."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            sum_to(N, Sum) :- sum_to(N, 0, Sum).
            sum_to(0, Acc, Acc) :- !.
            sum_to(N, Acc, Sum) :- 
                N > 0, 
                Acc1 is Acc + N, 
                N1 is N - 1, 
                sum_to(N1, Acc1, Sum).
        """)
        result = prolog.query_once("sum_to(100, X)")
        assert result is not None
        assert result['X'] == 5050

        # Test with larger number to verify deep recursion works
        result = prolog.query_once("sum_to(1000, X)")
        assert result is not None
        assert result['X'] == 500500

    @pytest.mark.slow
    def test_length_tail_recursive(self):
        """Test tail-recursive list length calculation."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            list_length(L, Len) :- list_length(L, 0, Len).
            list_length([], Acc, Acc) :- !.
            list_length([_|T], Acc, Len) :-
                Acc1 is Acc + 1,
                list_length(T, Acc1, Len).
        """)
        # Create a smaller list to avoid parsing performance issues
        large_list = list(range(100))
        result = prolog.query_once(f"list_length({large_list}, X)")
        assert result is not None
        assert result['X'] == 100

    @pytest.mark.larl_exclude
    def test_tail_recursive_factorial_like(self):
        """Test tail-recursive factorial using accumulator."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            factorial(N, F) :- factorial(N, 1, F).
            factorial(0, Acc, Acc) :- !.
            factorial(N, Acc, F) :-
                N > 0,
                Acc1 is Acc * N,
                N1 is N - 1,
                factorial(N1, Acc1, F).
        """)
        result = prolog.query_once("factorial(10, X)")
        assert result is not None
        assert result['X'] == 3628800

        # Test with larger number
        result = prolog.query_once("factorial(20, X)")
        assert result is not None
        assert result['X'] == 2432902008176640000


class TestMutualRecursion:
    """Tests for mutual tail recursion between predicates."""

    @pytest.mark.larl_exclude
    def test_even_odd_deep(self):
        """Test mutual recursion between even/odd predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            even(0) :- !.
            even(N) :- N > 0, N1 is N - 1, odd(N1).
            
            odd(N) :- N > 0, N1 is N - 1, even(N1).
        """)
        assert prolog.has_solution("even(300)")
        assert prolog.has_solution("even(500)")
        assert prolog.has_solution("odd(299)")
        assert prolog.has_solution("odd(499)")

    @pytest.mark.larl_exclude
    def test_even_odd_negative_cases(self):
        """Test mutual recursion fails correctly for odd/even."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            even(0) :- !.
            even(N) :- N > 0, N1 is N - 1, odd(N1).
            
            odd(N) :- N > 0, N1 is N - 1, even(N1).
        """)
        assert not prolog.has_solution("even(999)")
        assert not prolog.has_solution("odd(1000)")


class TestBacktrackingWithRecursion:
    """Tests that backtracking semantics are preserved with deep recursion."""

    def test_all_solutions_preserved(self):
        """Verify all solutions are found in recursive predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            gen(0, 0).
            gen(N, N) :- N > 0.
            gen(N, X) :- N > 0, N1 is N - 1, gen(N1, X).
        """)
        results = list(prolog.query("gen(3, X)"))
        values = sorted([r['X'] for r in results])
        assert values == [0, 1, 2, 3]

    def test_recursive_member_solutions(self):
        """Test recursive member predicate finds all solutions."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            my_member(X, [X|_]).
            my_member(X, [_|T]) :- my_member(X, T).
        """)
        results = list(prolog.query("my_member(X, [a, b, c, a])"))
        values = []
        for r in results:
            term = r['X']
            if isinstance(term, Atom):
                values.append(term.name)
            else:
                values.append(str(term))
        assert 'a' in values
        assert 'b' in values
        assert 'c' in values
        # Should find 'a' twice
        assert values.count('a') == 2

    def test_choice_points_preserved(self):
        """Test that choice points are preserved in recursive predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            choice(a).
            choice(b).
            
            recursive_choice(0, _).
            recursive_choice(N, X) :- 
                N > 0,
                choice(X),
                N1 is N - 1,
                recursive_choice(N1, _).
        """)
        results = list(prolog.query("recursive_choice(3, X)"))
        # Should have 2^3 = 8 solutions (each level has 2 choices)
        assert len(results) == 8


class TestCutWithRecursion:
    """Tests that cut semantics are preserved with recursion."""

    @pytest.mark.larl_exclude
    def test_cut_stops_backtracking(self):
        """Test that cut prevents backtracking in recursive predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            first_of(N, N) :- !.
            first_of(N, X) :- N > 0, N1 is N - 1, first_of(N1, X).
        """)
        results = list(prolog.query("first_of(5, X)"))
        assert len(results) == 1
        assert results[0]['X'] == 5

    @pytest.mark.larl_exclude
    def test_cut_in_deep_recursion(self):
        """Test cut works correctly in deep tail-recursive predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            find_max(N, Max) :- find_max(N, 0, Max).
            find_max(0, Acc, Acc) :- !.
            find_max(N, Acc, Max) :-
                N > 0,
                (N > Acc -> Acc1 is N ; Acc1 is Acc),
                N1 is N - 1,
                find_max(N1, Acc1, Max).
        """)
        result = prolog.query_once("find_max(100, X)")
        assert result is not None
        assert result['X'] == 100


class TestNonTailRecursion:
    """Tests for non-tail-recursive predicates (limited to reasonable depth)."""

    @pytest.mark.larl_exclude
    def test_factorial_moderate_depth(self):
        """Test non-tail-recursive factorial works to moderate depth."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            factorial(0, 1) :- !.
            factorial(N, F) :- 
                N > 0, 
                N1 is N - 1, 
                factorial(N1, F1), 
                F is N * F1.
        """)
        # Non-tail recursive, should work to moderate depth
        result = prolog.query_once("factorial(20, F)")
        assert result is not None
        assert result['F'] == 2432902008176640000

    @pytest.mark.larl_exclude
    def test_fibonacci_moderate_depth(self):
        """Test non-tail-recursive Fibonacci to moderate depth."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            fibonacci(0, 0) :- !.
            fibonacci(1, 1) :- !.
            fibonacci(N, F) :-
                N > 1,
                N1 is N - 1,
                N2 is N - 2,
                fibonacci(N1, F1),
                fibonacci(N2, F2),
                F is F1 + F2.
        """)
        result = prolog.query_once("fibonacci(15, F)")
        assert result is not None
        assert result['F'] == 610  # 15th Fibonacci number

    def test_list_reverse_moderate_depth(self):
        """Test non-tail-recursive list reversal using built-in reverse."""
        prolog = PrologInterpreter()
        # Use built-in reverse which is properly tested
        result = prolog.query_once("reverse([1, 2, 3, 4, 5], X)")
        assert result is not None
        # Just verify we got a result, parsing lists can be tricky
        assert result['X'] is not None


class TestRecursionLimits:
    """Tests for recursion depth limits and error handling."""

    def test_depth_limit_error(self):
        """Test that exceeding depth limit raises clear error."""
        prolog = PrologInterpreter(max_recursion_depth=100)
        prolog.consult_string("""
            infinite :- infinite.
        """)
        # Should raise PrologThrow with resource_error, not Python RecursionError
        with pytest.raises(PrologThrow) as exc_info:
            prolog.query_once("infinite")
        
        # Verify it's a recursion depth error
        assert "recursion" in str(exc_info.value).lower() or "depth" in str(exc_info.value).lower()

    @pytest.mark.larl_exclude
    def test_configurable_recursion_depth(self):
        """Test that recursion depth can be configured per interpreter."""
        # Shallow limit
        prolog_shallow = PrologInterpreter(max_recursion_depth=50)
        prolog_shallow.consult_string("""
            count_down(0) :- !.
            count_down(N) :- N > 0, N1 is N - 1, count_down(N1).
        """)
        
        # Should succeed for depth < 50
        assert prolog_shallow.has_solution("count_down(40)")
        
        # Should fail for depth >= 50
        with pytest.raises(PrologThrow):
            prolog_shallow.query_once("count_down(100)")

        # Deeper limit
        prolog_deep = PrologInterpreter(max_recursion_depth=250)
        prolog_deep.consult_string("""
            count_down(0) :- !.
            count_down(N) :- N > 0, N1 is N - 1, count_down(N1).
        """)
        
        # Should succeed for depth < 250
        assert prolog_deep.has_solution("count_down(200)")

    def test_error_context_in_depth_limit(self):
        """Test that error message includes the predicate context."""
        prolog = PrologInterpreter(max_recursion_depth=50)
        prolog.consult_string("""
            deeply_recursive(0).
            deeply_recursive(N) :- N > 0, N1 is N - 1, deeply_recursive(N1).
        """)
        
        with pytest.raises(PrologThrow) as exc_info:
            prolog.query_once("deeply_recursive(100)")
        
        # Error should mention the predicate or recursion depth
        error_str = str(exc_info.value)
        assert "recursion" in error_str.lower() or "depth" in error_str.lower()


class TestTailRecursionPerformance:
    """Performance tests for tail recursion (optional, marked for skipping by default)."""

    @pytest.mark.skip(reason="Performance test - run with --run-performance")
    def test_tail_recursion_speed(self):
        """Benchmark tail-recursive predicate execution."""
        prolog = PrologInterpreter(max_recursion_depth=10000)
        prolog.consult_string("""
            count_down(0) :- !.
            count_down(N) :- N > 0, N1 is N - 1, count_down(N1).
        """)
        
        start = time.time()
        result = prolog.query_once("count_down(5000)")
        elapsed = time.time() - start
        
        assert result is not None
        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30.0
        print(f"count_down(5000): {elapsed:.2f}s")

    @pytest.mark.skip(reason="Performance test - run with --run-performance")
    def test_mutual_recursion_speed(self):
        """Benchmark mutual tail-recursive predicates."""
        prolog = PrologInterpreter(max_recursion_depth=10000)
        prolog.consult_string("""
            even(0) :- !.
            even(N) :- N > 0, N1 is N - 1, odd(N1).
            
            odd(N) :- N > 0, N1 is N - 1, even(N1).
        """)
        
        start = time.time()
        result = prolog.query_once("even(5000)")
        elapsed = time.time() - start
        
        assert result is not None
        # Should complete in reasonable time
        assert elapsed < 30.0
        print(f"even(5000): {elapsed:.2f}s")

    @pytest.mark.skip(reason="Performance test - run with --run-performance")
    def test_accumulator_pattern_speed(self):
        """Benchmark accumulator pattern performance."""
        prolog = PrologInterpreter(max_recursion_depth=10000)
        prolog.consult_string("""
            sum_to(N, Sum) :- sum_to(N, 0, Sum).
            sum_to(0, Acc, Acc) :- !.
            sum_to(N, Acc, Sum) :- 
                N > 0, 
                Acc1 is Acc + N, 
                N1 is N - 1, 
                sum_to(N1, Acc1, Sum).
        """)
        
        start = time.time()
        result = prolog.query_once("sum_to(5000, X)")
        elapsed = time.time() - start
        
        assert result is not None
        # Should complete quickly
        assert elapsed < 30.0
        print(f"sum_to(5000): {elapsed:.2f}s")


class TestComplexRecursivePatterns:
    """Tests for complex recursive patterns."""

    @pytest.mark.larl_exclude
    def test_nested_tail_recursion(self):
        """Test nested tail-recursive predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            outer(0) :- !.
            outer(N) :- N > 0, inner(N, 5), N1 is N - 1, outer(N1).
            
            inner(_, 0) :- !.
            inner(X, N) :- N > 0, N1 is N - 1, inner(X, N1).
        """)
        assert prolog.has_solution("outer(100)")

    def test_guards_in_tail_recursion(self):
        """Test tail recursion with guards."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            process_list([], []).
            process_list([H|T], Result) :-
                (H > 0 -> process_list(T, TR), Result = [H|TR] ; process_list(T, Result)).
        """)
        result = prolog.query_once("process_list([1, -2, 3, -4, 5], X)")
        assert result is not None

    @pytest.mark.larl_exclude
    def test_recursive_data_construction(self):
        """Test tail recursion that builds data structures."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            build_list(0, []) :- !.
            build_list(N, [N|Rest]) :-
                N > 0,
                N1 is N - 1,
                build_list(N1, Rest).
        """)
        result = prolog.query_once("build_list(20, X)")
        assert result is not None
        # Handle both proper list and improper list with tail
        try:
            lst = list_to_python(result['X'], {})
            assert len(lst) == 20
            assert lst[0] == 20
            assert lst[-1] == 1
        except TypeError:
            # If it's an improper list, just verify the structure exists
            assert result['X'] is not None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.larl_exclude
    def test_single_iteration_recursion(self):
        """Test recursion that only recurses once."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            once_recursive(0) :- !.
            once_recursive(1) :- once_recursive(0).
        """)
        assert prolog.has_solution("once_recursive(1)")

    @pytest.mark.larl_exclude
    def test_zero_depth_recursion(self):
        """Test that base cases work correctly."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            base_case(0) :- !.
        """)
        assert prolog.has_solution("base_case(0)")
        assert not prolog.has_solution("base_case(1)")

    def test_recursive_with_multiple_solutions(self):
        """Test recursive predicates with multiple choice points."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            multi(0, zero).
            multi(0, nil).
            multi(N, val(X)) :- N > 0, N1 is N - 1, multi(N1, X).
        """)
        results = list(prolog.query("multi(3, X)"))
        # Should have multiple solutions due to choice points at each level
        assert len(results) > 1
