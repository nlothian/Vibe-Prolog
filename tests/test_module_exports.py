"""Tests for module export handling, including control constructs and invalid predicate indicators."""

import pytest
from vibeprolog.interpreter import PrologInterpreter


class TestModuleExports:
    """Tests for module/2 export list handling."""

    def test_valid_exports_standard_predicates(self):
        """Test that standard predicate exports work correctly."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [foo/1, bar/2]).
        foo(X) :- X = 1.
        bar(X, Y) :- X = Y.
        """
        prolog.consult_string(code)
        assert ("foo", 1) in prolog.modules["test_mod"].exports
        assert ("bar", 2) in prolog.modules["test_mod"].exports
        assert len(prolog.modules["test_mod"].exports) == 2

    def test_valid_exports_dcg_predicates(self):
        """Test that DCG predicate exports (//) work correctly."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [sentence//1]).
        sentence([]) --> [].
        """
        prolog.consult_string(code)
        # DCG predicates get expanded to +2 arity
        assert ("sentence", 3) in prolog.modules["test_mod"].exports

    @pytest.mark.larl_exclude
    def test_invalid_exports_control_constructs_skipped(self):
        """Test that control constructs in export lists are skipped with warning."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [foo/1, !/0, bar/2]).
        foo(X) :- X = 1.
        bar(X, Y) :- X = Y.
        """
        with pytest.warns(SyntaxWarning, match="Skipping invalid predicate indicator"):
            prolog.consult_string(code)
        assert ("foo", 1) in prolog.modules["test_mod"].exports
        assert ("bar", 2) in prolog.modules["test_mod"].exports
        assert ("!", 0) not in prolog.modules["test_mod"].exports
        assert len(prolog.modules["test_mod"].exports) == 2

    def test_invalid_exports_other_control_constructs(self):
        """Test that other control constructs are skipped."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [(,)/2, (;)/2, (->)/2, foo/1]).
        foo(X) :- X = 1.
        """
        with pytest.warns(SyntaxWarning):
            prolog.consult_string(code)
        assert ("foo", 1) in prolog.modules["test_mod"].exports
        assert (",", 2) not in prolog.modules["test_mod"].exports
        assert (";", 2) not in prolog.modules["test_mod"].exports
        assert ("->", 2) not in prolog.modules["test_mod"].exports

    def test_invalid_exports_malformed_indicators(self):
        """Test that malformed predicate indicators are skipped."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [foo/1, invalid, bar/2]).
        foo(X) :- X = 1.
        bar(X, Y) :- X = Y.
        """
        with pytest.warns(SyntaxWarning, match="Skipping invalid predicate indicator"):
            prolog.consult_string(code)
        assert ("foo", 1) in prolog.modules["test_mod"].exports
        assert ("bar", 2) in prolog.modules["test_mod"].exports
        assert len(prolog.modules["test_mod"].exports) == 2

    def test_invalid_exports_non_atom_names(self):
        """Test that non-atom predicate names are skipped."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [foo/1, 123/0, bar/2]).
        foo(X) :- X = 1.
        bar(X, Y) :- X = Y.
        """
        with pytest.warns(SyntaxWarning, match="Skipping invalid predicate indicator"):
            prolog.consult_string(code)
        assert ("foo", 1) in prolog.modules["test_mod"].exports
        assert ("bar", 2) in prolog.modules["test_mod"].exports
        assert len(prolog.modules["test_mod"].exports) == 2

    def test_invalid_exports_negative_arity(self):
        """Test that negative arity indicators are skipped."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [foo/1, bar/-1, baz/2]).
        foo(X) :- X = 1.
        baz(X, Y) :- X = Y.
        """
        with pytest.warns(SyntaxWarning, match="Skipping invalid predicate indicator"):
            prolog.consult_string(code)
        assert ("foo", 1) in prolog.modules["test_mod"].exports
        assert ("baz", 2) in prolog.modules["test_mod"].exports
        assert len(prolog.modules["test_mod"].exports) == 2

    @pytest.mark.larl_exclude
    def test_mixed_valid_invalid_exports(self):
        """Test module with mix of valid and invalid exports."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [foo/1, !/0, bar/2, invalid, baz/3]).
        foo(X) :- X = 1.
        bar(X, Y) :- X = Y.
        baz(X, Y, Z) :- X = Y, Y = Z.
        """
        with pytest.warns(SyntaxWarning):
            prolog.consult_string(code)
        assert ("foo", 1) in prolog.modules["test_mod"].exports
        assert ("bar", 2) in prolog.modules["test_mod"].exports
        assert ("baz", 3) in prolog.modules["test_mod"].exports
        assert len(prolog.modules["test_mod"].exports) == 3

    def test_empty_export_list(self):
        """Test module with empty export list."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, []).
        foo(X) :- X = 1.
        """
        prolog.consult_string(code)
        assert len(prolog.modules["test_mod"].exports) == 0

    @pytest.mark.slow
    def test_library_builtins_loads_successfully(self):
        """Test that library/builtins.pl loads successfully despite control constructs in exports."""
        prolog = PrologInterpreter()
        # This should not raise an exception
        prolog.consult("library/builtins.pl")
        assert "builtins" in prolog.modules
        # Check that valid exports are present
        exports = prolog.modules["builtins"].exports
        assert ("true", 0) in exports
        assert ("false", 0) in exports
        assert ("=", 2) in exports
        # Control constructs should not be exported
        assert ("!", 0) not in exports
        assert (",", 2) not in exports

    def test_operator_exports(self):
        """Test that operator exports work."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [op(500, xfx, my_op), foo/1]).
        :- op(500, xfx, my_op).
        foo(X) :- X = 1.
        """
        prolog.consult_string(code)
        assert ("foo", 1) in prolog.modules["test_mod"].exports
        assert (500, "xfx", "my_op") in prolog.modules["test_mod"].exported_operators
