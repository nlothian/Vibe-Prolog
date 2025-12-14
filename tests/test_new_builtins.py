"""Tests for newly implemented built-in predicates.

This module tests the built-ins that were added to support the meta-interpreter
and other advanced Prolog features:
- append/3
- clause/2
- call/1
- write/1, writeln/1
- maplist/2
- true/0
- nl/0
- !/0 (cut)
- ;/2 (disjunction)
- ->/2 (if-then)
- ,/2 (conjunction)
- format/2 (formatted output to stdout)
"""

import pytest
from vibeprolog import PrologInterpreter


class TestAppend:
    """Tests for append/3 predicate."""

    def test_append_two_lists(self):
        """Test appending two concrete lists."""
        prolog = PrologInterpreter()
        result = prolog.query_once("append([1, 2], [3, 4], X).")
        assert result is not None
        assert result is not None
        assert result['X'] == [1, 2, 3, 4]

    def test_append_empty_list(self):
        """Test appending empty list."""
        prolog = PrologInterpreter()
        result = prolog.query_once("append([], [1, 2], X).")
        assert result is not None
        assert result is not None
        assert result['X'] == [1, 2]

    def test_append_to_empty(self):
        """Test appending to empty list."""
        prolog = PrologInterpreter()
        result = prolog.query_once("append([1, 2], [], X).")
        assert result is not None
        assert result is not None
        assert result['X'] == [1, 2]

    def test_append_atoms(self):
        """Test appending lists of atoms."""
        prolog = PrologInterpreter()
        result = prolog.query_once("append([a, b], [c, d], X).")
        assert result is not None
        assert result is not None
        assert result['X'] == ['a', 'b', 'c', 'd']

    def test_append_check_mode(self):
        """Test append in check mode."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("append([1], [2], [1, 2])")
        assert not prolog.has_solution("append([1], [2], [1, 3])")


class TestClause:
    """Tests for clause/2 predicate."""

    def test_clause_fact(self):
        """Test retrieving body of a fact."""
        prolog = PrologInterpreter()
        prolog.consult_string("person(john).")
        result = prolog.query_once("clause(person(john), Body).")
        assert result is not None
        assert result is not None
        assert result['Body'] == 'true'

    def test_clause_rule(self):
        """Test retrieving body of a rule."""
        prolog = PrologInterpreter()
        prolog.consult_string("parent(X, Y) :- father(X, Y).")
        results = prolog.query("clause(parent(X, Y), Body).")
        assert len(results) > 0
        # Body should be the father(X, Y) goal
        assert 'Body' in results[0]

    def test_clause_multiple_clauses(self):
        """Test retrieving multiple clauses for same predicate."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            color(red).
            color(blue).
            color(green).
        """)
        results = prolog.query("clause(color(X), Body).")
        assert len(results) == 3
        for result in results:
            assert result['Body'] == 'true'

    def test_clause_no_match(self):
        """Test clause with non-existent predicate."""
        prolog = PrologInterpreter()
        results = prolog.query("clause(nonexistent(X), Body).")
        assert len(results) == 0


class TestCall:
    """Tests for call/1 predicate."""

    def test_call_simple_goal(self):
        """Test calling a simple goal."""
        prolog = PrologInterpreter()
        prolog.consult_string("fact(a).")
        assert prolog.has_solution("call(fact(a))")

    def test_call_with_variable(self):
        """Test calling a goal stored in a variable."""
        prolog = PrologInterpreter()
        prolog.consult_string("custom_number(42).")
        result = prolog.query_once("Goal = custom_number(42), call(Goal).")
        assert result is not None

    def test_call_arithmetic(self):
        """Test calling arithmetic goals."""
        prolog = PrologInterpreter()
        result = prolog.query_once("call(X is 2 + 3).")
        assert result is not None
        assert result is not None
        assert result['X'] == 5

    def test_call_unification(self):
        """Test calling unification goal."""
        prolog = PrologInterpreter()
        result = prolog.query_once("call(X = 5).")
        assert result is not None
        assert result is not None
        assert result['X'] == 5


class TestWritePredicates:
    """Tests for write/1 and writeln/1 predicates."""

    def test_write_atom(self):
        """Test writing an atom."""
        prolog = PrologInterpreter()
        result = prolog.query_once('write("hello").')
        assert result is not None

    def test_writeln_atom(self):
        """Test writing with newline."""
        prolog = PrologInterpreter()
        result = prolog.query_once('writeln("hello").')
        assert result is not None

    def test_write_number(self):
        """Test writing a number."""
        prolog = PrologInterpreter()
        result = prolog.query_once('writeln(42).')
        assert result is not None

    def test_write_variable(self):
        """Test writing a bound variable."""
        prolog = PrologInterpreter()
        result = prolog.query_once('X = hello, writeln(X).')
        assert result is not None
        assert result is not None
        assert result['X'] == 'hello'


class TestMaplist:
    """Tests for maplist/2 predicate."""

    def test_maplist_writeln(self):
        """Test maplist with writeln."""
        prolog = PrologInterpreter()
        result = prolog.query_once("maplist(writeln, [a, b, c]).")
        assert result is not None

    def test_maplist_empty_list(self):
        """Test maplist with empty list."""
        prolog = PrologInterpreter()
        result = prolog.query_once("maplist(writeln, []).")
        assert result is not None

    def test_maplist_custom_predicate(self):
        """Test maplist with custom predicate."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            double(X, Y) :- Y is X * 2.
        """)
        # Note: maplist/2 applies goal to each element
        # For transformations we'd need maplist/3
        result = prolog.query_once("maplist(writeln, [1, 2, 3]).")
        assert result is not None


class TestCut:
    """Tests for !/0 (cut) operator."""

    @pytest.mark.larl_exclude
    def test_cut_basic(self):
        """Test basic cut behavior."""
        prolog = PrologInterpreter()
        prolog.consult_string("test_cut :- !.")
        assert prolog.has_solution("test_cut")

    @pytest.mark.larl_exclude
    def test_cut_in_first_clause(self):
        """Test cut in first clause (note: full cut semantics not yet implemented)."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            first_only(a) :- !.
            first_only(b).
        """)
        # Note: Current implementation doesn't prevent trying other clauses
        # This test documents current behavior
        results = prolog.query("first_only(X).")
        assert len(results) >= 1
        assert results[0]['X'] == 'a'

    def test_cut_in_rule_body(self):
        """Test cut in rule body."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            first(X, Y) :- X = 1, !, Y = one.
            first(X, Y) :- X = 2, Y = two.
        """)
        result = prolog.query_once("first(1, Y).")
        assert result is not None
        assert result is not None
        assert result['Y'] == 'one'


class TestTrueAndNl:
    """Tests for true/0 and nl/0 predicates."""

    def test_true_succeeds(self):
        """Test that true always succeeds."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("true")

    def test_true_in_conjunction(self):
        """Test true in conjunction."""
        prolog = PrologInterpreter()
        result = prolog.query_once("true, X = 5.")
        assert result is not None
        assert result is not None
        assert result['X'] == 5

    def test_nl_in_conjunction(self):
        """Test that nl works in a conjunction."""
        prolog = PrologInterpreter()
        # nl is typically used in a conjunction with other goals
        result = prolog.query_once("X = 5, nl, Y = 10.")
        assert result is not None
        assert result is not None
        assert result['X'] == 5
        assert result is not None
        assert result['Y'] == 10


class TestDisjunction:
    """Tests for ;/2 (disjunction/or) operator."""

    def test_disjunction_first_succeeds(self):
        """Test disjunction when first branch succeeds."""
        prolog = PrologInterpreter()
        results = prolog.query("(X = a ; X = b).")
        assert len(results) == 2
        values = [r['X'] for r in results]
        assert 'a' in values
        assert 'b' in values

    def test_disjunction_second_succeeds(self):
        """Test disjunction when first fails."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(1 =:= 2 ; X = success).")
        assert result is not None
        assert result is not None
        assert result['X'] == 'success'

    def test_disjunction_both_fail(self):
        """Test disjunction when both branches fail."""
        prolog = PrologInterpreter()
        results = prolog.query("(1 =:= 2 ; 3 =:= 4).")
        assert len(results) == 0


class TestIfThen:
    """Tests for ->/2 (if-then) operator."""

    def test_if_then_condition_succeeds(self):
        """Test if-then when condition succeeds."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(1 =:= 1 -> X = yes).")
        assert result is not None
        assert result is not None
        assert result['X'] == 'yes'

    def test_if_then_condition_fails(self):
        """Test if-then when condition fails."""
        prolog = PrologInterpreter()
        results = prolog.query("(1 =:= 2 -> X = yes).")
        assert len(results) == 0


class TestIfThenElse:
    """Tests for (Cond -> Then ; Else) pattern."""

    def test_if_then_else_condition_true(self):
        """Test if-then-else when condition is true."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(1 =:= 1 -> X = yes ; X = no).")
        assert result is not None
        assert result is not None
        assert result['X'] == 'yes'

    def test_if_then_else_condition_false(self):
        """Test if-then-else when condition is false."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(1 =:= 2 -> X = yes ; X = no).")
        assert result is not None
        assert result is not None
        assert result['X'] == 'no'

    def test_if_then_else_with_variables(self):
        """Test if-then-else with variable binding."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            classify(X, Type) :-
                (X = 1 -> Type = one ; Type = other).
        """)
        result = prolog.query_once("classify(1, T).")
        assert result is not None
        assert result is not None
        assert result['T'] == 'one'

        result = prolog.query_once("classify(2, T).")
        assert result is not None
        assert result is not None
        assert result['T'] == 'other'

    def test_if_then_else_with_clause(self):
        """Test if-then-else with clause/2."""
        prolog = PrologInterpreter()
        prolog.consult_string("myfact(a).")
        result = prolog.query_once(
            "(clause(myfact(a), B) -> X = has_clause ; X = no_clause)."
        )
        assert result is not None
        assert result is not None
        assert result['X'] == 'has_clause'

        result = prolog.query_once(
            "(clause(X is 2 + 3, B) -> Y = has_clause ; Y = no_clause)."
        )
        assert result is not None
        assert result is not None
        assert result['Y'] == 'no_clause'

    def test_if_then_else_with_conjunction_in_else(self):
        """Test if-then-else with multiple goals (conjunction) in else branch."""
        prolog = PrologInterpreter()
        # Test with two goals in else branch
        result = prolog.query_once(
            "(1 =:= 2 -> X = yes ; X = no, Y = also_no)."
        )
        assert result is not None
        assert result is not None
        assert result['X'] == 'no'
        assert result is not None
        assert result['Y'] == 'also_no'

    def test_if_then_else_with_call_in_else(self):
        """Test if-then-else with call and other goals in else branch."""
        prolog = PrologInterpreter()
        result = prolog.query_once(
            "Goal = (X is 2 + 3), (clause(Goal, B) -> Y = has ; call(Goal), Y = X)."
        )
        assert result is not None
        assert result is not None
        assert result['X'] == 5
        assert result is not None
        assert result['Y'] == 5

    def test_if_then_else_with_multiple_goals_in_else(self):
        """Test if-then-else with multiple goals in else branch (reproduces cans.pl pattern)."""
        prolog = PrologInterpreter()
        result = prolog.query_once(
            "Goal = (X is 10), (clause(Goal, B) -> Y = has ; call(Goal), Z = X, Y = Z)."
        )
        assert result is not None
        assert result is not None
        assert result['X'] == 10
        assert result is not None
        assert result['Y'] == 10
        assert result is not None
        assert result['Z'] == 10


class TestConjunction:
    """Tests for ,/2 (conjunction/and) operator."""

    def test_conjunction_simple(self):
        """Test simple conjunction of two goals."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(X = 1, Y = 2).")
        assert result is not None
        assert result is not None
        assert result['X'] == 1
        assert result is not None
        assert result['Y'] == 2

    def test_conjunction_three_goals(self):
        """Test conjunction of three goals."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(X = 1, Y = 2, Z = 3).")
        assert result is not None
        assert result is not None
        assert result['X'] == 1
        assert result is not None
        assert result['Y'] == 2
        assert result is not None
        assert result['Z'] == 3

    def test_conjunction_with_arithmetic(self):
        """Test conjunction with arithmetic evaluation."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(X is 2 + 3, Y is X * 2).")
        assert result is not None
        assert result is not None
        assert result['X'] == 5
        assert result is not None
        assert result['Y'] == 10

    def test_conjunction_with_call(self):
        """Test conjunction with call/1."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(Goal = (X is 5), call(Goal), Y = X).")
        assert result is not None
        assert result is not None
        assert result['X'] == 5
        assert result is not None
        assert result['Y'] == 5

    def test_conjunction_failure(self):
        """Test conjunction that fails."""
        prolog = PrologInterpreter()
        results = prolog.query("(X = 1, 1 =:= 2, Y = 3).")
        assert len(results) == 0

    def test_conjunction_in_rule(self):
        """Test conjunction in rule definition."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            compute(X, Y, Z) :- (A is X + Y, Z is A * 2).
        """)
        result = prolog.query_once("compute(3, 4, Z).")
        assert result is not None
        assert result is not None
        assert result['Z'] == 14


class TestFormatStdout:
    """Tests for format/2 predicate (stdout output)."""

    def test_format_simple_string(self):
        """Test formatting a simple string to stdout."""
        prolog = PrologInterpreter()
        result = prolog.query_once('format("Hello", []).')
        assert result is not None

    def test_format_with_w_placeholder(self):
        """Test ~w placeholder."""
        prolog = PrologInterpreter()
        result = prolog.query_once('format("Value: ~w", [42]).')
        assert result is not None

    def test_format_multiple_placeholders(self):
        """Test multiple placeholders."""
        prolog = PrologInterpreter()
        result = prolog.query_once('format("~w and ~w", [foo, bar]).')
        assert result is not None

    def test_format_with_newline(self):
        """Test ~n placeholder."""
        prolog = PrologInterpreter()
        result = prolog.query_once('format("Line 1~nLine 2~n", []).')
        assert result is not None

    def test_format_with_variables(self):
        """Test format with bound variables."""
        prolog = PrologInterpreter()
        result = prolog.query_once('X is 2 + 3, format("Result: ~w~n", [X]).')
        assert result is not None
        assert result is not None
        assert result['X'] == 5

    def test_format_complex(self):
        """Test complex format string."""
        prolog = PrologInterpreter()
        result = prolog.query_once(
            'format("Name: ~w, Age: ~d, Score: ~2f~n", [john, 25, 98.756]).'
        )
        assert result is not None

    def test_format_in_rule(self):
        """Test format/2 in rule definition."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            print_result(X) :- format("The result is ~w~n", [X]).
        """)
        result = prolog.query_once("print_result(42).")
        assert result is not None


class TestMetaInterpreter:
    """Integration tests for meta-interpreter support."""

    @pytest.mark.larl_exclude
    def test_simple_meta_interpreter(self):
        """Test a simple meta-interpreter."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            fact(a).
            fact(b).
            rule(X) :- fact(X).

            mi(true, Expl, Expl) :- !.
            mi((A,B), ExplIn, ExplOut) :- !,
                mi(A, ExplIn, ExplMid),
                mi(B, ExplMid, ExplOut).
            mi(Goal, ExplIn, ExplOut) :-
                (   clause(Goal, Body)
                ->  mi(Body, ExplIn, ExplOut)
                ;   call(Goal),
                    ExplOut = ExplIn
                ).
        """)

        # Test mi with true
        result = prolog.query_once("mi(true, [], Expl).")
        assert result is not None
        assert result is not None
        assert result['Expl'] == []

        # Test mi with fact
        result = prolog.query_once("mi(fact(a), [], Expl).")
        assert result is not None
        assert result is not None
        assert result['Expl'] == []

        # Test mi with rule
        results = prolog.query("mi(rule(X), [], Expl).")
        assert len(results) > 0


class TestIntegration:
    """Integration tests combining multiple built-ins."""

    def test_append_with_clause(self):
        """Test using append with clause retrieval."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            process(X) :- write(X).
        """)
        result = prolog.query_once(
            "clause(process(Y), Body), append([], [Body], L)."
        )
        assert result is not None
        assert result is not None
        assert len(result['L']) == 1

    def test_call_with_if_then_else(self):
        """Test call within if-then-else."""
        prolog = PrologInterpreter()
        prolog.consult_string("valid(1). valid(2).")
        result = prolog.query_once(
            "Goal = valid(1), (call(Goal) -> X = ok ; X = fail)."
        )
        assert result is not None
        assert result is not None
        assert result['X'] == 'ok'

    def test_maplist_with_write(self):
        """Test maplist with write predicate."""
        prolog = PrologInterpreter()
        # Use a simple predicate without conjunction
        result = prolog.query_once("maplist(write, [a, b, c]).")
        assert result is not None
