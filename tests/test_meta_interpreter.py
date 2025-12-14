"""Tests for meta-interpreter support built-ins and features.

This module tests the built-ins and features added to support meta-interpreters:
- format/1, format/2, format/3
- catch/3
- predicate_property/2
- List unification with complex patterns
- Anonymous variables (_)
- String parsing with special characters
"""

import pytest
from vibeprolog import PrologInterpreter


class TestFormatBuiltins:
    """Tests for format/1, format/2, and format/3 predicates."""

    def test_format_1_simple_string(self, capsys):
        """Test format/1 with a simple string."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format('Hello, world!').")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "Hello, world!"

    def test_format_1_with_newline(self, capsys):
        """Test format/1 with newline escape."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format('Line 1~nLine 2~n').")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "Line 1\nLine 2\n"

    def test_format_1_with_tilde_escape(self, capsys):
        """Test format/1 with ~~ for literal tilde."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format('Tilde: ~~').")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "Tilde: ~"

    def test_format_2_with_atom(self, capsys):
        """Test format/2 with atom substitution."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format('Hello, ~w!', [world]).")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "Hello, world!"

    def test_format_2_with_number(self, capsys):
        """Test format/2 with number substitution."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format('Value: ~w', [42]).")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "Value: 42"

    def test_format_2_multiple_args(self, capsys):
        """Test format/2 with multiple arguments."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format('~w and ~w', [foo, bar]).")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "foo and bar"

    def test_format_3_to_atom(self):
        """Test format/3 for string formatting to atom."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format(atom(X), 'Hello, ~w!', [world]).")
        assert result is not None
        assert result is not None
        assert result['X'] == "Hello, world!"

    def test_format_3_complex(self):
        """Test format/3 with multiple format specifiers."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format(atom(X), 'Result: ~w = ~w', [answer, 42]).")
        assert result is not None
        assert result is not None
        assert result['X'] == "Result: answer = 42"


class TestCatchBuiltin:
    """Tests for catch/3 predicate."""

    def test_catch_successful_goal(self):
        """Test catch/3 with a goal that succeeds."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(X) :- X = 5.")
        result = prolog.query_once("catch(test(X), _, fail).")
        assert result is not None
        assert result is not None
        assert result['X'] == 5

    def test_catch_failing_goal(self):
        """Test catch/3 with a goal that fails."""
        prolog = PrologInterpreter()
        result = prolog.query_once("catch(fail, _, true).")
        assert result is None

    def test_catch_with_member(self):
        """Test catch/3 with member/2 built-in."""
        prolog = PrologInterpreter()
        result = prolog.query_once("catch(member(X, [1, 2, 3]), _, fail).")
        assert result is not None
        assert result is not None
        assert result['X'] == 1

    def test_catch_multiple_solutions(self):
        """Test catch/3 can backtrack through multiple solutions."""
        prolog = PrologInterpreter()
        results = list(prolog.query("catch(member(X, [a, b, c]), _, fail)."))
        assert len(results) == 3
        assert results[0]['X'] == 'a'
        assert results[1]['X'] == 'b'
        assert results[2]['X'] == 'c'

    def test_catch_with_clause(self):
        """Test catch/3 with clause/2 built-in."""
        prolog = PrologInterpreter()
        prolog.consult_string("fact(42).")
        result = prolog.query_once("catch(clause(fact(X), true), _, fail).")
        assert result is not None
        assert result is not None
        assert result['X'] == 42


class TestPredicateProperty:
    """Tests for predicate_property/2 predicate."""

    def test_builtin_member(self):
        """Test that member/2 is recognized as built-in."""
        prolog = PrologInterpreter()
        result = prolog.query_once("predicate_property(member(_, _), built_in).")
        assert result == {}

    def test_builtin_append(self):
        """Test that append/3 is recognized as built-in."""
        prolog = PrologInterpreter()
        result = prolog.query_once("predicate_property(append(_, _, _), built_in).")
        assert result == {}

    @pytest.mark.larl_exclude
    def test_builtin_is(self):
        """Test that is/2 is recognized as built-in."""
        prolog = PrologInterpreter()
        result = prolog.query_once("predicate_property(is(_, _), built_in).")
        assert result == {}

    def test_builtin_format(self):
        """Test that format is recognized as built-in."""
        prolog = PrologInterpreter()
        result = prolog.query_once("predicate_property(format(_, _), built_in).")
        assert result == {}

    def test_builtin_call(self):
        """Test that call/1 is recognized as built-in."""
        prolog = PrologInterpreter()
        result = prolog.query_once("predicate_property(call(_), built_in).")
        assert result == {}

    def test_builtin_clause(self):
        """Test that clause/2 is recognized as built-in."""
        prolog = PrologInterpreter()
        result = prolog.query_once("predicate_property(clause(_, _), built_in).")
        assert result == {}

    def test_builtin_arithmetic_inequality(self):
        r"""Test that =\=/2 is recognized as built-in."""
        prolog = PrologInterpreter()
        result = prolog.query_once(r"predicate_property((_ =\= _), built_in).")
        assert result == {}

    def test_non_builtin(self):
        """Test that user-defined predicates are not built-in."""
        prolog = PrologInterpreter()
        prolog.consult_string("my_pred(X) :- X = 42.")
        result = prolog.query_once("predicate_property(my_pred(_), built_in).")
        assert result is None

    def test_builtin_with_variable(self):
        """Test predicate_property with unbound property variable."""
        prolog = PrologInterpreter()
        result = prolog.query_once("predicate_property(member(_, _), X).")
        assert result is not None
        assert result is not None
        assert result['X'] == 'built_in'


class TestListUnification:
    """Tests for list unification with complex patterns."""

    def test_simple_head_tail(self):
        """Test basic [H|T] pattern matching."""
        prolog = PrologInterpreter()
        result = prolog.query_once("[a, b, c] = [H|T].")
        assert result is not None
        assert result is not None
        assert result['H'] == 'a'
        assert result is not None
        assert result['T'] == ['b', 'c']

    def test_multi_element_pattern(self):
        """Test [A, B|T] pattern matching."""
        prolog = PrologInterpreter()
        result = prolog.query_once("[a, b, c, d] = [A, B|T].")
        assert result is not None
        assert result is not None
        assert result['A'] == 'a'
        assert result is not None
        assert result['B'] == 'b'
        assert result is not None
        assert result['T'] == ['c', 'd']

    def test_three_element_pattern(self):
        """Test [A, B, C|T] pattern matching."""
        prolog = PrologInterpreter()
        result = prolog.query_once("[1, 2, 3, 4, 5] = [A, B, C|T].")
        assert result is not None
        assert result is not None
        assert result['A'] == 1
        assert result is not None
        assert result['B'] == 2
        assert result is not None
        assert result['C'] == 3
        assert result is not None
        assert result['T'] == [4, 5]

    def test_pattern_with_anonymous_vars(self):
        """Test [_, H|_] pattern matching with anonymous variables."""
        prolog = PrologInterpreter()
        result = prolog.query_once("[a, b, c] = [_, H|_].")
        assert result is not None
        assert result is not None
        assert result['H'] == 'b'

    def test_second_element_predicate(self):
        """Test extracting second element using pattern matching."""
        prolog = PrologInterpreter()
        prolog.consult_string("second([_, H|_], H).")
        result = prolog.query_once("second([a, b, c], X).")
        assert result is not None
        assert result is not None
        assert result['X'] == 'b'

    def test_third_element_predicate(self):
        """Test extracting third element using pattern matching."""
        prolog = PrologInterpreter()
        prolog.consult_string("third([_, _, H|_], H).")
        result = prolog.query_once("third([a, b, c, d], X).")
        assert result is not None
        assert result is not None
        assert result['X'] == 'c'

    def test_recursive_list_processing(self):
        """Test recursive predicate that processes all list elements."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            count_list([], 0).
            count_list([_|T], N) :-
                count_list(T, N1),
                N is N1 + 1.
        """)
        result = prolog.query_once("count_list([a, b, c, d, e], N).")
        assert result is not None
        assert result is not None
        assert result['N'] == 5

    def test_list_concatenation_pattern(self):
        """Test pattern matching with list concatenation."""
        prolog = PrologInterpreter()
        result = prolog.query_once("append([a, b], [c, d], [A, B|T]).")
        assert result is not None
        assert result is not None
        assert result['A'] == 'a'
        assert result is not None
        assert result['B'] == 'b'
        assert result is not None
        assert result['T'] == ['c', 'd']

    def test_empty_tail(self):
        """Test pattern matching where tail is empty."""
        prolog = PrologInterpreter()
        result = prolog.query_once("[a] = [H|T].")
        assert result is not None
        assert result is not None
        assert result['H'] == 'a'
        assert result is not None
        assert result['T'] == []

    def test_exact_length_match(self):
        """Test pattern matching with exact list length."""
        prolog = PrologInterpreter()
        result = prolog.query_once("[a, b, c] = [A, B, C|[]].")
        assert result is not None
        assert result is not None
        assert result['A'] == 'a'
        assert result is not None
        assert result['B'] == 'b'
        assert result is not None
        assert result['C'] == 'c'


class TestAnonymousVariables:
    """Tests for anonymous variable (_) handling."""

    def test_multiple_anonymous_vars_in_pattern(self):
        """Test that multiple _ in a pattern are independent."""
        prolog = PrologInterpreter()
        result = prolog.query_once("[a, b, c] = [_, _, X].")
        assert result is not None
        assert result is not None
        assert result['X'] == 'c'

    def test_anonymous_in_head_and_tail(self):
        """Test _ in both head and tail position."""
        prolog = PrologInterpreter()
        result = prolog.query_once("[a, b, c] = [_|_].")
        assert result == {}

    def test_anonymous_var_not_bound(self):
        """Test that _ doesn't create bindings."""
        prolog = PrologInterpreter()
        result = prolog.query_once("_ = 5.")
        # Anonymous variables don't appear in results
        assert '_' not in result

    def test_anonymous_in_compound_term(self):
        """Test anonymous variables in compound terms."""
        prolog = PrologInterpreter()
        prolog.consult_string("test(foo(_, X)) :- X = 42.")
        result = prolog.query_once("test(foo(anything, Y)).")
        assert result is not None
        assert result is not None
        assert result['Y'] == 42

    def test_multiple_anonymous_unify_differently(self):
        """Test that each _ can unify with different values."""
        prolog = PrologInterpreter()
        prolog.consult_string("different(_, _).")
        result = prolog.query_once("different(a, b).")
        assert result == {}
        result = prolog.query_once("different(1, 2).")
        assert result == {}

    def test_anonymous_in_recursive_predicate(self):
        """Test anonymous variables in recursive predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            skip_first([], []).
            skip_first([_|T], T).
        """)
        result = prolog.query_once("skip_first([a, b, c], X).")
        assert result is not None
        assert result is not None
        assert result['X'] == ['b', 'c']


class TestStringParsing:
    """Tests for string parsing with special characters."""

    def test_single_quoted_string(self):
        """Test parsing single-quoted strings."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'hello'.")
        assert result is not None
        assert result is not None
        assert result['X'] == 'hello'

    def test_double_quoted_string(self):
        """Test parsing double-quoted strings."""
        prolog = PrologInterpreter()
        result = prolog.query_once('X = "world".')
        assert result is not None
        assert result is not None
        assert result['X'] == 'world'

    def test_escaped_single_quote(self):
        """Test string with escaped single quote (doubled)."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'It''s a test'.")
        assert result is not None
        assert result is not None
        assert result['X'] == "It's a test"

    def test_multiple_escaped_quotes(self):
        """Test string with multiple escaped single quotes."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'She said, ''It''s fine'''.")
        assert result is not None
        assert result is not None
        assert result['X'] == "She said, 'It's fine'"

    def test_string_with_spaces(self):
        """Test strings containing spaces."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'hello world'.")
        assert result is not None
        assert result is not None
        assert result['X'] == 'hello world'

    def test_string_with_special_chars(self):
        """Test strings with special characters."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'test@#$%'.")
        assert result is not None
        assert result is not None
        assert result['X'] == 'test@#$%'

    def test_string_with_numbers(self):
        """Test strings containing numbers."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'abc123def'.")
        assert result is not None
        assert result is not None
        assert result['X'] == 'abc123def'

    def test_string_in_format(self):
        """Test escaped quotes in format strings."""
        prolog = PrologInterpreter()
        result = prolog.query_once("format(atom(X), 'It''s ~w!', [great]).")
        assert result is not None
        assert result is not None
        assert result['X'] == "It's great!"

    def test_string_in_compound(self):
        """Test strings with quotes in compound terms."""
        prolog = PrologInterpreter()
        prolog.consult_string("message('Don''t forget').")
        result = prolog.query_once("message(X).")
        assert result is not None
        assert result is not None
        assert result['X'] == "Don't forget"

    def test_empty_string(self):
        """Test empty strings."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = ''.")
        assert result is not None
        assert result is not None
        assert result['X'] == ''


class TestPrintPredicates:
    """Tests for write, writeln, and nl predicates used with format."""

    def test_write_atom(self, capsys):
        """Test write/1 with atom."""
        prolog = PrologInterpreter()
        result = prolog.query_once("write(hello).")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "hello"

    def test_writeln_atom(self, capsys):
        """Test writeln/1 adds newline."""
        prolog = PrologInterpreter()
        result = prolog.query_once("writeln(hello).")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "hello\n"

    def test_nl(self, capsys):
        """Test nl/0 prints newline."""
        prolog = PrologInterpreter()
        result = prolog.query_once("nl.")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "\n"

    def test_write_sequence(self, capsys):
        """Test sequence of write operations."""
        prolog = PrologInterpreter()
        result = prolog.query_once("write('A'), write('B'), write('C').")
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "ABC"

    def test_mixed_output(self, capsys):
        """Test mixing write, writeln, and format."""
        prolog = PrologInterpreter()
        result = prolog.query_once("""
            write('Start: '),
            format('~w~n', [test]),
            writeln('End').
        """)
        captured = capsys.readouterr()
        assert result == {}
        assert captured.out == "Start: test\nEnd\n"
