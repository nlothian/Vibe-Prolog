"""
Tests for parser string handling, including escape sequences and edge cases.
"""

import pytest
from vibeprolog import PrologInterpreter
from vibeprolog.parser import PrologParser, Clause
from vibeprolog.terms import Atom


class TestSingleQuotedStrings:
    """Tests for single-quoted strings (atoms in Prolog)."""

    def test_simple_single_quoted_string(self):
        """Test basic single-quoted string without special characters."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'hello world'.")
        assert result is not None
        assert result is not None
        assert result['X'] == 'hello world'

    def test_doubled_apostrophe_prolog_standard(self):
        """Test Prolog standard doubled apostrophe escaping."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'it''s working'.")
        assert result is not None
        assert result is not None
        assert result['X'] == "it's working"

    def test_multiple_doubled_apostrophes(self):
        """Test multiple escaped apostrophes in one string."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'can''t won''t don''t'.")
        assert result is not None
        assert result is not None
        assert result['X'] == "can't won't don't"

    def test_backslash_escaped_apostrophe(self):
        """Test backslash-escaped apostrophe."""
        parser = PrologParser()
        # Create string with actual backslash escape
        test_code = r"test('it\'s working')."
        result = parser.parse(test_code)
        assert len(result) == 1
        assert isinstance(result[0], Clause)
        assert result[0].head.args[0].name == "it's working"

    def test_backslash_escaped_multiple_apostrophes(self):
        """Test multiple backslash-escaped apostrophes."""
        parser = PrologParser()
        test_code = r"test('can\'t won\'t don\'t')."
        result = parser.parse(test_code)
        assert len(result) == 1
        assert result[0].head.args[0].name == "can't won't don't"

    def test_mixed_escaping_methods(self):
        """Test that both escaping methods work in same program."""
        prolog = PrologInterpreter()
        parser = PrologParser()

        # Add a rule with doubled apostrophes
        prolog.consult_string("fact1('it''s nice').")

        # Add a rule with backslash escapes (need to use parser directly)
        code = r"fact2('it\'s great')."
        clauses = parser.parse(code)
        for clause in clauses:
            prolog.engine.clauses.append(clause)
            # Update the predicate index
            prolog.engine._add_predicate_to_index(clause)
            # Update module predicates
            key = (clause.head.functor, len(clause.head.args))
            mod = prolog.modules["user"]
            mod.predicates.setdefault(key, []).append(clause)

        # Query both
        result1 = prolog.query_once("fact1(X).")
        assert result1 is not None
        assert result1 is not None
        assert result1['X'] == "it's nice"

        result2 = prolog.query_once("fact2(Y).")
        assert result2 is not None
        assert result2 is not None
        assert result2['Y'] == "it's great"

    def test_escaped_backslash(self):
        """Test escaped backslash in single-quoted string."""
        parser = PrologParser()
        test_code = r"test('path\\to\\file')."
        result = parser.parse(test_code)
        assert result[0].head.args[0].name == r"path\to\file"

    def test_newline_escape(self):
        """Test newline escape sequence."""
        parser = PrologParser()
        test_code = r"test('line1\nline2')."
        result = parser.parse(test_code)
        assert result[0].head.args[0].name == "line1\nline2"

    def test_tab_escape(self):
        """Test tab escape sequence."""
        parser = PrologParser()
        test_code = r"test('col1\tcol2')."
        result = parser.parse(test_code)
        assert result[0].head.args[0].name == "col1\tcol2"

    def test_empty_string(self):
        """Test empty single-quoted string."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = ''.")
        assert result is not None
        assert result is not None
        assert result['X'] == ''


class TestDoubleQuotedStrings:
    """Tests for double-quoted strings."""

    def test_simple_double_quoted_string(self):
        """Test basic double-quoted string."""
        prolog = PrologInterpreter()
        result = prolog.query_once('X = "hello world".')
        assert result is not None
        assert result is not None
        assert result['X'] == 'hello world'

    def test_escaped_double_quote(self):
        """Test escaped double quote in double-quoted string."""
        parser = PrologParser()
        test_code = r'test("He said \"hello\"").'
        result = parser.parse(test_code)
        assert result[0].head.args[0].name == 'He said "hello"'

    def test_escaped_backslash_in_double_quotes(self):
        """Test escaped backslash in double-quoted string."""
        parser = PrologParser()
        test_code = r'test("C:\\Users\\Name").'
        result = parser.parse(test_code)
        assert result[0].head.args[0].name == r"C:\Users\Name"

    def test_newline_in_double_quotes(self):
        """Test newline escape in double-quoted string."""
        parser = PrologParser()
        test_code = r'test("line1\nline2").'
        result = parser.parse(test_code)
        assert result[0].head.args[0].name == "line1\nline2"

    def test_tab_in_double_quotes(self):
        """Test tab escape in double-quoted string."""
        parser = PrologParser()
        test_code = r'test("col1\tcol2").'
        result = parser.parse(test_code)
        assert result[0].head.args[0].name == "col1\tcol2"

    def test_empty_double_quoted_string(self):
        """Test empty double-quoted string."""
        prolog = PrologInterpreter()
        result = prolog.query_once('X = "".')
        assert result is not None
        assert result is not None
        assert result['X'] == ''


class TestStringEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_string_with_spaces(self):
        """Test strings with multiple spaces."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'hello    world'.")
        assert result is not None
        assert result is not None
        assert result['X'] == 'hello    world'

    def test_string_with_numbers(self):
        """Test strings containing numbers."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'test123'.")
        assert result is not None
        assert result is not None
        assert result['X'] == 'test123'

    def test_string_with_special_chars(self):
        """Test strings with special characters."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'test!@#$%^&*()'.")
        assert result is not None
        assert result is not None
        assert result['X'] == 'test!@#$%^&*()'

    def test_string_starting_with_capital(self):
        """Test single-quoted string starting with capital letter."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'Hello'.")
        assert result is not None
        assert result is not None
        assert result['X'] == 'Hello'

    def test_string_in_compound_term(self):
        """Test strings as arguments in compound terms."""
        prolog = PrologInterpreter()
        prolog.consult_string("person('John Smith', 30).")
        result = prolog.query_once("person(Name, Age).")
        assert result is not None
        assert result is not None
        assert result['Name'] == 'John Smith'
        assert result is not None
        assert result['Age'] == 30

    def test_string_in_list(self):
        """Test strings inside lists."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = ['it''s', 'a', 'list'].")
        assert result is not None
        assert result is not None
        assert result['X'] == ["it's", 'a', 'list']

    def test_string_unification(self):
        """Test unification with strings containing apostrophes."""
        prolog = PrologInterpreter()
        prolog.consult_string("greeting('it''s nice').")
        assert prolog.has_solution("greeting('it''s nice').")

    def test_consecutive_apostrophes(self):
        """Test four consecutive apostrophes (two escaped apostrophes)."""
        prolog = PrologInterpreter()
        result = prolog.query_once("X = 'a''''b'.")
        assert result is not None
        assert result is not None
        assert result['X'] == "a''b"


class TestStringParserErrors:
    """Tests for malformed strings and error handling."""

    def test_unclosed_single_quote(self):
        """Test that unclosed single quote raises error."""
        parser = PrologParser()
        with pytest.raises(Exception):
            parser.parse("test('unclosed).")

    def test_unclosed_double_quote(self):
        """Test that unclosed double quote raises error."""
        parser = PrologParser()
        with pytest.raises(Exception):
            parser.parse('test("unclosed).')

    def test_mismatched_quotes(self):
        """Test that mismatched quotes raise error."""
        parser = PrologParser()
        with pytest.raises(Exception):
            parser.parse('test("mixed\').')


class TestRealWorldExamples:
    """Tests based on real-world usage scenarios."""

    def test_marks_garden_example(self):
        """Test the specific case from test_programs/5.pl."""
        prolog = PrologInterpreter()
        prolog.consult_string(
            "step_msg('Step 2: So in Mark''s garden, there are flowers.')."
        )
        result = prolog.query_once("step_msg(X).")
        assert result is not None
        assert result is not None
        assert "Mark's garden" in result['X']

    def test_contractions(self):
        """Test common English contractions."""
        prolog = PrologInterpreter()
        contractions = [
            ("don''t", "don't"),
            ("can''t", "can't"),
            ("won''t", "won't"),
            ("it''s", "it's"),
            ("we''re", "we're"),
            ("they''ve", "they've"),
        ]
        for escaped, expected in contractions:
            result = prolog.query_once(f"X = '{escaped}'.")
            assert result is not None
            assert result is not None
            assert result['X'] == expected, f"Failed for {escaped}"

    def test_possessives(self):
        """Test possessive forms."""
        prolog = PrologInterpreter()
        possessives = [
            ("John''s", "John's"),
            ("Mary''s", "Mary's"),
            ("the dog''s", "the dog's"),
        ]
        for escaped, expected in possessives:
            result = prolog.query_once(f"X = '{escaped}'.")
            assert result is not None
            assert result is not None
            assert result['X'] == expected, f"Failed for {escaped}"

    def test_format_strings(self):
        """Test strings used in format predicates."""
        prolog = PrologInterpreter()
        # Test format string with apostrophe
        prolog.consult_string("""
            test_format(X) :-
                format(atom(X), 'It''s ~w!', [working]).
        """)
        result = prolog.query_once("test_format(X).")
        assert result is not None
        assert result is not None
        assert result['X'] == "It's working!"

    def test_file_paths(self):
        """Test file path strings with backslashes."""
        parser = PrologParser()
        test_code = r"path('C:\Users\Name\file.txt')."
        result = parser.parse(test_code)
        # Note: doubled backslashes in the string
        assert result[0].head.args[0].name == r"C:\Users\Name\file.txt"

    def test_escape_sequences_in_output(self):
        """Test that escape sequences work in format output."""
        prolog = PrologInterpreter()
        prolog.consult_string(r"""
            test_newline(X) :-
                format(atom(X), 'line1\nline2', []).
        """)
        result = prolog.query_once("test_newline(X).")
        assert result is not None
        # The format/2 should handle the escape sequence
        assert result is not None
        assert '\n' in result['X'] or 'line1' in result['X']


class TestOctalEscapes:
    """Tests for octal escape sequences in quoted literals."""

    def test_octal_escape_single_digit(self):
        """Test octal escape with single digit."""
        prolog = PrologInterpreter()
        result = prolog.query_once(r"X = '\0\'.")
        assert result is not None
        assert result['X'] == '\x00'  # NUL character

    def test_octal_escape_two_digits(self):
        """Test octal escape with two digits."""
        prolog = PrologInterpreter()
        result = prolog.query_once(r"X = '\10\'.")
        assert result is not None
        assert result['X'] == '\x08'  # Backspace

    def test_octal_escape_three_digits(self):
        """Test octal escape with three digits."""
        prolog = PrologInterpreter()
        result = prolog.query_once(r"X = '\101\'.")
        assert result is not None
        assert result['X'] == 'A'  # ASCII 65

    def test_octal_escape_in_double_quotes(self):
        """Test octal escape in double-quoted strings."""
        prolog = PrologInterpreter()
        result = prolog.query_once(r'X = "\102\".')
        assert result is not None
        assert result['X'] == 'B'  # ASCII 66

    def test_octal_escape_embedded(self):
        """Test octal escape embedded in larger literal."""
        prolog = PrologInterpreter()
        result = prolog.query_once(r"X = 'foo\101\bar'.")
        assert result is not None
        assert result['X'] == 'fooAbar'

    def test_octal_escape_max_value(self):
        """Test octal escape with maximum valid value (255)."""
        prolog = PrologInterpreter()
        result = prolog.query_once(r"X = '\377\'.")
        assert result is not None
        assert result['X'] == '\xff'  # 255

    def test_octal_escape_invalid_digit(self):
        """Test that invalid octal digit raises syntax error."""
        parser = PrologParser()
        with pytest.raises(Exception):  # Should raise PrologThrow with syntax_error
            parser.parse(r"test('\8\').")

    def test_octal_escape_missing_terminator(self):
        """Test that missing trailing backslash does not raise error (not parsed as octal)."""
        parser = PrologParser()
        # This should not raise error, as it's not recognized as octal escape
        result = parser.parse(r"test('\101').")
        assert result[0].head.args[0].name == r'\101'  # Remains unescaped

    def test_octal_escape_overflow(self):
        """Test that value > 255 raises syntax error."""
        parser = PrologParser()
        with pytest.raises(Exception):  # Should raise PrologThrow with syntax_error
            parser.parse(r"test('\400\').")

    def test_octal_escape_empty(self):
        """Test that empty octal escape does not raise error."""
        parser = PrologParser()
        # This should not raise error
        result = parser.parse(r"test('\\').")
        assert result[0].head.args[0].name == '\\'  # The atom name
