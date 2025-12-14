"""Tests for module operator imports and pre-scanning functionality.

This test suite verifies that operators from imported modules are correctly
collected and made available to the parser before parsing the importing file.
"""

import builtins
import inspect
from pathlib import Path

import pytest

from vibeprolog import PrologInterpreter
from vibeprolog.parser import (
    extract_op_directives,
    tokenize_prolog_statements,
    _strip_comments,
)
from vibeprolog.exceptions import PrologThrow


class TestOperatorExtraction:
    """Tests for extracting operators from source code."""

    def test_extract_op_from_standalone_directive(self):
        """Test extracting operators from standalone :- op(...) directives."""
        source = """
        :- op(700, xfx, my_op).
        :- op(500, yfx, another_op).
        """
        ops = extract_op_directives(source)
        assert (700, "xfx", "my_op") in ops
        assert (500, "yfx", "another_op") in ops

    def test_extract_op_from_module_declaration(self):
        """Test extracting operators from module export lists."""
        source = """
        :- module(my_module, [
            op(600, xfx, custom_op),
            my_pred/1
        ]).
        """
        ops = extract_op_directives(source)
        assert (600, "xfx", "custom_op") in ops

    def test_extract_op_with_block_comment_before_module(self):
        """Test that block comments before module declaration are handled."""
        source = """
        /* This is a block comment */
        :- module(my_module, [
            op(700, xfx, test_op)
        ]).
        """
        ops = extract_op_directives(source)
        assert (700, "xfx", "test_op") in ops

    def test_extract_op_with_line_comment_before_directive(self):
        """Test that line comments before op directive are handled."""
        source = """
        % This is a line comment
        :- op(500, yfx, line_op).
        """
        ops = extract_op_directives(source)
        assert (500, "yfx", "line_op") in ops

    def test_extract_multiple_ops_same_line(self):
        """Test extracting multiple operators in a list."""
        source = """
        :- op(700, xfx, [op1, op2, op3]).
        """
        ops = extract_op_directives(source)
        assert (700, "xfx", "op1") in ops
        assert (700, "xfx", "op2") in ops
        assert (700, "xfx", "op3") in ops


class TestCommentStripping:
    """Tests for the comment stripping functions."""

    def test_strip_comments(self):
        """Test stripping comments."""
        text = """
        % comment
        :- op(500, yfx, test).
        """
        result = _strip_comments(text)
        assert "% comment" not in result
        assert ":- op(500, yfx, test)" in result

    def test_strip_comments_preserves_quoted(self):
        """Test that comments inside quoted strings are preserved."""
        text = """atom_with_percent('hello % world')."""
        result = _strip_comments(text)
        assert "'hello % world'" in result

    def test_strip_block_comments(self):
        """Test stripping block comments."""
        text = """
        /* block comment */
        :- op(500, yfx, test).
        """
        result = _strip_comments(text)
        assert "block comment" not in result
        assert ":- op(500, yfx, test)" in result

    def test_strip_nested_block_comments(self):
        """Test stripping nested block comments."""
        text = """
        /* outer /* inner */ still outer */
        :- op(500, yfx, test).
        """
        result = _strip_comments(text)
        assert "outer" not in result
        assert "inner" not in result
        assert ":- op(500, yfx, test)" in result


class TestTokenizer:
    """Tests for the tokenize_prolog_statements function."""

    def test_tokenize_ellipsis(self):
        """Test that ... is not split into separate tokens."""
        source = ":- module(test, [...//0])."
        chunks = tokenize_prolog_statements(source)
        assert len(chunks) == 1
        assert "...//0" in chunks[0]

    def test_tokenize_range_operator(self):
        """Test that .. range operator is handled correctly."""
        source = "X in 1..9."
        chunks = tokenize_prolog_statements(source)
        assert len(chunks) == 1
        assert "1..9" in chunks[0]

    def test_tokenize_module_with_dcg_exports(self):
        """Test tokenizing module with DCG predicate exports."""
        source = """:- module(dcgs,
          [op(1105, xfy, '|'),
           phrase/2,
           phrase//2
          ])."""
        chunks = tokenize_prolog_statements(source)
        assert len(chunks) == 1
        assert "phrase//2" in chunks[0]


class TestImportTermExtraction:
    """Tests for extracting import terms from source code."""

    def test_extract_use_module_from_code_with_comments(self):
        """Test that use_module is extracted even with comments before it."""
        prolog = PrologInterpreter()
        source = """
        % This is a test file
        % With comments at the top
        :- use_module(library(lists)).
        
        my_pred(X) :- member(X, [1,2,3]).
        """
        import_terms = prolog._extract_import_terms(source, [])
        assert len(import_terms) == 1
        # First element is the import term, second is whether operators should be imported
        assert import_terms[0][1] is True  # Full import includes operators

    def test_extract_selective_use_module(self):
        """Test that selective use_module does not import operators."""
        prolog = PrologInterpreter()
        source = """
        :- use_module(library(lists), [member/2, append/3]).
        """
        import_terms = prolog._extract_import_terms(source, [])
        assert len(import_terms) == 1
        assert import_terms[0][1] is False  # Selective import excludes operators


class TestModuleOperatorImport:
    """Tests for importing operators from modules."""

    @pytest.mark.slow
    def test_import_operators_from_clpz(self):
        """Test that operators from clpz.pl are correctly collected."""
        prolog = PrologInterpreter()
        source = ":- use_module(library(clpz))."
        source_name = "file:test#1"
        local_ops = []
        imported_ops = prolog._collect_imported_operators(source, source_name, local_ops)
        
        # Check that key clpz operators are collected
        op_names = [op[2] for op in imported_ops]
        assert "in" in op_names
        assert "ins" in op_names
        assert ".." in op_names

    def test_operators_from_module_with_block_comment(self):
        """Test that operators are collected from modules with block comments."""
        prolog = PrologInterpreter()
        source = ":- use_module(library(dcgs))."
        source_name = "file:test#1"
        local_ops = []
        imported_ops = prolog._collect_imported_operators(source, source_name, local_ops)
        
        # dcgs exports op(1105, xfy, '|')
        assert any(op[2] == "|" and op[0] == 1105 for op in imported_ops)


class TestDCGIndicators:
    """Tests for DCG predicate indicator handling in module exports."""

    def test_dcg_indicator_in_export_list(self):
        """Test that Name//Arity indicators are accepted in module exports."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
        :- module(test_dcg, [phrase//2, my_pred/1]).
        my_pred(X) :- X = 1.
        """)
        # Should not raise an error
        assert "test_dcg" in prolog.modules

    def test_dcg_arity_expansion(self):
        """Test that DCG predicates get +2 arity when exported."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
        :- module(test_dcg2, [foo//1]).
        foo(X) --> [X].
        """)
        module = prolog.modules.get("test_dcg2")
        assert module is not None
        # foo//1 should be exported as foo/3 (1 + 2 for difference lists)
        assert ("foo", 3) in module.exports


class TestOperatorUsageAfterImport:
    """Tests for using operators after they've been imported."""

    @pytest.mark.larl_exclude
    def test_use_custom_operator_after_op_directive(self):
        """Test that operators defined with op/3 can be used in subsequent clauses."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
        :- op(700, xfx, my_equals).
        my_equals(X, X).
        test_pred(X) :- X my_equals 5.
        """)
        # The parser should handle 'X my_equals 5' correctly
        assert prolog.has_solution("test_pred(5)")

    def test_custom_operator_parses_correctly(self):
        """Test that custom operators are parsed into the correct structure."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
        :- op(700, xfx, my_op).
        """)
        # The operator should be registered - check it exists in the table
        ops = list(prolog.operator_table.iter_current_ops())
        op_names = [name for name, info in ops]
        assert "my_op" in op_names

    @pytest.mark.larl_exclude
    def test_use_imported_operator_from_module(self):
        """Test that operators from use_module work in subsequent code."""
        prolog = PrologInterpreter()
        
        # First, create a module with an operator and a predicate that uses it
        prolog.consult_string("""
        :- module(test_ops, [op(600, xfx, custom_rel), custom_rel/2]).
        custom_rel(X, Y) :- X < Y.
        """)
        
        # Now import that module and use the operator
        prolog.consult_string("""
        :- use_module(test_ops).
        test_custom(X, Y) :- X custom_rel Y.
        """)
        
        # The predicate should have been parsed correctly
        results = prolog.query("test_custom(1, 2)")
        assert len(results) > 0


class TestParsingWithImportedOperators:
    """Tests for parsing code that uses imported operators."""

    @pytest.mark.slow
    def test_parse_sudoku_style_code(self):
        """Test parsing code similar to sudoku.pl that uses clpz operators."""
        prolog = PrologInterpreter()
        source = """
        :- use_module(library(clpz)).
        
        test_constraint(X) :-
            X in 1..9,
            X #> 0.
        """
        
        # Get directive ops
        local_ops = extract_op_directives(source)
        source_name = "file:test#1"
        imported_ops = prolog._collect_imported_operators(source, source_name, local_ops)
        directive_ops = imported_ops + local_ops
        
        # Try parsing each chunk
        chunks = prolog._split_clauses(source)
        for chunk in chunks:
            stripped = chunk.strip()
            if not stripped:
                continue
            # This should not raise a parse error
            items = prolog.parser.parse(
                stripped,
                "test",
                directive_ops=directive_ops,
            )
            assert len(items) > 0

    @pytest.mark.slow
    def test_parse_range_operator(self):
        """Test parsing the .. range operator from clpz."""
        prolog = PrologInterpreter()
        source = """
        :- use_module(library(clpz)).
        test_range(X) :- X in 1..100.
        """
        
        local_ops = extract_op_directives(source)
        source_name = "file:test#1"
        imported_ops = prolog._collect_imported_operators(source, source_name, local_ops)
        directive_ops = imported_ops + local_ops
        
        chunks = prolog._split_clauses(source)
        for chunk in chunks:
            stripped = chunk.strip()
            if not stripped:
                continue
            items = prolog.parser.parse(
                stripped,
                "test",
                directive_ops=directive_ops,
            )
            assert len(items) > 0


class TestCircularImports:
    """Tests for handling circular module imports."""

    @pytest.mark.slow
    def test_circular_import_detection(self):
        """Test that circular imports don't cause infinite loops in operator collection."""
        prolog = PrologInterpreter()
        
        # Module A imports B, B would import A (if it existed)
        # This tests that visited set prevents infinite recursion
        source = ":- use_module(library(clpz))."  # clpz imports other modules
        
        local_ops = extract_op_directives(source)
        source_name = "file:test#1"
        
        # This should complete without hanging
        imported_ops = prolog._collect_imported_operators(source, source_name, local_ops)
        assert isinstance(imported_ops, list)


class TestRecursiveModuleLoading:
    """Tests for recursive module operator collection."""

    @pytest.mark.slow
    def test_operators_from_transitive_imports(self):
        """Test that operators from transitively imported modules are collected."""
        prolog = PrologInterpreter()
        
        # clpz imports other modules that might define operators
        source = ":- use_module(library(clpz))."
        
        local_ops = extract_op_directives(source)
        source_name = "file:test#1"
        imported_ops = prolog._collect_imported_operators(source, source_name, local_ops)
        
        # clpz defines these directly
        assert any(op[2] == "in" for op in imported_ops)
        
        # Check that we got a reasonable number of operators
        assert len(imported_ops) > 10  # clpz and its deps define many operators


class TestOperatorCaching:
    """Tests for caching operator scans across consultations."""

    @pytest.mark.larl_exclude
    def test_reuses_cached_operator_scans_across_interpreters(self, tmp_path, monkeypatch):
        """Consulting the same nested modules twice should avoid re-scanning imports."""
        # Build a small module tree: top -> mid -> leaf (defines an operator)
        leaf = tmp_path / "leaf.pl"
        leaf.write_text(
            ":- module(leaf, [op(500, xfx, leaf_op), leaf_op/2]).\n"
            "leaf_op(X, Y) :- X = Y.\n"
        )
        mid = tmp_path / "mid.pl"
        mid.write_text(f":- module(mid, []).\n:- use_module('{leaf.as_posix()}').\n")
        top = tmp_path / "top.pl"
        top.write_text(
            f":- use_module('{mid.as_posix()}').\n"
            f":- use_module('{leaf.as_posix()}', [leaf_op/2]).\n"
            "top_ok :- leaf_op(1, 1).\n"
        )

        scan_reads: list[str] = []
        real_open = builtins.open

        def tracing_open(file, mode="r", *args, **kwargs):
            if any(frame.function == "_collect_module_operators_from_file" for frame in inspect.stack()):
                scan_reads.append(Path(file).name)
            return real_open(file, mode, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", tracing_open)

        # First interpreter populates the cache by consulting the top module.
        prolog = PrologInterpreter()
        prolog.consult(str(top))
        assert set(scan_reads) >= {mid.name, leaf.name}

        # Second interpreter should reuse cached operator metadata and avoid re-reading imports.
        scan_reads.clear()
        prolog_again = PrologInterpreter()
        prolog_again.consult(str(top))

        assert mid.name not in scan_reads
        assert leaf.name not in scan_reads


class TestIntegration:
    """Integration tests for the complete operator import workflow."""

    @pytest.mark.slow
    def test_sudoku_parsing(self):
        """Test that sudoku.pl can be parsed successfully with imported operators."""
        sudoku_path = Path("examples/not yet working/sudoku.pl")
        if not sudoku_path.exists():
            pytest.skip("sudoku.pl not found")
        
        prolog = PrologInterpreter()
        
        with open(sudoku_path, "r") as f:
            source = f.read()
        
        # Get all operators
        local_ops = extract_op_directives(source)
        source_name = f"file:{sudoku_path}#1"
        imported_ops = prolog._collect_imported_operators(source, source_name, local_ops)
        directive_ops = imported_ops + local_ops
        
        # Verify we have the 'in' operator
        assert any(op[2] == "in" for op in directive_ops)
        
        # Parse each chunk
        chunks = prolog._split_clauses(source)
        parsed_count = 0
        for chunk in chunks:
            stripped = chunk.strip()
            if not stripped:
                continue
            # All chunks should parse without error
            items = prolog.parser.parse(
                stripped,
                "test",
                directive_ops=directive_ops,
            )
            parsed_count += len(items)
        
        # Should have parsed multiple clauses
        assert parsed_count > 0
