"""
Comprehensive tests to cover gaps in test coverage.

This file targets specific code paths that are not covered by existing tests,
focusing on failure cases and edge cases for built-in predicates.
"""
import pytest
from vibeprolog import PrologInterpreter


class TestArithmeticFailures:
    """Test failure cases for arithmetic predicates."""

    def test_is_with_invalid_expression(self):
        """Test is/2 with an invalid expression that should fail."""
        prolog = PrologInterpreter()
        # Test with an atom that can't be evaluated
        assert not prolog.has_solution("X is foo")

    def test_is_with_unbound_variables(self):
        """Test is/2 with unbound variables in expression."""
        prolog = PrologInterpreter()
        # Y is unbound, so evaluation should fail
        assert not prolog.has_solution("X is Y + 1")


class TestIOPredicates:
    """Test I/O predicates for coverage."""

    def test_write_basic(self):
        """Test write/1 predicate."""
        prolog = PrologInterpreter()
        # write/1 should succeed and return the substitution
        assert prolog.has_solution("write(hello)")

    def test_write_with_variable(self):
        """Test write/1 with a variable."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 42, write(X)")
        assert result is not None

    def test_writeln_basic(self):
        """Test writeln/1 predicate."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("writeln(hello)")

    def test_writeln_with_variable(self):
        """Test writeln/1 with a variable."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 42, writeln(X)")
        assert result is not None

    def test_nl_predicate(self):
        """Test nl/0 predicate."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("nl")

    def test_nl_in_sequence(self):
        """Test nl/0 in a sequence of predicates."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("write(hello), nl, write(world)")


class TestTruePredicate:
    """Test the true/0 predicate."""

    def test_true_always_succeeds(self):
        """Test that true/0 always succeeds."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("true")

    def test_true_in_conjunction(self):
        """Test true/0 in conjunction."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("true, X = 5")
        result = prolog.query_once("true, X = 5")
        assert result is not None
        assert result['X'] == 5

    def test_true_in_disjunction(self):
        """Test true/0 in disjunction."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("true ; fail")


class TestFormatThreeArgs:
    """Test format/3 predicate (string formatting to atom)."""

    def test_format_to_atom_basic(self):
        """Test format/3 with basic formatting."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format(atom(X), 'Hello ~w', [world])")
        assert result is not None
        # The result should be an atom containing 'Hello world'

    def test_format_to_atom_with_integer(self):
        """Test format/3 with integer formatting."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format(atom(X), 'Number: ~d', [42])")
        assert result is not None

    def test_format_to_atom_with_float(self):
        """Test format/3 with float formatting."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format(atom(X), 'Float: ~f', [3.14])")
        assert result is not None

    def test_format_to_atom_with_newline(self):
        """Test format/3 with newline."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format(atom(X), 'Line1~nLine2', [])")
        assert result is not None

    def test_format_to_atom_with_tilde_escape(self):
        """Test format/3 with escaped tilde."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format(atom(X), 'Tilde: ~~', [])")
        assert result is not None


class TestUnivFailures:
    """Test =../2 (univ) failure cases."""

    def test_univ_with_mismatched_list(self):
        """Test =../2 when list doesn't match term structure."""
        prolog = PrologInterpreter()
        # foo(a, b) should not unify with [bar, a, b]
        assert not prolog.has_solution("foo(a, b) =.. [bar, a, b]")

    def test_univ_with_wrong_arity(self):
        """Test =../2 with wrong arity."""
        prolog = PrologInterpreter()
        # foo(a) should not unify with [foo, a, b]
        assert not prolog.has_solution("foo(a) =.. [foo, a, b]")


class TestFindallEdgeCases:
    """Test findall/3 edge cases."""

    def test_findall_no_solutions(self):
        """Test findall/3 when goal has no solutions."""
        prolog = PrologInterpreter()
        result = prolog.query_once("findall(X, fail, L)")
        assert result is not None
        assert result is not None
        assert result['L'] == []

    def test_findall_with_complex_template(self):
        """Test findall/3 with complex template."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            person(alice, 30).
            person(bob, 25).
            person(charlie, 35).
        """)
        result = prolog.query_once("findall([Name, Age], person(Name, Age), L)")
        assert result is not None
        assert result is not None
        assert len(result['L']) == 3


class TestAssertFailures:
    """Test assert/1 edge cases."""

    def test_assert_complex_clause(self):
        """Test assert/1 with a complex clause."""
        prolog = PrologInterpreter()
        prolog.consult_string(":- dynamic(parent/2).")
        assert prolog.has_solution("assert(parent(alice, bob))")
        # Now query the asserted fact
        assert prolog.has_solution("parent(alice, bob)")

    def test_assert_multiple_facts(self):
        """Test assert/1 with multiple facts."""
        prolog = PrologInterpreter()
        prolog.consult_string(":- dynamic(parent/2).")
        # Assert multiple facts
        assert prolog.has_solution("assert(parent(alice, bob))")
        assert prolog.has_solution("assert(parent(bob, charlie))")
        # Verify both facts are asserted
        assert prolog.has_solution("parent(alice, bob)")
        assert prolog.has_solution("parent(bob, charlie)")


class TestAppendEdgeCases:
    """Test append/3 edge cases for coverage."""

    def test_append_with_variable_first_list(self):
        """Test append/3 when first list is a variable (generative mode)."""
        prolog = PrologInterpreter()
        # This should generate solutions: [], [3], [3,4], etc.
        results = prolog.query("append(X, [3, 4], [3, 4])", limit=1)
        assert len(results) > 0

    def test_append_with_tail_variable(self):
        """Test append/3 with a list that has a tail variable."""
        prolog = PrologInterpreter()
        result = prolog.query_once("append([1], [2, 3], X)")
        assert result is not None
        assert result is not None
        assert result['X'] == [1, 2, 3]


class TestLengthEdgeCases:
    """Test length/2 edge cases."""

    def test_length_generate_list(self):
        """Test length/2 in generative mode."""
        prolog = PrologInterpreter()
        # Length should generate a list of variables
        result = prolog.query_once("length(L, 3)")
        assert result is not None
        assert result is not None
        assert len(result['L']) == 3

    def test_length_with_zero(self):
        """Test length/2 with zero length."""
        prolog = PrologInterpreter()
        result = prolog.query_once("length(L, 0)")
        assert result is not None
        assert result is not None
        assert result['L'] == []


class TestRetractEdgeCases:
    """Test retract/1 edge cases."""

    def test_retract_with_variable(self):
        """Test retract/1 with a variable to enumerate facts."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic(color/1).
            color(red).
            color(blue).
            color(green).
        """)
        # Retract should match and remove one fact
        results = prolog.query("retract(color(X))", limit=1)
        assert len(results) == 1
        # One of the colors should have been removed
        assert results[0]['X'] in ['red', 'blue', 'green']

    def test_retract_nonexistent(self):
        """Test retract/1 with a fact that doesn't exist."""
        prolog = PrologInterpreter()
        # Should fail
        assert not prolog.has_solution("retract(nonexistent(foo))")


class TestMaplistEdgeCases:
    """Test maplist/2 edge cases."""

    def test_maplist_with_empty_list(self):
        """Test maplist/2 with empty list."""
        prolog = PrologInterpreter()
        # maplist should succeed on empty list
        assert prolog.has_solution("maplist(atom, [])")

    def test_maplist_with_single_element(self):
        """Test maplist/2 with single element list."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("maplist(atom, [hello])")

    def test_maplist_failure(self):
        """Test maplist/2 when goal fails for some element."""
        prolog = PrologInterpreter()
        # Should fail because 1 is not an atom
        assert not prolog.has_solution("maplist(atom, [hello, 1])")


class TestDisjunctionEdgeCases:
    """Test ;/2 (disjunction) edge cases."""

    def test_disjunction_both_succeed(self):
        """Test disjunction when both branches succeed."""
        prolog = PrologInterpreter()
        results = prolog.query("(X = 1 ; X = 2)", limit=2)
        assert len(results) == 2
        assert results[0]['X'] == 1
        assert results[1]['X'] == 2

    def test_disjunction_first_succeeds(self):
        """Test disjunction when only first branch succeeds."""
        prolog = PrologInterpreter()
        results = prolog.query("(X = 1 ; fail)", limit=2)
        assert len(results) == 1
        assert results[0]['X'] == 1

    def test_disjunction_second_succeeds(self):
        """Test disjunction when only second branch succeeds."""
        prolog = PrologInterpreter()
        results = prolog.query("(fail ; X = 2)", limit=2)
        assert len(results) == 1
        assert results[0]['X'] == 2


class TestIfThenEdgeCases:
    """Test ->/2 (if-then) edge cases."""

    def test_if_then_condition_succeeds(self):
        """Test if-then when condition succeeds."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(true -> X = yes)")
        assert result is not None
        assert result is not None
        assert result['X'] == 'yes'

    def test_if_then_condition_fails(self):
        """Test if-then when condition fails."""
        prolog = PrologInterpreter()
        # The whole if-then should fail
        assert not prolog.has_solution("(fail -> X = yes)")


class TestConjunctionEdgeCases:
    """Test ,/2 (conjunction) edge cases."""

    def test_conjunction_both_succeed(self):
        """Test conjunction when both goals succeed."""
        prolog = PrologInterpreter()
        result = prolog.query_once("(X = 1, Y = 2)")
        assert result is not None
        assert result is not None
        assert result['X'] == 1
        assert result is not None
        assert result['Y'] == 2

    def test_conjunction_first_fails(self):
        """Test conjunction when first goal fails."""
        prolog = PrologInterpreter()
        assert not prolog.has_solution("(fail, X = 1)")

    def test_conjunction_second_fails(self):
        """Test conjunction when second goal fails."""
        prolog = PrologInterpreter()
        assert not prolog.has_solution("(X = 1, fail)")


class TestBagofSetof:
    """Test bagof/3 and setof/3."""

    def test_bagof_with_solutions(self):
        """Test bagof/3 when goal has solutions."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            likes(mary, food).
            likes(mary, wine).
            likes(john, wine).
            likes(john, mary).
        """)
        result = prolog.query_once("bagof(X, likes(mary, X), L)")
        assert result is not None
        assert result is not None
        assert len(result['L']) == 2

    def test_bagof_no_solutions(self):
        """Test bagof/3 when goal has no solutions (should fail)."""
        prolog = PrologInterpreter()
        # bagof fails when there are no solutions (unlike findall)
        assert not prolog.has_solution("bagof(X, fail, L)")

    def test_setof_with_duplicates(self):
        """Test setof/3 removes duplicates and sorts."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            num(3).
            num(1).
            num(2).
            num(1).
        """)
        result = prolog.query_once("setof(X, num(X), L)")
        assert result is not None
        # Should be sorted and unique
        assert result is not None
        assert result['L'] == [1, 2, 3]

    def test_setof_no_solutions(self):
        """Test setof/3 when goal has no solutions (should fail)."""
        prolog = PrologInterpreter()
        assert not prolog.has_solution("setof(X, fail, L)")


class TestSortAndReverse:
    """Test sort/2 and reverse/2."""

    def test_sort_with_duplicates(self):
        """Test sort/2 removes duplicates."""
        prolog = PrologInterpreter()
        result = prolog.query_once("sort([3, 1, 2, 1, 3], L)")
        assert result is not None
        assert result is not None
        assert result['L'] == [1, 2, 3]

    def test_sort_empty_list(self):
        """Test sort/2 with empty list."""
        prolog = PrologInterpreter()
        result = prolog.query_once("sort([], L)")
        assert result is not None
        assert result is not None
        assert result['L'] == []

    def test_reverse_empty_list(self):
        """Test reverse/2 with empty list."""
        prolog = PrologInterpreter()
        result = prolog.query_once("reverse([], L)")
        assert result is not None
        assert result is not None
        assert result['L'] == []

    def test_reverse_single_element(self):
        """Test reverse/2 with single element."""
        prolog = PrologInterpreter()
        result = prolog.query_once("reverse([1], L)")
        assert result is not None
        assert result is not None
        assert result['L'] == [1]


class TestFunctorArgEdgeCases:
    """Test functor/3 and arg/3 edge cases."""

    def test_functor_with_atom(self):
        """Test functor/3 with an atom."""
        prolog = PrologInterpreter()
        result = prolog.query_once("functor(hello, F, N)")
        assert result is not None
        assert result is not None
        assert result['F'] == 'hello'
        assert result is not None
        assert result['N'] == 0

    def test_functor_construct_term(self):
        """Test functor/3 to construct a term."""
        prolog = PrologInterpreter()
        result = prolog.query_once("functor(T, foo, 2)")
        assert result is not None
        # T should be foo(_,_) with unbound variables

    def test_arg_with_invalid_index(self):
        """Test arg/3 with invalid index (should fail)."""
        prolog = PrologInterpreter()
        assert not prolog.has_solution("arg(0, foo(a, b), X)")
        assert not prolog.has_solution("arg(5, foo(a, b), X)")

    def test_arg_with_atom(self):
        """Test arg/3 with an atom (should fail)."""
        prolog = PrologInterpreter()
        assert not prolog.has_solution("arg(1, hello, X)")


class TestCallPredicate:
    """Test call/1 predicate."""

    def test_call_with_compound(self):
        """Test call/1 with a compound term."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            test_pred(42).
        """)
        result = prolog.query_once("call(test_pred(X))")
        assert result is not None
        assert result is not None
        assert result['X'] == 42

    def test_call_with_variable(self):
        """Test call/1 with a variable bound to a goal."""
        prolog = PrologInterpreter()
        result = prolog.query_once("G = (X = 5), call(G)")
        assert result is not None
        assert result is not None
        assert result['X'] == 5


class TestClausePredicate:
    """Test clause/2 predicate."""

    def test_clause_with_fact(self):
        """Test clause/2 with a fact."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            parent(tom, bob).
        """)
        result = prolog.query_once("clause(parent(tom, bob), Body)")
        assert result is not None
        # Body should be 'true' for facts

    def test_clause_with_rule(self):
        """Test clause/2 with a rule."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
        """)
        result = prolog.query_once("clause(grandparent(A, B), Body)")
        assert result is not None
        # Body should be the rule body


class TestPredicateProperty:
    """Test predicate_property/2."""

    @pytest.mark.larl_exclude
    def test_predicate_property_builtin(self):
        """Test predicate_property/2 with a built-in."""
        prolog = PrologInterpreter()
        result = prolog.query_once("predicate_property(is(_, _), built_in)")
        assert result is not None

    def test_predicate_property_user_defined(self):
        """Test predicate_property/2 with user-defined predicate."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            my_pred(x).
        """)
        # User predicates should not have built_in property
        result = prolog.query_once("predicate_property(my_pred(_), built_in)")
        # This might return None if not built-in


class TestCatchPredicate:
    """Test catch/3 predicate."""

    def test_catch_no_error(self):
        """Test catch/3 when no error occurs."""
        prolog = PrologInterpreter()
        result = prolog.query_once("catch(X = 5, _, X = error)")
        assert result is not None
        assert result is not None
        assert result['X'] == 5

    def test_catch_with_failing_goal(self):
        """Test catch/3 with a goal that fails (no error thrown)."""
        prolog = PrologInterpreter()
        # When the goal fails (no error), catch should also fail
        result = prolog.query_once("catch(fail, _, X = caught)")
        # This should fail since fail doesn't throw an error, it just fails
        assert result is None


class TestTypeChecking:
    """Test type checking predicates."""

    def test_var_with_unbound(self):
        """Test var/1 with unbound variable."""
        prolog = PrologInterpreter()
        # This is tricky - we need to check if X is unbound
        prolog.consult_string("""
            test_var(X) :- var(X).
        """)
        assert prolog.has_solution("test_var(_)")

    def test_var_with_bound(self):
        """Test var/1 with bound variable."""
        prolog = PrologInterpreter()
        assert not prolog.has_solution("X = 5, var(X)")

    def test_nonvar_with_bound(self):
        """Test nonvar/1 with bound variable."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("X = 5, nonvar(X)")

    def test_nonvar_with_unbound(self):
        """Test nonvar/1 with unbound variable."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            test_nonvar(X) :- nonvar(X).
        """)
        # X is unbound in the query, so nonvar should fail
        assert not prolog.has_solution("test_nonvar(_)")

    def test_atom_with_atom(self):
        """Test atom/1 with an atom."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("atom(hello)")

    def test_atom_with_number(self):
        """Test atom/1 with a number."""
        prolog = PrologInterpreter()
        assert not prolog.has_solution("atom(42)")

    def test_atom_with_compound(self):
        """Test atom/1 with a compound term."""
        prolog = PrologInterpreter()
        assert not prolog.has_solution("atom(foo(bar))")

    def test_number_with_number(self):
        """Test number/1 with a number."""
        prolog = PrologInterpreter()
        assert prolog.has_solution("number(42)")
        assert prolog.has_solution("number(3.14)")

    def test_number_with_atom(self):
        """Test number/1 with an atom."""
        prolog = PrologInterpreter()
        assert not prolog.has_solution("number(hello)")
