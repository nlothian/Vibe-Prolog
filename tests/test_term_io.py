"""Tests for term I/O built-ins (read_term/2-3, write_term/2-3, writeq/1-2, write_canonical/1-2, print/1-2)."""

import io
import sys
import pytest
from contextlib import redirect_stdout

from vibeprolog import PrologInterpreter


@pytest.fixture
def prolog() -> PrologInterpreter:
    return PrologInterpreter()


class TestReadTerm:
    """Tests for read_term/2-3 predicates."""

    def test_read_term_exists(self, prolog: PrologInterpreter):
        """Test that read_term/2 predicate exists and handles invalid options."""
        # Test with invalid options - should raise domain_error
        result = prolog.query_once("catch(read_term(test, [invalid_option]), Error, true)")
        assert result is not None
        error_term = result["Error"]
        assert "error" in error_term
        domain_error = error_term["error"][0]
        assert "domain_error" in domain_error


class TestWriteTerm:
    """Tests for write_term/2-3 predicates."""

    def test_write_term_quoted(self, prolog: PrologInterpreter):
        """Test write_term/2 with quoted option and capture stdout."""
        s = io.StringIO()
        with redirect_stdout(s):
            result = prolog.query_once("write_term('needs quotes', [quoted(true)])")
        assert result == {}
        assert s.getvalue() == "'needs quotes'"

    def test_write_term_ignore_ops(self, prolog: PrologInterpreter):
        """Test write_term/2 with ignore_ops option."""
        result, had_output = prolog.query_once("write_term(a+b*c, [ignore_ops(true)])", capture_output=True)
        assert result == {}
        assert had_output

    def test_write_term_max_depth(self, prolog: PrologInterpreter):
        """Test write_term/2 with max_depth option."""
        result, had_output = prolog.query_once("write_term(f(f(f(f(x)))), [max_depth(2)])", capture_output=True)
        assert result == {}
        assert had_output

    def test_write_term_invalid_options(self, prolog: PrologInterpreter):
        """Test write_term/2 with invalid options raises domain_error."""
        result = prolog.query_once("catch(write_term(test, [invalid_option]), Error, true)")
        assert result is not None
        error_term = result["Error"]
        assert "error" in error_term
        domain_error = error_term["error"][0]
        assert "domain_error" in domain_error


class TestWriteq:
    """Tests for writeq/1-2 predicates."""

    def test_writeq_basic(self, prolog: PrologInterpreter):
        """Test writeq/1 works."""
        result, had_output = prolog.query_once("writeq(hello)", capture_output=True)
        assert result == {}
        assert had_output

    def test_writeq_quoted_atom(self, prolog: PrologInterpreter):
        """Test writeq/1 quotes atoms when necessary."""
        result, had_output = prolog.query_once("writeq('needs quotes')", capture_output=True)
        assert result == {}
        assert had_output


class TestWriteCanonical:
    """Tests for write_canonical/1-2 predicates."""

    def test_write_canonical_basic(self, prolog: PrologInterpreter):
        """Test write_canonical/1 produces canonical output."""
        result, had_output = prolog.query_once("write_canonical(a+b*c)", capture_output=True)
        assert result == {}
        assert had_output

    def test_write_canonical_list(self, prolog: PrologInterpreter):
        """Test write_canonical/1 with lists."""
        result, had_output = prolog.query_once("write_canonical([1,2,3])", capture_output=True)
        assert result == {}
        assert had_output


class TestPrint:
    """Tests for print/1-2 predicates."""

    def test_print_basic(self, prolog: PrologInterpreter):
        """Test print/1 works (should not error)."""
        result = prolog.query_once("print(hello)")
        assert result == {}