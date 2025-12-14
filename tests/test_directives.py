import pytest

from vibeprolog import PrologInterpreter
from vibeprolog.engine import PrologThrow


class TestPredicateDirectives:
    def test_dynamic_allows_assert_and_retract(self):
        prolog = PrologInterpreter()
        prolog.consult_string(":- dynamic(foo/1).\nfoo(1).")

        assert prolog.has_solution("asserta(foo(2))")
        assert prolog.has_solution("foo(2)")

        result = prolog.query_once(
            "catch(retract(foo(1)), error(permission_error(modify, static_procedure, _), _), fail)"
        )
        assert result is not None
        assert prolog.has_solution("\\+ foo(1)")

    def test_static_predicate_rejects_assert(self):
        prolog = PrologInterpreter()
        result = prolog.query_once(
            "catch(asserta(bar(1)), error(permission_error(modify, static_procedure, Pred), context(Context)), true)."
        )

        assert result is not None
        assert result["Pred"] == {"/": ["bar", 1]}
        assert result["Context"] == "asserta/1"
        assert not prolog.has_solution("bar(1)")

    def test_multifile_allows_multiple_sources(self):
        prolog = PrologInterpreter()
        prolog.consult_string(":- multifile(shared/1).\nshared(1).")
        prolog.consult_string("shared(2).")

        results = prolog.query("shared(X)")
        values = {row["X"] for row in results}
        assert values == {1, 2}

    def test_non_multifile_redefinition_raises(self):
        prolog = PrologInterpreter()
        prolog.consult_string("solo(1).")

        with pytest.raises(PrologThrow):
            prolog.consult_string("solo(2).")

    def test_discontiguous_requires_directive(self):
        prolog = PrologInterpreter()

        with pytest.raises(PrologThrow):
            prolog.consult_string("alpha(1).\nbeta(1).\nalpha(2).")

        prolog2 = PrologInterpreter()
        prolog2.consult_string(
            ":- discontiguous(alpha/1).\nalpha(1).\nbeta(1).\nalpha(2)."
        )
        results = prolog2.query("alpha(X)")
        assert {row["X"] for row in results} == {1, 2}

    def test_predicate_property_queries(self):
        prolog = PrologInterpreter()
        prolog.consult_string(
            ":- dynamic(dyn/1).\n:- multifile(dyn/1).\n:- discontiguous(dyn/1).\ndyn(1)."
        )

        assert prolog.has_solution("predicate_property(dyn/1, dynamic(dyn/1))")
        assert prolog.has_solution("predicate_property(dyn/1, multifile(dyn/1))")
        assert prolog.has_solution("predicate_property(dyn/1, discontiguous(dyn/1))")
        assert not prolog.has_solution("predicate_property(dyn/1, static(dyn/1))")

        prolog.consult_string("static_p(1).")
        assert prolog.has_solution("predicate_property(static_p/1, static(static_p/1))")

        built_in_props = prolog.query("predicate_property(member(_, _), Prop)")
        assert any(row["Prop"] == "built_in" for row in built_in_props)

    def test_invalid_predicate_indicators_raise_errors(self):
        prolog = PrologInterpreter()

        with pytest.raises(PrologThrow):
            prolog.consult_string(":- dynamic(X/1).")

        with pytest.raises(PrologThrow):
            prolog.consult_string(":- dynamic(1/2).")

        with pytest.raises(PrologThrow):
            prolog.consult_string(":- dynamic(foo/x).")

        with pytest.raises(PrologThrow):
            prolog.consult_string(":- dynamic(foo/ -1).")

    def test_builtins_cannot_be_dynamic(self):
        prolog = PrologInterpreter()

        with pytest.raises(PrologThrow):
            prolog.consult_string(":- dynamic(member/2).")

    @pytest.mark.larl_exclude
    def test_dynamic_no_parens_single(self):
        prolog = PrologInterpreter()
        prolog.consult_string(":- dynamic foo/1.\nfoo(1).")

        assert prolog.has_solution("asserta(foo(2))")
        assert prolog.has_solution("foo(2)")

    @pytest.mark.larl_exclude
    def test_dynamic_no_parens_multiple(self):
        prolog = PrologInterpreter()
        prolog.consult_string(":- dynamic foo/1, bar/2.\nfoo(1).\nbar(a, b).")

        assert prolog.has_solution("asserta(foo(2))")
        assert prolog.has_solution("foo(2)")
        assert prolog.has_solution("asserta(bar(c, d))")
        assert prolog.has_solution("bar(c, d)")

    @pytest.mark.larl_exclude
    def test_dynamic_no_parens_multiline(self):
        prolog = PrologInterpreter()
        prolog.consult_string("""\
    :- dynamic
    known/3,
    voice/1.
    known(yes, test, val).
    voice(loud).
    """)

        assert prolog.has_solution("asserta(known(no, test, val2))")
        assert prolog.has_solution("known(no, test, val2)")
        assert prolog.has_solution("asserta(voice(soft))")
        assert prolog.has_solution("voice(soft)")

    @pytest.mark.larl_exclude
    def test_multifile_no_parens(self):
        prolog = PrologInterpreter()
        prolog.consult_string(":- multifile shared/1.\nshared(1).")
        prolog.consult_string("shared(2).")

        results = prolog.query("shared(X)")
        values = {row["X"] for row in results}
        assert values == {1, 2}

    @pytest.mark.larl_exclude
    def test_discontiguous_no_parens(self):
        prolog = PrologInterpreter()
        prolog.consult_string(
            ":- discontiguous alpha/1.\nalpha(1).\nbeta(1).\nalpha(2)."
        )
        results = prolog.query("alpha(X)")
        assert {row["X"] for row in results} == {1, 2}

