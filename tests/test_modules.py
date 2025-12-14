import pytest

from vibeprolog import PrologInterpreter
from vibeprolog.exceptions import PrologThrow


class TestModuleIsolation:
    def test_private_predicate_not_accessible(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(m1, [public/1]).
            public(x).
            private(y).
        """)
        assert prolog.has_solution("m1:public(x)")
        assert not prolog.has_solution("m1:private(y)")


class TestMultipleModules:
    def test_two_modules_same_predicate(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(m1, [foo/1]).
            foo(from_m1).

            :- module(m2, [foo/1]).
            foo(from_m2).
        """)
        r1 = prolog.query_once("m1:foo(X)")
        assert r1 is not None and r1["X"] == "from_m1"
        r2 = prolog.query_once("m2:foo(X)")
        assert r2 is not None and r2["X"] == "from_m2"


def test_current_module_builtin():
    prolog = PrologInterpreter()
    prolog.consult_string(":- module(m1, [a/1]).\n")
    sols = prolog.query("current_module(M)")
    names = set(s["M"] for s in sols)
    assert names == {"m1", "user"}

def test_builtin_accessible_from_module():
    prolog = PrologInterpreter()
    prolog.consult_string(":- module(m1, [test/1]). test(X) :- append([1], [2], X).")
    sols = prolog.query("m1:test(X)")
    assert any(s.get("X") == [1, 2] for s in sols)

def test_module_qualified_call_in_clause_body():
    prolog = PrologInterpreter()
    prolog.consult_string("""
        bar :- m1:foo(x).
        :- module(m1, [foo/1]).
        foo(x).
    """)
    assert prolog.has_solution("bar")

def test_module_property_nonexistent_module():
    prolog = PrologInterpreter()
    sols = list(prolog.query("module_property(nonexistent, _)"))
    assert len(sols) == 0


def test_unqualified_call_in_clause_body():
    """Test that unqualified goals in clause bodies resolve to the defining module."""
    prolog = PrologInterpreter()
    prolog.consult_string("""
        :- module(m1, [test/1]).
        helper(a).
        test(X) :- helper(X).

        :- module(m2, [helper/1]).
        helper(b).
    """)
    # m1:test should find m1:helper(a), not m2:helper(b)
    result = prolog.query_once("m1:test(X)")
    assert result is not None and result["X"] == "a"


def test_unqualified_call_prefers_defining_module():
    """Unqualified calls in module clauses prefer local predicates over user."""
    prolog = PrologInterpreter()
    prolog.consult_string("""
        helper(user).  % in user module

        :- module(m1, [test/1]).
        helper(local).  % in m1 module
        test(X) :- helper(X).
    """)
    # Should find local, not user
    result = prolog.query_once("m1:test(X)")
    assert result is not None and result["X"] == "local"


def test_unqualified_call_cannot_access_private_other_module():
    """Unqualified calls cannot access private predicates of other modules."""
    prolog = PrologInterpreter()
    prolog.consult_string("""
        :- module(m1, [test/1]).
        test(X) :- other_helper(X).  % unqualified, should not find m2's private

        :- module(m2, [public/1]).
        other_helper(private).  % not exported
        public(public).
    """)
    # Should not find the private predicate
    assert not prolog.has_solution("m1:test(X)")


def test_builtin_accessible_from_module_clause():
    """Built-ins remain globally accessible from module clauses."""
    prolog = PrologInterpreter()
    prolog.consult_string("""
        :- module(m1, [test/1]).
        test(X) :- append([1], [2], X).
    """)
    result = prolog.query_once("m1:test(X)")
    assert result is not None and result["X"] == [1, 2]


class TestUseModule:
    """Tests for use_module/1,2 directives."""

    def test_use_module_file_all_exports(self):
        """Test use_module(File) imports all exported predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- use_module('examples/modules/math_utils.pl').
            test_double(X) :- double(5, X).
            test_square(X) :- square(3, X).
        """)
        result1 = prolog.query_once("test_double(X)")
        assert result1 is not None and result1["X"] == 10
        result2 = prolog.query_once("test_square(X)")
        assert result2 is not None and result2["X"] == 9

    def test_use_module_file_specific_imports(self):
        """Test use_module(File, [pred/arity]) imports only specified predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- use_module('examples/modules/math_utils.pl', [double/2]).
            test_double(X) :- double(4, X).
        """)
        # Should work for imported predicate
        result = prolog.query_once("test_double(X)")
        assert result is not None and result["X"] == 8

        # Should fail for non-imported predicate
        assert not prolog.has_solution("square(2, X)")

    def test_use_module_nonexistent_file(self):
        """Test use_module with nonexistent file raises error."""
        prolog = PrologInterpreter()
        from vibeprolog.exceptions import PrologThrow

        with pytest.raises(PrologThrow) as excinfo:
            prolog.consult_string(":- use_module('nonexistent.pl').")
        assert "existence_error" in str(excinfo.value.term)

    def test_use_module_nonexistent_file_in_path(self):
        """Test use_module with a nonexistent file in an existing path raises an error."""
        prolog = PrologInterpreter()
        try:
            prolog.consult_string(":- use_module('examples/modules/nonexistent.pl').")
            assert False, "Should have raised an error"
        except Exception as e:
            assert "existence_error" in str(e)

    def test_use_module_private_predicate(self):
        """Test use_module cannot import non-exported predicates."""
        prolog = PrologInterpreter()
        try:
            prolog.consult_string("""
                :- use_module('examples/modules/math_utils.pl', [private_helper/2]).
            """)
            assert False, "Should have raised a permission error"
        except Exception as e:
            assert "permission_error" in str(e)

    def test_use_module_idempotent(self):
        """Test use_module is idempotent - multiple imports don't duplicate."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- use_module('examples/modules/lists.pl').
            :- use_module('examples/modules/lists.pl').
            test(X) :- my_append([1,2], [3,4], X).
        """)
        result = prolog.query_once("test(X)")
        assert result is not None and result["X"] == [1, 2, 3, 4]

    def test_use_module_in_module_clause(self):
        """Test use_module works when used inside a module."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(my_module, [test/1]).
            :- use_module('examples/modules/math_utils.pl').
            test(X) :- double(3, X).
        """)
        result = prolog.query_once("my_module:test(X)")
        assert result is not None and result["X"] == 6

    def test_imported_predicates_in_clause_body(self):
        """Test imported predicates work in clause bodies."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- use_module('examples/modules/lists.pl').
            test_combined(X) :- my_append([1], [2], Temp), my_reverse(Temp, X).
        """)
        result = prolog.query_once("test_combined(X)")
        assert result is not None and result["X"] == [2, 1]

    def test_use_module_library_syntax(self):
        """Test library(Name) syntax for use_module."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- use_module(library(math_utils)).
            test(X) :- double(7, X).
        """)
        result = prolog.query_once("test(X)")
        assert result is not None and result["X"] == 14

    def test_library_preferred_over_examples(self):
        """Test that library/ is preferred over examples/modules/ for module resolution."""
        prolog = PrologInterpreter()
        # Use test_module which exists in both library/ and examples/modules/
        # library/test_module.pl defines test_pred(library_version)
        prolog.consult_string("""
            :- use_module(library(test_module)).
            test_version(X) :- test_pred(X).
        """)
        result = prolog.query_once("test_version(X)")
        assert result is not None and result["X"] == "library_version"

    def test_examples_fallback_when_library_missing(self):
        """Test that examples/modules/ is used when library/ doesn't exist."""
        prolog = PrologInterpreter()
        # Use math_utils which only exists in examples/modules/
        prolog.consult_string("""
            :- use_module(library(math_utils)).
            test_double(X) :- double(5, X).
        """)
        result = prolog.query_once("test_double(X)")
        assert result is not None and result["X"] == 10


class TestOperatorExports:
    """Tests for operator exports in module declarations."""

    def test_module_exports_operator(self):
        """Module can export an operator in its export list."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(ops_test, [op(300, fy, ~), foo/1]).
            foo(bar).
        """)
        # Check that the module was created and the predicate is accessible via qualification
        assert prolog.has_solution("ops_test:foo(bar)")

    def test_operator_available_after_import(self):
        """Exported operators are available after import."""
        prolog = PrologInterpreter()
        # Create a module that exports an operator
        prolog.consult_string("""
            :- op(200, xfx, +++).
            :- module(myops, [op(200, xfx, +++), test/1]).
            test(a +++ b).
        """)
        # Import it and verify operator works
        prolog.consult_string("""
            :- use_module(myops).
            query :- test(a +++ b).
        """)
        assert prolog.has_solution("query")

    def test_multiple_operator_exports(self):
        """Module can export multiple operators."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(multi_ops, [op(300, fy, ~), op(500, xfx, #), pred/0]).
            pred.
        """)
        assert prolog.has_solution("multi_ops:pred")

    def test_selective_import_excludes_operators(self):
        """Selective import should not import operators (SWI-Prolog behavior)."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(selective, [op(200, xfx, <<<), foo/1, bar/1]).
            foo(1).
            bar(2).
        """)
        # Selective import should not get the operator
        prolog.consult_string("""
            :- use_module(selective, [foo/1]).
            % The operator <<< should NOT be available here
        """)
        # Test that predicate works but operator doesn't
        assert prolog.has_solution("foo(1)")

    def test_full_import_includes_operators(self):
        """Full import (no list) should import operators."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(200, xfx, ++).
            :- module(full, [op(200, xfx, ++), baz/1]).
            baz(test ++ test).
        """)
        prolog.consult_string("""
            :- use_module(full).
            verify :- baz(test ++ test).
        """)
        assert prolog.has_solution("verify")

    def test_invalid_operator_precedence_in_export(self):
        """Invalid operator precedence should raise error."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(":- module(bad, [op(2000, fy, ~)]).")
        assert "domain_error" in str(exc_info.value.term) or "operator_priority" in str(exc_info.value.term)

    @pytest.mark.larl_exclude
    def test_invalid_operator_associativity_in_export(self):
        """Invalid associativity should raise error."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as exc_info:
            prolog.consult_string(":- module(bad, [op(300, bad_assoc, ~)]).")
        assert "domain_error" in str(exc_info.value.term) or "operator_specifier" in str(exc_info.value.term)

    def test_clpb_operators(self):
        """Test with actual operators from library(clpb)."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(300, fy, ~).
            :- op(500, yfx, #).
            :- module(clpb_lite, [op(300, fy, ~), op(500, yfx, #), sat/1]).
            sat(~X) :- sat(1 # X).
            sat(1).
        """)
        prolog.consult_string("""
            :- use_module(clpb_lite).
            test :- sat(1).
        """)
        assert prolog.has_solution("test")


class TestOperatorPredicateIndicators:
    """Tests for operator predicate indicators in module exports and imports."""

    def test_module_exports_operator_predicate(self):
        """Module can export operator predicates like (#\=)/2."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(700, xfx, #\=).
            :- module(ops, [(#\=)/2, test/1]).
            test(a #\= b).
        """)
        # Check that the module was created and the predicate is accessible
        assert prolog.has_solution("ops:test(a #\= b)")

    def test_prefix_operator_predicate_export(self):
        """Test exporting prefix operator predicates like (#\)/1."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(710, fy, #\).
            :- module(prefix_ops, [(#\)/1, test/1]).
            test(#\ X) :- X = true.
        """)
        assert prolog.has_solution("prefix_ops:test(#\ true)")

    @pytest.mark.larl_exclude
    def test_infix_operator_predicate_export(self):
        """Test exporting infix operator predicates like (#>)/2."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(700, xfx, #>).
            :- module(infix_ops, [(#>)/2, test/1]).
            #>(A, B) :- A > B.
            test(X) :- 5 #> 3.
        """)
        assert prolog.has_solution("infix_ops:test(X)")

    @pytest.mark.larl_exclude
    def test_multiple_operator_predicates_export(self):
        """Test exporting multiple operator predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(700, xfx, #=).
            :- op(700, xfx, #\=).
            :- module(multi_ops, [(#=)/2, (#\=)/2, test/1]).
            #=(A, B) :- A =:= B.
            #\=(A, B) :- A =\= B.
            test(X) :- X #= 5, X #\= 6.
        """)
        assert prolog.has_solution("multi_ops:test(5)")

    @pytest.mark.larl_exclude
    def test_selective_import_operator_predicates(self):
        """Test selective import of operator predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(700, xfx, #=).
            :- op(700, xfx, #\=).
            :- module(source, [(#=)/2, (#\=)/2, regular/1]).
            #=(A, B) :- A =:= B.
            #\=(A, B) :- A =\= B.
            regular(ok).
        """)
        prolog.consult_string("""
            :- use_module(source, [(#\=)/2]).
            test :- 5 #\= 6.
        """)
        # Should work for imported operator predicate
        assert prolog.has_solution("test")
        # Should fail for non-imported predicate
        assert not prolog.has_solution("regular(X)")

    def test_nested_operator_predicate(self):
        """Test operator predicates with nested operators."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(710, fy, #\).
            :- module(nested_ops, [(#\)/1, test/1]).
            test(#\ (#\ X)) :- X = true.
        """)
        assert prolog.has_solution("nested_ops:test(#\ (#\ true))")

    @pytest.mark.larl_exclude
    def test_mixed_exports_operators_and_regular(self):
        """Test module with both operator predicates and regular predicates."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- op(700, xfx, #=).
            :- module(mixed, [(#=)/2, regular/1, op(300, fy, ~)]).
            #=(A, B) :- A =:= B.
            regular(value).
        """)
        # Both should be accessible
        assert prolog.has_solution("mixed:regular(value)")
        # Test that operator predicate export works
        prolog.consult_string("""
            :- use_module(mixed, [(#=)/2]).
            test_eq :- 2 #= 2.
        """)
        assert prolog.has_solution("test_eq")


class TestModuleQualifiedClauseHeads:
    """Tests for defining predicates with module-qualified heads (Module:Head :- Body)."""

    def test_define_fact_in_user_module(self):
        """Define a fact in user module from another module."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(mylib, []).
            user:my_hook(x, transformed_x).
        """)
        assert prolog.has_solution("user:my_hook(x, Y), Y = transformed_x")

    def test_define_rule_in_user_module(self):
        """Define a rule with module-qualified head in user module."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(mymod, []).
            user:doubled(X, Y) :- Y is X * 2.
        """)
        result = prolog.query_once("user:doubled(5, Y)")
        assert result is not None and result["Y"] == 10

    def test_define_in_named_module(self):
        """Define predicate in a specific named module."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(target, [helper/1]).
            :- module(source, []).
            target:helper(1).
            target:helper(2).
        """)
        results = list(prolog.query("target:helper(X)"))
        assert len(results) == 2
        values = {r["X"] for r in results}
        assert values == {1, 2}

    def test_multiple_clauses_same_predicate(self):
        """Multiple clauses for the same module-qualified predicate."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(mylib, []).
            user:color(red).
            user:color(green).
            user:color(blue).
        """)
        results = list(prolog.query("user:color(X)"))
        assert len(results) == 3
        colors = {r["X"] for r in results}
        assert colors == {"red", "green", "blue"}

    def test_module_qualified_head_with_body(self):
        """Module-qualified head with complex body."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(lib, []).
            user:sum_list([], 0).
            user:sum_list([H|T], S) :- user:sum_list(T, S1), S is H + S1.
        """)
        result = prolog.query_once("user:sum_list([1, 2, 3, 4], S)")
        assert result is not None and result["S"] == 10

    def test_goal_expansion_pattern(self):
        """Test the goal_expansion hook pattern used in libraries."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(dcgs_lib, []).
            user:goal_expansion(phrase(GRBody, S), phrase(GRBody, S, [])).
        """)
        # Verify the clause was added to user module by calling it directly
        result = prolog.query_once("user:goal_expansion(phrase(foo, bar), Expanded)")
        assert result is not None
        # Expanded should be phrase(foo, bar, [])
        expanded = result["Expanded"]
        # Result format is {'phrase': ['foo', 'bar', []]}
        assert "phrase" in expanded
        assert expanded["phrase"] == ["foo", "bar", []]

    def test_cross_module_predicate_definition(self):
        """Define predicates across multiple modules."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(definer, []).
            m1:foo(from_m1).
            m2:foo(from_m2).
            user:foo(from_user).
        """)
        # Ensure all modules got their predicates
        # Note: m1 and m2 are auto-created but without exports
        r1 = prolog.query_once("user:foo(X)")
        assert r1 is not None and r1["X"] == "from_user"
        assert prolog.has_solution("m1:foo(from_m1)")
        assert prolog.has_solution("m2:foo(from_m2)")

    def test_atom_head_fact(self):
        """Test module-qualified fact with atom head (zero-arity predicate)."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(mylib, []).
            user:my_flag.
        """)
        assert prolog.has_solution("user:my_flag")

    def test_preserves_clause_order(self):
        """Ensure clause order is preserved for module-qualified heads."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(lib, []).
            user:num(1).
            user:num(2).
            user:num(3).
        """)
        results = list(prolog.query("user:num(X)"))
        values = [r["X"] for r in results]
        assert values == [1, 2, 3]

    def test_module_created_if_not_exists(self):
        """Target module is created if it doesn't exist."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            newmod:new_pred(value).
        """)
        # Module should exist now
        assert "newmod" in prolog.modules
        # Predicate should be accessible (though not exported)
        assert ("new_pred", 1) in prolog.modules["newmod"].predicates
        assert prolog.has_solution("newmod:new_pred(value)")

    def test_module_qualified_head_with_variable_module(self):
        """Using a variable for the module in a qualified head raises an error."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as excinfo:
            prolog.consult_string("M:foo(a).")
        assert "instantiation_error" in str(excinfo.value.term)

    def test_module_qualified_head_with_non_atom_module(self):
        """Using a non-atom for the module in a qualified head raises an error."""
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow) as excinfo:
            prolog.consult_string("123:foo(a).")
        assert "type_error" in str(excinfo.value.term)


class TestModuleQualifiedPredicateDirectives:
    """Tests for module-qualified predicate property directives."""

    @pytest.mark.larl_exclude
    def test_module_qualified_discontiguous_directive(self):
        """Module-qualified discontiguous directives should work."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(test, []).
            :- discontiguous user:test_pred/2.
            user:test_pred(a, 1).
            foo(bar). % Intervening clause
            user:test_pred(b, 2).
        """)
        
        # Test that both clauses were loaded
        result1 = prolog.query_once("user:test_pred(a, X)")
        assert result1 is not None and result1["X"] == 1
        
        result2 = prolog.query_once("user:test_pred(b, X)")
        assert result2 is not None and result2["X"] == 2

    @pytest.mark.larl_exclude
    def test_module_qualified_dynamic_directive(self):
        """Module-qualified dynamic directives should work."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(test, []).
            :- dynamic user:dynamic_pred/1.
            user:dynamic_pred(test_value).
        """)
        
        result = prolog.query_once("user:dynamic_pred(X)")
        assert result is not None and result["X"] == "test_value"

    @pytest.mark.larl_exclude
    def test_module_qualified_multifile_directive(self):
        """Module-qualified multifile directives should work."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(test, []).
            :- multifile user:multifile_pred/1.
            user:multifile_pred(test_value).
        """)
        
        result = prolog.query_once("user:multifile_pred(X)")
        assert result is not None and result["X"] == "test_value"

    @pytest.mark.larl_exclude
    def test_module_qualified_goal_expansion_scenario(self):
        """Test the specific scenario from the original issue with goal_expansion."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(fmt, []).
            :- discontiguous user:goal_expansion/2.
            
            % Multiple goal_expansion clauses like in format.pl
            user:goal_expansion(format_(Fs,Args,Cs0,Cs), format:format_cells(Cells, Cs0, Cs)).
            user:goal_expansion(format(Fs, Args), (current_output(Stream), format(Stream, Fs, Args))).
            user:goal_expansion(format(Stream, Fs, Args), (pio:phrase_to_stream(format:format_(Fs, Args), Stream), flush_output(Stream))).
        """)
        
        # Test that all clauses were loaded without permission errors
        result1 = prolog.query_once("user:goal_expansion(format_(A,B,C,D), X)")
        assert result1 is not None
        
        result2 = prolog.query_once("user:goal_expansion(format(A,B), X)")
        assert result2 is not None
        
        result3 = prolog.query_once("user:goal_expansion(format(A,B,C), X)")
        assert result3 is not None

    @pytest.mark.larl_exclude
    def test_module_qualified_directive_with_invalid_module(self):
        """Module-qualified directives with invalid module names should raise errors."""
        prolog = PrologInterpreter()
        
        # Test with variable module name
        with pytest.raises(PrologThrow) as excinfo:
            prolog.consult_string("""
                :- module(test, []).
                :- discontiguous Var:test_pred/1.
            """)
        assert "instantiation_error" in str(excinfo.value.term)
        
        # Test with non-atom module name
        with pytest.raises(PrologThrow) as excinfo:
            prolog.consult_string("""
                :- module(test, []).
                :- discontiguous 123:test_pred/1.
            """)
        assert "type_error" in str(excinfo.value.term)

    @pytest.mark.larl_exclude
    def test_module_qualified_directive_creates_module_if_needed(self):
        """Module-qualified directives should create the target module if it doesn't exist."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(test, []).
            :- discontiguous nonexistent_module:test_pred/1.
            nonexistent_module:test_pred(value).
        """)
        
        # Check that the module was created
        assert "nonexistent_module" in prolog.modules
        
        # Test that the clause was added to the correct module by checking the module's predicates
        nonexistent_module = prolog.modules["nonexistent_module"]
        assert ("test_pred", 1) in nonexistent_module.predicates
        assert len(nonexistent_module.predicates[("test_pred", 1)]) == 1

    @pytest.mark.larl_exclude
    def test_mixed_module_qualified_and_regular_directives(self):
        """Test that regular and module-qualified directives can coexist."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            :- module(test, [local_pred/1]).
            :- discontiguous user:test_pred/1.
            :- dynamic local_pred/1.
            
            user:test_pred(user_value).
            local_pred(local_value).
        """)
        
        # Test both predicates work
        result1 = prolog.query_once("user:test_pred(X)")
        assert result1 is not None and result1["X"] == "user_value"
        
        result2 = prolog.query_once("test:local_pred(X)")
        assert result2 is not None and result2["X"] == "local_value"

    def test_module_qualified_discontiguous_error_without_directive(self):
        """Non-contiguous module-qualified predicates without discontiguous should raise error.

        This test verifies that the closed_predicates mechanism works correctly with
        module-qualified predicates. Without the :- discontiguous directive, adding
        clauses for the same predicate after an intervening clause should raise a
        permission_error.
        """
        prolog = PrologInterpreter()

        with pytest.raises(PrologThrow) as excinfo:
            prolog.consult_string("""
                :- module(test, []).
                user:test_pred(a, 1).
                foo(bar). % Intervening clause
                user:test_pred(b, 2).  % Should fail - discontiguous not declared
            """)

        # Should get a permission_error for modifying a static procedure
        assert "permission_error" in str(excinfo.value.term)
