"""Tests for ignored Scryer-specific directives."""

import warnings

import pytest

from vibeprolog import PrologInterpreter


class TestIgnoredDirectives:
    """Tests for directives that are recognized but ignored with a warning."""

    def test_non_counted_backtracking_parsed(self):
        """Test that non_counted_backtracking directive is parsed without error."""
        prolog = PrologInterpreter()
        # Should not raise an error
        prolog.consult_string("""
            :- non_counted_backtracking foo/1.
            foo(1).
        """)
        # Verify the clause was still loaded
        assert prolog.has_solution("foo(1)")

    @pytest.mark.larl_exclude
    def test_meta_predicate_parsed(self):
        """Test that meta_predicate directive is parsed without error."""
        prolog = PrologInterpreter()
        # Should not raise an error
        prolog.consult_string("""
            :- meta_predicate(maplist(1, ?)).
            my_pred(a).
        """)
        # Verify the clause was still loaded
        assert prolog.has_solution("my_pred(a)")

    @pytest.mark.larl_exclude
    def test_meta_predicate_complex_args(self):
        """Test meta_predicate with multiple arguments."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- meta_predicate(foldl(3, ?, ?, ?)).
            :- meta_predicate(maplist(2, ?, ?)).
            test_pred(x).
        """)
        assert prolog.has_solution("test_pred(x)")

    def test_non_counted_backtracking_warning_emitted(self):
        """Test that a warning is emitted for non_counted_backtracking."""
        prolog = PrologInterpreter()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            prolog.consult_string(":- non_counted_backtracking bar/2.")
            assert len(w) == 1
            assert "Ignoring unsupported directive" in str(w[0].message)
            assert "non_counted_backtracking" in str(w[0].message)

    def test_meta_predicate_warning_emitted(self):
        """Test that a warning is emitted for meta_predicate."""
        prolog = PrologInterpreter()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            prolog.consult_string(":- meta_predicate(test(0)).")
            assert len(w) == 1
            assert "Ignoring unsupported directive" in str(w[0].message)
            assert "meta_predicate" in str(w[0].message)

    @pytest.mark.larl_exclude
    def test_program_continues_after_ignored_directive(self):
        """Test that program loading continues after an ignored directive."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            before(1).
            :- non_counted_backtracking some_pred/1.
            after(2).
            :- meta_predicate(another(0, ?)).
            final(3).
        """)
        assert prolog.has_solution("before(1)")
        assert prolog.has_solution("after(2)")
        assert prolog.has_solution("final(3)")

    @pytest.mark.larl_exclude
    def test_multiple_ignored_directives(self):
        """Test that multiple ignored directives work correctly."""
        prolog = PrologInterpreter()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            prolog.consult_string("""
                :- non_counted_backtracking pred1/1.
                :- non_counted_backtracking pred2/2.
                :- meta_predicate(call_it(0)).
                :- meta_predicate(apply_to(1, ?)).
                fact(ok).
            """)
            # Should have 4 warnings
            assert len(w) == 4
        assert prolog.has_solution("fact(ok)")

    def test_non_counted_backtracking_with_module_qualified(self):
        """Test non_counted_backtracking with module-qualified predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- non_counted_backtracking setup_call_cleanup/3.
            test_clause(done).
        """)
        assert prolog.has_solution("test_clause(done)")

    def test_mixed_valid_and_ignored_directives(self):
        """Test that valid directives still work alongside ignored ones."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- dynamic(dyn_pred/1).
            :- non_counted_backtracking some_pred/1.
            :- meta_predicate(my_meta(0)).
            dyn_pred(initial).
        """)
        assert prolog.has_solution("dyn_pred(initial)")
        # Verify dynamic still works
        prolog.query_once("assertz(dyn_pred(added))")
        assert prolog.has_solution("dyn_pred(added)")


class TestIgnoredDirectivesInLibraries:
    """Test that library files with ignored directives can be loaded."""

    @pytest.mark.larl_exclude
    def test_library_with_meta_predicate(self):
        """Test loading a library that uses meta_predicate."""
        prolog = PrologInterpreter()
        # Create a simple test case - just verify the directive doesn't cause errors
        # and that regular clauses after the directive are loaded properly
        prolog.consult_string("""
            :- meta_predicate(my_maplist(1, ?)).
            after_directive(ok).
        """)
        # Verify the clause after the meta_predicate directive was loaded
        assert prolog.has_solution("after_directive(ok)")
