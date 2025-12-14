"""
Tests for backtracking behavior.
Tests how the interpreter handles choice points and backtracking.
"""

import pytest
from vibeprolog import PrologInterpreter


class TestBasicBacktracking:
    """Basic backtracking tests"""

    def test_multiple_facts(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            color(red).
            color(green).
            color(blue).
        """)

        # Should backtrack through all solutions
        results = list(prolog.query("color(X)"))
        assert len(results) == 3
        colors = {r['X'] for r in results}
        assert colors == {'red', 'green', 'blue'}

    def test_backtracking_in_conjunction(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            p(1).
            p(2).
            q(a).
            q(b).
        """)

        # Should try all combinations
        results = list(prolog.query("p(X), q(Y)"))
        assert len(results) == 4

        # Verify all combinations exist
        combinations = {(r['X'], r['Y']) for r in results}
        expected = {(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')}
        assert combinations == expected


class TestBacktrackingWithRules:
    """Backtracking through rule clauses"""

    def test_multiple_rule_clauses(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            route(a, b).
            route(b, c).
            route(c, d).

            connected(X, Y) :- route(X, Y).
            connected(X, Y) :- route(Y, X).
        """)

        # Should find both directions
        results = list(prolog.query("connected(b, X)"))
        assert len(results) == 2
        connected_to = {r['X'] for r in results}
        assert connected_to == {'c', 'a'}  # b->c and a->b (reversed)

    def test_recursive_backtracking(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            edge(a, b).
            edge(b, c).
            edge(a, d).

            reachable(X, Y) :- edge(X, Y).
            reachable(X, Z) :- edge(X, Y), reachable(Y, Z).
        """)

        # Find all nodes reachable from 'a'
        results = list(prolog.query("reachable(a, X)"))
        reachable = {r['X'] for r in results}
        assert 'b' in reachable
        assert 'c' in reachable
        assert 'd' in reachable


class TestFailureAndBacktracking:
    """Testing failure-driven backtracking"""

    def test_failure_causes_backtracking(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            p(1).
            p(2).
            p(3).
            q(2).
        """)

        # Only p(2) should succeed because q(2) exists
        results = list(prolog.query("p(X), q(X)"))
        assert len(results) == 1
        assert results[0]['X'] == 2

    def test_nested_backtracking(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            num(1).
            num(2).
            num(3).
        """)

        # Find pairs where X < Y
        results = list(prolog.query("num(X), num(Y), X < Y"))
        assert len(results) == 3

        pairs = {(r['X'], r['Y']) for r in results}
        expected = {(1, 2), (1, 3), (2, 3)}
        assert pairs == expected


class TestCutAndBacktracking:
    """Testing cut's effect on backtracking"""

    @pytest.mark.larl_exclude
    def test_cut_in_rule(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            max(X, Y, X) :- X >= Y, !.
            max(X, Y, Y).
        """)

        # When first clause succeeds, cut prevents trying second clause
        result = prolog.query_once("max(5, 3, M)")
        assert result is not None
        assert result['M'] == 5

        # When first clause fails, try second clause
        result = prolog.query_once("max(3, 5, M)")
        assert result is not None
        assert result['M'] == 5

    @pytest.mark.larl_exclude
    def test_cut_in_disjunction(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            test(X, a) :- X > 0, !.
            test(X, b).
        """)

        # When X > 0, cut prevents second clause
        results = list(prolog.query("test(5, Y)"))
        assert len(results) == 1
        assert results[0]['Y'] == 'a'

        # When X <= 0, second clause is tried
        results = list(prolog.query("test(-1, Y)"))
        # Should get both results (first fails, second succeeds)
        assert len(results) >= 1
        assert results[-1]['Y'] == 'b'


class TestBacktrackingWithMember:
    """Backtracking with member/2"""

    def test_member_generates_choices(self):
        prolog = PrologInterpreter()

        # member should backtrack through all elements
        results = list(prolog.query("member(X, [1, 2, 3])"))
        assert len(results) == 3
        members = {r['X'] for r in results}
        assert members == {1, 2, 3}

    def test_member_in_conjunction(self):
        prolog = PrologInterpreter()

        # Find pairs from two lists
        results = list(prolog.query("member(X, [a, b]), member(Y, [1, 2])"))
        assert len(results) == 4

        pairs = {(r['X'], r['Y']) for r in results}
        expected = {('a', 1), ('a', 2), ('b', 1), ('b', 2)}
        assert pairs == expected


class TestBacktrackingWithAppend:
    """Backtracking with append/3"""

    def test_append_multiple_solutions(self):
        prolog = PrologInterpreter()

        # append can generate multiple ways to split a list
        results = list(prolog.query("append(X, Y, [1, 2, 3])"))
        assert len(results) >= 3

        # Check some expected splits
        splits = {(tuple(r['X']), tuple(r['Y'])) for r in results}
        assert ((), (1, 2, 3)) in splits
        assert ((1,), (2, 3)) in splits
        assert ((1, 2), (3,)) in splits
        assert ((1, 2, 3), ()) in splits


class TestBacktrackingWithFindall:
    """Findall collects all backtracking solutions"""

    def test_findall_collects_all(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            p(1).
            p(2).
            p(3).
        """)

        result = prolog.query_once("findall(X, p(X), L)")
        assert result is not None
        assert result['L'] == [1, 2, 3]

    def test_findall_with_condition(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            num(1).
            num(2).
            num(3).
            num(4).
            num(5).
        """)

        # Collect even numbers
        result = prolog.query_once("findall(X, (num(X), 0 is X mod 2), Evens)")
        assert result is not None
        assert set(result['Evens']) == {2, 4}


class TestBacktrackingWithNegation:
    """Backtracking with negation as failure"""

    def test_negation_no_backtracking(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            p(1).
            p(2).
            q(2).
        """)

        # \\+ (not provable) doesn't generate choice points
        results = list(prolog.query("p(X), \\+(q(X))"))
        assert len(results) == 1
        assert results[0]['X'] == 1


class TestComplexBacktrackingPatterns:
    """Complex backtracking scenarios"""

    def test_permutation_generation(self):
        prolog = PrologInterpreter()

        # Generate all ways to select 2 different elements
        query = """
            member(X, [a, b, c]),
            member(Y, [a, b, c]),
            X \\= Y
        """
        results = list(prolog.query(query))

        # Should have 6 results (3 * 2)
        assert len(results) == 6

        pairs = {(r['X'], r['Y']) for r in results}
        # All different pairs
        for x, y in pairs:
            assert x != y

    def test_three_way_join(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            likes(alice, pizza).
            likes(bob, burger).
            likes(charlie, pizza).

            serves(restaurant_a, pizza).
            serves(restaurant_b, burger).
            serves(restaurant_b, pizza).

            location(restaurant_a, downtown).
            location(restaurant_b, uptown).
        """)

        # Find person-restaurant-location combinations
        query = """
            likes(Person, Food),
            serves(Restaurant, Food),
            location(Restaurant, Location)
        """
        results = list(prolog.query(query))

        # alice likes pizza: restaurant_a (downtown), restaurant_b (uptown)
        # bob likes burger: restaurant_b (uptown)
        # charlie likes pizza: restaurant_a (downtown), restaurant_b (uptown)
        assert len(results) == 5

    def test_backtracking_with_arithmetic(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            num(1).
            num(2).
            num(3).
            num(4).
        """)

        # Find pairs where sum equals 5
        results = list(prolog.query("num(X), num(Y), 5 is X + Y"))
        assert len(results) == 4

        pairs = {(r['X'], r['Y']) for r in results}
        expected = {(1, 4), (2, 3), (3, 2), (4, 1)}
        assert pairs == expected
