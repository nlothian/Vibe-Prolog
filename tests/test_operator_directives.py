import pytest

from vibeprolog import PrologInterpreter
from vibeprolog.exceptions import PrologThrow


class TestOperatorDirectives:
    def test_define_new_operator_and_query_current_op(self):
        prolog = PrologInterpreter()
        prolog.consult_string(":- op(500, xfy, '#').")

        result = prolog.query_once("current_op(P, xfy, '#').")
        assert result is not None
        assert result["P"] == 500

    def test_protected_operator_modify_raises_permission_error(self):
        prolog = PrologInterpreter(builtin_conflict="error")
        with pytest.raises(PrologThrow):
            prolog.consult_string(":- op(500, xfy, ',').")

    def test_invalid_specifier_domain_error(self):
        prolog = PrologInterpreter()
        # Use a truly invalid specifier like 'zfz'
        with pytest.raises(PrologThrow):
            prolog.consult_string(":- op(500, zfz, foo).")

    def test_define_multiple_operators_from_list(self):
        prolog = PrologInterpreter()
        prolog.consult_string(":- op(400, yfx, [foo, bar]).")
        assert prolog.has_solution("current_op(400, yfx, foo).")
        assert prolog.has_solution("current_op(400, yfx, bar).")

    def test_instantiation_error_when_arguments_unbound(self):
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow):
            prolog.consult_string(":- op(P, xfx, foo).")

    def test_type_error_for_precedence(self):
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow):
            prolog.consult_string(":- op(foo, xfx, bar).")

    def test_type_error_for_non_integer_number_precedence(self):
        prolog = PrologInterpreter()
        with pytest.raises(PrologThrow):
            prolog.consult_string(":- op(3.5, xfx, bar).")

    @pytest.mark.larl_exclude
    def test_write_term_respects_new_operator(self):
        prolog = PrologInterpreter()
        prolog.consult_string(
            """
            :- op(500, xfy, foo).
            expr(foo(a, b)).
            """
        )
        result = prolog.query_once(
            "expr(T), write_term_to_chars(T, [ignore_ops(false), quoted(false)], Cs)."
        )
        assert result is not None
        assert "".join(result["Cs"]) == "a foo b"
