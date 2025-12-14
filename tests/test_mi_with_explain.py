import pytest

from vibeprolog import PrologInterpreter


@pytest.mark.larl_exclude
def test_explain_goal_with_rule():
    """Test explain_goal(rule(X), Msg)."""
    prolog = PrologInterpreter()
    prolog.consult("tests/test_mi_with_explain.pl")

    results = prolog.query("explain_goal(rule(X), Msg).")
    assert results


@pytest.mark.larl_exclude
def test_mi_with_rule_variable():
    """Test mi(rule(X), [], Expl)."""
    prolog = PrologInterpreter()
    prolog.consult("tests/test_mi_with_explain.pl")

    results = prolog.query("mi(rule(X), [], Expl).")
    assert len(results) >= 2


@pytest.mark.larl_exclude
def test_mi_with_rule_atom():
    """Test mi(rule(a), [], Expl)."""
    prolog = PrologInterpreter()
    prolog.consult("tests/test_mi_with_explain.pl")

    results = prolog.query("mi(rule(a), [], Expl).")
    assert results


@pytest.mark.larl_exclude
def test_mi_with_fact():
    """Test mi(fact(a), [], Expl)."""
    prolog = PrologInterpreter()
    prolog.consult("tests/test_mi_with_explain.pl")

    results = prolog.query("mi(fact(a), [], Expl).")
    assert results
