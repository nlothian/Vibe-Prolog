"""Tests for module syntax fixes and validation."""

import pytest
from vibeprolog.interpreter import PrologInterpreter
from vibeprolog.exceptions import PrologThrow


class TestModuleSyntax:
    """Tests for corrected module syntax in library files."""

    @pytest.mark.performance
    def test_library_builtins_loads_successfully(self):
        """Test that library/builtins.pl loads successfully after removing !/0 from exports."""
        prolog = PrologInterpreter()
        prolog.builtin_conflict = "shadow"  # Allow shadowing built-ins
        prolog.consult("library/builtins.pl")
        assert "builtins" in prolog.modules
        # Verify !/0 is not exported
        assert ("!", 0) not in prolog.modules["builtins"].exports
        # Verify other exports are present
        assert ("true", 0) in prolog.modules["builtins"].exports
        assert ("=", 2) in prolog.modules["builtins"].exports

    @pytest.mark.performance
    def test_library_numerics_special_functions_loads_successfully(self):
        """Test that library/numerics/special_functions.pl loads successfully."""
        prolog = PrologInterpreter()
        prolog.builtin_conflict = "shadow"
        prolog.consult("library/numerics/special_functions.pl")
        assert "special_functions" in prolog.modules
        # Test that exported predicates can be called
        result = prolog.query_once("special_functions:test_special_functions.")
        # The test should run without error (may fail due to falsification, but should not crash)
        assert isinstance(result, dict) or result is False

    @pytest.mark.performance
    def test_library_tabling_loads_successfully(self):
        """Test that library/tabling.pl loads successfully."""
        prolog = PrologInterpreter()
        prolog.builtin_conflict = "shadow"
        prolog.consult("library/tabling.pl")
        assert "tabling" in prolog.modules
        # Test that exported predicates exist
        assert ("start_tabling", 2) in prolog.modules["tabling"].exports

    @pytest.mark.performance
    def test_library_tabling_batched_worklist_loads_successfully(self):
        """Test that library/tabling/batched_worklist.pl loads successfully."""
        prolog = PrologInterpreter()
        prolog.builtin_conflict = "shadow"
        prolog.consult("library/tabling/batched_worklist.pl")
        assert "batched_worklist" in prolog.modules

    @pytest.mark.performance
    def test_library_tabling_table_data_structure_loads_successfully(self):
        """Test that library/tabling/table_data_structure.pl loads successfully."""
        prolog = PrologInterpreter()
        prolog.builtin_conflict = "shadow"
        prolog.consult("library/tabling/table_data_structure.pl")
        assert "table_datastructure" in prolog.modules

    @pytest.mark.performance
    def test_module_qualified_calls_work(self):
        """Test that module-qualified calls work for the fixed modules."""
        prolog = PrologInterpreter()
        prolog.builtin_conflict = "shadow"
        prolog.consult("library/builtins.pl")
        # Test qualified call
        result = prolog.query_once("builtins:true.")
        assert result == {}

    @pytest.mark.larl_exclude
    def test_cut_cannot_be_exported(self):
        """Test that attempting to export cut (!/0) raises an error or is skipped."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [foo/1, !/0]).
        foo(X) :- X = 1.
        """
        # This should either warn or skip the invalid export
        with pytest.warns(SyntaxWarning):
            prolog.consult_string(code)
        assert ("!", 0) not in prolog.modules["test_mod"].exports
        assert ("foo", 1) in prolog.modules["test_mod"].exports

    def test_invalid_module_path_syntax_raises_error(self):
        """Test that invalid module path syntax raises type_error."""
        prolog = PrologInterpreter()
        code = """
        :- use_module(library(name, sub)).
        """
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(code)
        error = exc_info.value.term
        assert error.functor == "error"
        type_error = error.args[0]
        assert type_error.functor == "type_error"
        assert type_error.args[0].name == "atom"

    def test_correct_module_path_syntax_works(self):
        """Test that correct module path syntax works."""
        prolog = PrologInterpreter()
        # Create a mock submodule
        prolog.consult_string("""
        :- module('library(test/sub)', [test_pred/1]).
        test_pred(X) :- X = 42.
        """)
        # Use correct syntax
        code = """
        :- use_module('library(test/sub)').
        """
        prolog.consult_string(code)
        # Should work without error
        result = prolog.query_once("sub:test_pred(X).")
        assert result == {"X": 42}

    def test_use_module_with_correct_syntax(self):
        """Test use_module/2 with correct nested module syntax."""
        prolog = PrologInterpreter()
        # Create modules
        prolog.consult_string("""
        :- module('library(math/utils)', [add/3]).
        add(X, Y, Z) :- Z is X + Y.
        """)
        prolog.consult_string("""
        :- module(test_user, []).
        :- use_module('library(math/utils)').
        """)
        # Test that the imported predicate works
        result = prolog.query_once("test_user:add(1, 2, Z).")
        assert result == {"Z": 3}

    def test_export_lists_respected(self):
        """Test that module export lists are respected."""
        prolog = PrologInterpreter()
        code = """
        :- module(test_mod, [public/1]).
        public(X) :- X = 1.
        private(X) :- X = 2.
        """
        prolog.consult_string(code)
        # Exported predicate should be accessible
        result = prolog.query_once("test_mod:public(X).")
        assert result == {"X": 1}
        # Non-exported should not be accessible from outside
        with pytest.raises(PrologThrow):
            prolog.query_once("test_mod:private(X).")