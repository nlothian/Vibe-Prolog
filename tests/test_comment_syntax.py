"""Tests for block comment syntax and edge cases."""

import pytest
from vibeprolog.parser import PrologParser
from vibeprolog.exceptions import PrologThrow


class TestBlockCommentSyntax:
    """Tests for block comment parsing and syntax errors."""

    def test_properly_terminated_block_comments(self):
        """Test that properly terminated block comments parse correctly."""
        parser = PrologParser()
        code = """
            /* single line comment */
            fact1.
            /*
             * Multi-line
             * block comment
             */
            fact2.
        """
        clauses = parser.parse(code)
        assert len(clauses) == 2
        assert clauses[0].head.name == "fact1"
        assert clauses[1].head.name == "fact2"

    def test_nested_block_comments(self):
        """Test that nested block comments are handled correctly."""
        parser = PrologParser()
        code = """
            /* outer /* nested */ comment */
            fact.
        """
        clauses = parser.parse(code)
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"

    def test_deeply_nested_block_comments(self):
        """Test deeply nested block comments."""
        parser = PrologParser()
        code = """
            /* /* /* deep */ nested */ comment */
            fact.
        """
        clauses = parser.parse(code)
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"

    def test_block_comment_at_end_of_file(self):
        """Test block comment at end of file."""
        parser = PrologParser()
        code = "fact. /* comment at end */"
        clauses = parser.parse(code)
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"

    def test_block_comment_between_clauses(self):
        """Test block comments between clauses."""
        parser = PrologParser()
        code = """
            fact1.
            /* comment between clauses */
            fact2.
        """
        clauses = parser.parse(code)
        assert len(clauses) == 2
        assert clauses[0].head.name == "fact1"
        assert clauses[1].head.name == "fact2"

    def test_block_comment_adjacent_to_tokens(self):
        """Test block comments adjacent to tokens."""
        parser = PrologParser()
        code = "parent/*comment*/(john, mary)."
        clauses = parser.parse(code)
        assert len(clauses) == 1
        assert clauses[0].head.functor == "parent"

    def test_javadoc_style_comments(self):
        """Test /** javadoc style comments */."""
        parser = PrologParser()
        code = """
            /** javadoc comment */
            fact.
        """
        clauses = parser.parse(code)
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"

    def test_unterminated_block_comment_raises_error(self):
        """Test that unterminated block comments raise syntax_error."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="Unterminated block comment"):
            parser.parse("/* unterminated fact.")

    def test_unterminated_nested_comment_raises_error(self):
        """Test unterminated nested block comment."""
        parser = PrologParser()
        with pytest.raises(PrologThrow, match="Unterminated block comment"):
            parser.parse("/* outer /* nested unterminated fact.")

    def test_comment_content_ignored(self):
        """Test that content inside comments doesn't affect parsing."""
        parser = PrologParser()
        code = """
            /* This contains Prolog-like syntax: fact(arg). :- rule. */
            actual_fact.
        """
        clauses = parser.parse(code)
        assert len(clauses) == 1
        assert clauses[0].head.name == "actual_fact"

    @pytest.mark.slow
    def test_crypto_library_loads(self):
        """Test that library/crypto.pl comments parse without syntax errors."""
        parser = PrologParser()
        with open("library/crypto.pl", "r") as f:
            content = f.read()
        # Should not raise an exception
        clauses = parser.parse(content)
        assert len(clauses) > 0  # Should have parsed some clauses

    @pytest.mark.larl_exclude
    def test_uuid_library_loads(self):
        """Test that library/uuid.pl loads without comment syntax errors."""
        parser = PrologParser()
        with open("library/uuid.pl", "r") as f:
            content = f.read()
        # Should not raise an exception
        clauses = parser.parse(content)
        assert len(clauses) > 0  # Should have parsed some clauses

    def test_block_comment_with_stars(self):
        """Test block comments with decorative stars."""
        parser = PrologParser()
        code = """
            /* - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
               Decorative comment
               - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - */
            fact.
        """
        clauses = parser.parse(code)
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"

    def test_empty_block_comment(self):
        """Test empty block comments."""
        parser = PrologParser()
        code = "/* */ fact."
        clauses = parser.parse(code)
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"

    def test_block_comment_with_newlines_and_spaces(self):
        """Test block comments with various whitespace."""
        parser = PrologParser()
        code = """
            /*
             * Comment with
             *   indented lines
             */
            fact.
        """
        clauses = parser.parse(code)
        assert len(clauses) == 1
        assert clauses[0].head.name == "fact"
