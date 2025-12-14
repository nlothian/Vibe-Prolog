"""
SWI-Prolog Compatibility Tests

This module tests our Prolog interpreter against expected behavior from SWI-Prolog.
It validates that we handle the same syntax and produce the same results for common
predicates and language features.

Test structure:
- Control flow tests (conjunction, disjunction, cut, negation)
- Arithmetic tests (operations, comparisons, expressions)
- List operations tests (append, member, reverse, sort, etc.)
- Term manipulation tests (functor, arg, univ, copy_term)
- Atom/String tests (atom_codes, atom_length, atom_concat, etc.)
- Type testing tests (var, atom, number, etc.)
- Comparison tests (unification, term ordering)
- Meta-predicates tests (findall, bagof, setof)
- Higher-order tests (maplist, include, exclude)
"""

import pytest
from vibeprolog import PrologInterpreter


class TestSWIControlFlow:
    """Tests for control flow constructs matching SWI-Prolog behavior."""

    def test_conjunction_simple(self):
        """
        SWI-Prolog: ?- X = 1, Y = 2.
        Expected: X = 1, Y = 2
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 1, Y = 2")
        assert result is not None
        assert result['X'] == 1
        assert result['Y'] == 2

    def test_conjunction_with_predicates(self):
        """
        SWI-Prolog: ?- atom(hello), number(42).
        Expected: true (both succeed)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("atom(hello), number(42)")
        assert result is not None

    def test_disjunction_first_succeeds(self):
        """
        SWI-Prolog: ?- X = 1; X = 2.
        Expected: X = 1 (first solution)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 1; X = 2")
        assert result is not None
        assert result['X'] == 1

    def test_disjunction_backtracking(self):
        """
        SWI-Prolog: ?- X = 1; X = 2.
        Expected: X = 1 ; X = 2 (both solutions via backtracking)
        """
        prolog = PrologInterpreter()
        results = list(prolog.query("X = 1; X = 2"))
        assert len(results) == 2
        assert results[0]['X'] == 1
        assert results[1]['X'] == 2

    def test_if_then_else_true_condition(self):
        """
        SWI-Prolog: ?- (1 < 2 -> write(yes); write(no)).
        Expected: yes (condition is true, execute then-part)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("(1 < 2 -> X = yes; X = no)")
        assert result is not None
        assert result['X'] == 'yes'

    def test_if_then_else_false_condition(self):
        """
        SWI-Prolog: ?- (1 > 2 -> write(yes); write(no)).
        Expected: no (condition is false, execute else-part)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("(1 > 2 -> X = yes; X = no)")
        assert result is not None
        assert result['X'] == 'no'

    def test_negation_as_failure_true(self):
        """
        SWI-Prolog: ?- \\+ member(5, [1,2,3]).
        Expected: true (5 is not in list)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once(r"\+ member(5, [1,2,3])")
        assert result is not None

    def test_negation_as_failure_false(self):
        """
        SWI-Prolog: ?- \\+ member(2, [1,2,3]).
        Expected: false (2 is in list)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once(r"\+ member(2, [1,2,3])")
        assert result is None

    @pytest.mark.larl_exclude
    def test_cut_prevents_backtracking(self):
        """
        SWI-Prolog: ?- member(X, [1,2,3]), !.
        Expected: X = 1 (cut prevents finding 2, 3)
        """
        prolog = PrologInterpreter()
        prolog.consult_string("test_cut(X) :- member(X, [1,2,3]), !.")
        results = list(prolog.query("test_cut(X)"))
        assert len(results) == 1
        assert results[0]['X'] == 1

    def test_cut_in_disjunction(self):
        """
        SWI-Prolog: ?- (member(X, [1,2,3]), !; X = 0).
        Expected: X = 1 (cut in first branch)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("(member(X, [1,2,3]), !; X = 0)")
        assert result is not None
        assert result['X'] == 1


class TestSWIArithmetic:
    """Tests for arithmetic operations matching SWI-Prolog behavior."""

    def test_addition(self):
        """
        SWI-Prolog: ?- X is 2 + 3.
        Expected: X = 5
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is 2 + 3")
        assert result is not None
        assert result['X'] == 5

    def test_subtraction(self):
        """
        SWI-Prolog: ?- X is 10 - 3.
        Expected: X = 7
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is 10 - 3")
        assert result is not None
        assert result['X'] == 7

    def test_multiplication(self):
        """
        SWI-Prolog: ?- X is 4 * 5.
        Expected: X = 20
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is 4 * 5")
        assert result is not None
        assert result['X'] == 20

    def test_integer_division(self):
        """
        SWI-Prolog: ?- X is 10 // 3.
        Expected: X = 3 (integer division)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is 10 // 3")
        assert result is not None
        assert result['X'] == 3

    def test_float_division(self):
        """
        SWI-Prolog: ?- X is 10 / 3.
        Expected: X = 3.333... (float division)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is 10 / 3")
        assert result is not None
        assert result['X'] == pytest.approx(10 / 3)

    def test_modulo(self):
        """
        SWI-Prolog: ?- X is 10 mod 3.
        Expected: X = 1
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is 10 mod 3")
        assert result is not None
        assert result['X'] == 1

    def test_power(self):
        """
        SWI-Prolog: ?- X is 2 ** 3.
        Expected: X = 8
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is 2 ** 3")
        assert result is not None
        assert result['X'] == 8

    def test_operator_precedence(self):
        """
        SWI-Prolog: ?- X is 2 + 3 * 4.
        Expected: X = 14 (multiplication before addition)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is 2 + 3 * 4")
        assert result is not None
        assert result['X'] == 14

    def test_unary_negation(self):
        """
        SWI-Prolog: ?- X is -(5).
        Expected: X = -5
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is -(5)")
        assert result is not None
        assert result['X'] == -5

    def test_arithmetic_comparison_less_than(self):
        """
        SWI-Prolog: ?- 3 < 5.
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("3 < 5")
        assert result is not None

    def test_arithmetic_comparison_equal(self):
        """
        SWI-Prolog: ?- 5 =:= 5.
        Expected: true (arithmetic equality)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("5 =:= 5")
        assert result is not None

    def test_arithmetic_comparison_not_equal(self):
        """
        SWI-Prolog: ?- 5 =\\= 3.
        Expected: true (arithmetic inequality)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once(r"5 =\= 3")
        assert result is not None

    def test_abs_function(self):
        """
        SWI-Prolog: ?- X is abs(-5).
        Expected: X = 5
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is abs(-5)")
        assert result is not None
        assert result['X'] == 5

    def test_min_function(self):
        """
        SWI-Prolog: ?- X is min(3, 5).
        Expected: X = 3
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is min(3, 5)")
        assert result is not None
        assert result['X'] == 3

    def test_max_function(self):
        """
        SWI-Prolog: ?- X is max(3, 5).
        Expected: X = 5
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X is max(3, 5)")
        assert result is not None
        assert result['X'] == 5


class TestSWIListOperations:
    """Tests for list predicates matching SWI-Prolog behavior."""

    def test_append_concatenate(self):
        """
        SWI-Prolog: ?- append([1,2], [3,4], X).
        Expected: X = [1, 2, 3, 4]
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("append([1,2], [3,4], X)")
        assert result is not None
        assert result['X'] == [1, 2, 3, 4]

    def test_append_decompose(self):
        """
        SWI-Prolog: ?- append(X, Y, [1,2,3]).
        Expected: Multiple solutions (X/Y pairs)
        """
        prolog = PrologInterpreter()
        results = list(prolog.query("append(X, Y, [1,2,3])"))
        assert len(results) == 4  # [], [1,2,3]; [1], [2,3]; [1,2], [3]; [1,2,3], []
        assert results[0]['X'] == []
        assert results[0]['Y'] == [1, 2, 3]

    def test_member_finding(self):
        """
        SWI-Prolog: ?- member(X, [1,2,3]).
        Expected: X = 1 ; X = 2 ; X = 3
        """
        prolog = PrologInterpreter()
        results = list(prolog.query("member(X, [1,2,3])"))
        assert len(results) == 3
        assert results[0]['X'] == 1
        assert results[1]['X'] == 2
        assert results[2]['X'] == 3

    def test_member_checking(self):
        """
        SWI-Prolog: ?- member(2, [1,2,3]).
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("member(2, [1,2,3])")
        assert result is not None

    def test_length_known_list(self):
        """
        SWI-Prolog: ?- length([a,b,c], L).
        Expected: L = 3
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("length([a,b,c], L)")
        assert result is not None
        assert result['L'] == 3

    def test_length_generate_list(self):
        """
        SWI-Prolog: ?- length(X, 3).
        Expected: X = [_,_,_] (list of 3 unbound variables)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("length(X, 3)")
        assert result is not None
        assert len(result['X']) == 3

    def test_reverse(self):
        """
        SWI-Prolog: ?- reverse([1,2,3], X).
        Expected: X = [3,2,1]
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("reverse([1,2,3], X)")
        assert result is not None
        assert result['X'] == [3, 2, 1]

    def test_sort_removes_duplicates(self):
        """
        SWI-Prolog: ?- sort([3,1,2,1], X).
        Expected: X = [1,2,3] (duplicates removed, sorted)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("sort([3,1,2,1], X)")
        assert result is not None
        assert result['X'] == [1, 2, 3]

    def test_msort_keeps_duplicates(self):
        """
        SWI-Prolog: ?- msort([3,1,2,1], X).
        Expected: X = [1,1,2,3] (duplicates kept, sorted)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("msort([3,1,2,1], X)")
        assert result is not None
        assert result['X'] == [1, 1, 2, 3]

    def test_nth0_indexing(self):
        """
        SWI-Prolog: ?- nth0(1, [a,b,c], X).
        Expected: X = b (0-indexed)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("nth0(1, [a,b,c], X)")
        assert result is not None
        assert result['X'] == 'b'

    def test_nth1_indexing(self):
        """
        SWI-Prolog: ?- nth1(1, [a,b,c], X).
        Expected: X = a (1-indexed)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("nth1(1, [a,b,c], X)")
        assert result is not None
        assert result['X'] == 'a'

    def test_last_element(self):
        """
        SWI-Prolog: ?- last([a,b,c], X).
        Expected: X = c
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("last([a,b,c], X)")
        assert result is not None
        assert result['X'] == 'c'

    def test_numlist_generation(self):
        """
        SWI-Prolog: ?- numlist(1, 3, X).
        Expected: X = [1,2,3]
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("numlist(1, 3, X)")
        assert result is not None
        assert result['X'] == [1, 2, 3]


class TestSWITermManipulation:
    """Tests for term manipulation predicates."""

    def test_unification_simple(self):
        """
        SWI-Prolog: ?- f(X, Y) = f(a, b).
        Expected: X = a, Y = b
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("f(X, Y) = f(a, b)")
        assert result is not None
        assert result['X'] == 'a'
        assert result['Y'] == 'b'

    def test_unification_fails(self):
        """
        SWI-Prolog: ?- f(a) = g(a).
        Expected: false
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("f(a) = g(a)")
        assert result is None

    def test_functor_decompose(self):
        """
        SWI-Prolog: ?- functor(foo(a,b,c), F, A).
        Expected: F = foo, A = 3
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("functor(foo(a,b,c), F, A)")
        assert result is not None
        assert result['F'] == 'foo'
        assert result['A'] == 3

    def test_functor_construct(self):
        """
        SWI-Prolog: ?- functor(X, foo, 2).
        Expected: X = foo(_,_) (compound with 2 unbound args)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("functor(X, foo, 2)")
        assert result is not None
        # Check structure: foo/2 with unbound variables
        term = result['X']
        # Term is represented as a dict with functor name as key
        assert isinstance(term, dict)
        assert 'foo' in term
        assert len(term['foo']) == 2

    def test_arg_access(self):
        """
        SWI-Prolog: ?- arg(2, foo(a,b,c), X).
        Expected: X = b (2nd argument)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("arg(2, foo(a,b,c), X)")
        assert result is not None
        assert result['X'] == 'b'

    def test_univ_decompose(self):
        """
        SWI-Prolog: ?- foo(a,b) =.. L.
        Expected: L = [foo,a,b]
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("foo(a,b) =.. L")
        assert result is not None
        assert result['L'] == ['foo', 'a', 'b']

    def test_univ_construct(self):
        """
        SWI-Prolog: ?- X =.. [foo,a,b].
        Expected: X = foo(a,b)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X =.. [foo,a,b]")
        assert result is not None
        term = result['X']
        # Term is represented as a dict with functor name as key
        assert isinstance(term, dict)
        assert 'foo' in term
        assert term['foo'] == ['a', 'b']

    def test_copy_term_basic(self):
        """
        SWI-Prolog: ?- copy_term(f(X,X), f(Y,Z)).
        Expected: Y and Z are the same variable
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("copy_term(f(X,X), f(Y,Z)), Y = Z")
        assert result is not None

    def test_copy_term_distinct(self):
        """
        SWI-Prolog: ?- copy_term(f(a,b), f(X,Y)).
        Expected: X = a, Y = b
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("copy_term(f(a,b), f(X,Y))")
        assert result is not None
        assert result['X'] == 'a'
        assert result['Y'] == 'b'

    def test_term_variables(self):
        """
        SWI-Prolog: ?- term_variables(f(X,Y,a), Vars).
        Expected: Vars = [X,Y] (list of variables)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("term_variables(f(X,Y,a), Vars)")
        assert result is not None
        assert len(result['Vars']) == 2


class TestSWITypeTests:
    """Tests for type testing predicates."""

    def test_var_unbound(self):
        """
        SWI-Prolog: ?- var(X).
        Expected: true (X is unbound)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("var(X)")
        assert result is not None

    def test_var_bound(self):
        """
        SWI-Prolog: ?- var(5).
        Expected: false (5 is bound)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("var(5)")
        assert result is None

    def test_nonvar(self):
        """
        SWI-Prolog: ?- nonvar(hello).
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("nonvar(hello)")
        assert result is not None

    def test_atom_type(self):
        """
        SWI-Prolog: ?- atom(hello).
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("atom(hello)")
        assert result is not None

    def test_atom_type_number(self):
        """
        SWI-Prolog: ?- atom(42).
        Expected: false
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("atom(42)")
        assert result is None

    def test_number_type(self):
        """
        SWI-Prolog: ?- number(42).
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("number(42)")
        assert result is not None

    def test_integer_type(self):
        """
        SWI-Prolog: ?- integer(42).
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("integer(42)")
        assert result is not None

    def test_float_type(self):
        """
        SWI-Prolog: ?- float(3.14).
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("float(3.14)")
        assert result is not None

    def test_compound_type(self):
        """
        SWI-Prolog: ?- compound(foo(a)).
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("compound(foo(a))")
        assert result is not None

    def test_atomic_type(self):
        """
        SWI-Prolog: ?- atomic(42).
        Expected: true (atoms and numbers are atomic)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("atomic(42)")
        assert result is not None

    def test_callable_type(self):
        """
        SWI-Prolog: ?- callable(foo).
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("callable(foo)")
        assert result is not None

    def test_ground_type(self):
        """
        SWI-Prolog: ?- ground(foo(a,b)).
        Expected: true (no variables)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("ground(foo(a,b))")
        assert result is not None

    def test_ground_with_variables(self):
        """
        SWI-Prolog: ?- ground(foo(a,X)).
        Expected: false (X is unbound)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("ground(foo(a,X))")
        assert result is None

    def test_is_list(self):
        """
        SWI-Prolog: ?- is_list([1,2,3]).
        Expected: true
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("is_list([1,2,3])")
        assert result is not None


class TestSWIComparison:
    """Tests for comparison predicates."""

    def test_term_equality(self):
        """
        SWI-Prolog: ?- foo(a) == foo(a).
        Expected: true (structural equality)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("foo(a) == foo(a)")
        assert result is not None

    def test_term_not_equal(self):
        """
        SWI-Prolog: ?- foo(a) \\== foo(b).
        Expected: true (structurally different)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once(r"foo(a) \== foo(b)")
        assert result is not None

    def test_term_standard_order_less(self):
        """
        SWI-Prolog: ?- a @< b.
        Expected: true (standard term order)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("a @< b")
        assert result is not None

    def test_term_standard_order_greater(self):
        """
        SWI-Prolog: ?- b @> a.
        Expected: true (standard term order)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("b @> a")
        assert result is not None

    def test_compare_predicate(self):
        """
        SWI-Prolog: ?- compare(Order, 1, 2).
        Expected: Order = '<'
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("compare(Order, 1, 2)")
        assert result is not None
        assert result['Order'] == '<'


class TestSWIAtomProcessing:
    """Tests for atom processing predicates."""

    def test_atom_length(self):
        """
        SWI-Prolog: ?- atom_length(hello, L).
        Expected: L = 5
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("atom_length(hello, L)")
        assert result is not None
        assert result['L'] == 5

    def test_atom_concat_combine(self):
        """
        SWI-Prolog: ?- atom_concat(hello, world, X).
        Expected: X = helloworld
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("atom_concat(hello, world, X)")
        assert result is not None
        assert result['X'] == 'helloworld'

    def test_atom_codes(self):
        """
        SWI-Prolog: ?- atom_codes(ab, C).
        Expected: C = [97,98] (ASCII codes)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("atom_codes(ab, C)")
        assert result is not None
        assert result['C'] == [97, 98]

    def test_atom_chars(self):
        """
        SWI-Prolog: ?- atom_chars(hello, C).
        Expected: C = [h,e,l,l,o]
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("atom_chars(hello, C)")
        assert result is not None
        assert result['C'] == ['h', 'e', 'l', 'l', 'o']

    def test_char_code(self):
        """
        SWI-Prolog: ?- char_code(a, C).
        Expected: C = 97
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("char_code(a, C)")
        assert result is not None
        assert result['C'] == 97

    def test_number_codes(self):
        """
        SWI-Prolog: ?- number_codes(123, C).
        Expected: C = [49,50,51] (ASCII '1','2','3')
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("number_codes(123, C)")
        assert result is not None
        assert result['C'] == [49, 50, 51]

    def test_number_chars(self):
        """
        SWI-Prolog: ?- number_chars(123, C).
        Expected: C = ['1','2','3']
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("number_chars(123, C)")
        assert result is not None
        assert result['C'] == ['1', '2', '3']


class TestSWIMetaPredicates:
    """Tests for meta-predicates like findall, bagof, setof."""

    def test_findall_basic(self):
        """
        SWI-Prolog: ?- findall(X, member(X, [1,2,3]), L).
        Expected: L = [1,2,3]
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("findall(X, member(X, [1,2,3]), L)")
        assert result is not None
        assert result['L'] == [1, 2, 3]

    def test_findall_no_solution(self):
        """
        SWI-Prolog: ?- findall(X, member(X, []), L).
        Expected: L = [] (empty list)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("findall(X, member(X, []), L)")
        assert result is not None
        assert result['L'] == []

    def test_findall_with_template(self):
        """
        SWI-Prolog: ?- findall(f(X), member(X, [1,2]), L).
        Expected: L = [f(1), f(2)]
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("findall(f(X), member(X, [1,2]), L)")
        assert result is not None
        assert len(result['L']) == 2

    def test_bagof_basic(self):
        """
        SWI-Prolog with facts: parent(a, b), parent(a, c), parent(d, e).
        Query: ?- bagof(Y, parent(X, Y), L).
        Expected: Multiple solutions (groups by X)
        """
        prolog = PrologInterpreter()
        prolog.consult_string("""
            parent(a, b).
            parent(a, c).
            parent(d, e).
        """)
        results = list(prolog.query("bagof(Y, parent(X, Y), L)"))
        assert len(results) == 2
        # bagof's solution order is not guaranteed, so check for both expected results.
        # Extract only X and L from the results (Y is a free variable that may be included)
        simplified_results = [{'X': r['X'], 'L': r['L']} for r in results]
        assert {'X': 'a', 'L': ['b', 'c']} in simplified_results
        assert {'X': 'd', 'L': ['e']} in simplified_results

    def test_setof_sorts_results(self):
        """
        SWI-Prolog: ?- setof(X, member(X, [3,1,2,1]), L).
        Expected: L = [1,2,3] (sorted, duplicates removed)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("setof(X, member(X, [3,1,2,1]), L)")
        assert result is not None
        assert result['L'] == [1, 2, 3]


class TestSWIHigherOrder:
    """Tests for higher-order predicates."""

    def test_maplist_2args(self):
        """
        SWI-Prolog with predicate plus(X) :- X > 0.
        Query: ?- maplist(atom, [a,b,c]).
        Expected: true (all elements are atoms)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("maplist(atom, [a,b,c])")
        assert result is not None

    def test_findall_with_between(self):
        """
        SWI-Prolog: ?- between(1, 3, X).
        Expected: X = 1 ; X = 2 ; X = 3
        """
        prolog = PrologInterpreter()
        results = list(prolog.query("between(1, 3, X)"))
        assert len(results) == 3
        assert results[0]['X'] == 1
        assert results[1]['X'] == 2
        assert results[2]['X'] == 3

    def test_succ_relation(self):
        """
        SWI-Prolog: ?- succ(3, X).
        Expected: X = 4
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("succ(3, X)")
        assert result is not None
        assert result['X'] == 4


class TestSWIPrologConsistency:
    """Tests for general Prolog consistency and semantics."""

    def test_variable_substitution(self):
        """
        SWI-Prolog: ?- X = Y, Y = 5.
        Expected: X = 5, Y = 5 (variable bindings propagate)
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("X = Y, Y = 5")
        assert result is not None
        assert result['X'] == 5
        assert result['Y'] == 5

    def test_query_failure(self):
        """
        SWI-Prolog: ?- 1 = 2.
        Expected: false
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("1 = 2")
        assert result is None

    def test_nested_compounds(self):
        """
        SWI-Prolog: ?- f(g(h(a))) = f(g(h(X))).
        Expected: X = a
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("f(g(h(a))) = f(g(h(X)))")
        assert result is not None
        assert result['X'] == 'a'

    def test_list_unification(self):
        """
        SWI-Prolog: ?- [H|T] = [1,2,3].
        Expected: H = 1, T = [2,3]
        """
        prolog = PrologInterpreter()
        result = prolog.query_once("[H|T] = [1,2,3]")
        assert result is not None
        assert result['H'] == 1
        assert result['T'] == [2, 3]

    def test_assert_retract(self):
        """
        SWI-Prolog: assertz(fact(a)), fact(X), retract(fact(a)).
        Expected: X = a, then fact(X) fails
        """
        prolog = PrologInterpreter()
        prolog.consult_string(":- dynamic(fact/1).")
        
        # Assert a fact
        prolog.query_once("assertz(fact(a))")
        
        # Query it
        result = prolog.query_once("fact(X)")
        assert result is not None
        assert result['X'] == 'a'
        
        # Retract it
        prolog.query_once("retract(fact(a))")
        
        # Now it should fail
        result = prolog.query_once("fact(X)")
        assert result is None

    def test_clause_order_matters(self):
        """
        SWI-Prolog with rules:
            first(1).
            first(2).
        Query: ?- first(X).
        Expected: X = 1 first, then X = 2 on backtracking
        """
        prolog = PrologInterpreter()
        prolog.consult_string("""
            first(1).
            first(2).
        """)
        results = list(prolog.query("first(X)"))
        assert len(results) == 2
        assert results[0]['X'] == 1
        assert results[1]['X'] == 2

    def test_rule_with_body(self):
        """
        SWI-Prolog with rule: double(X, Y) :- Y is X * 2.
        Query: ?- double(5, X).
        Expected: X = 10
        """
        prolog = PrologInterpreter()
        prolog.consult_string("double(X, Y) :- Y is X * 2.")
        result = prolog.query_once("double(5, X)")
        assert result is not None
        assert result['X'] == 10
