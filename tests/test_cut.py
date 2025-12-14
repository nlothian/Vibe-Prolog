import pytest

from vibeprolog import PrologInterpreter


@pytest.mark.larl_exclude
def test_cut():
    """Test cut directly."""
    prolog = PrologInterpreter()
    prolog.consult_string("""
    test_cut :- !.
    test_cut_with_true :- !, true.
    """)

    results = prolog.query("test_cut.")
    assert results


@pytest.mark.larl_exclude
def test_cut_with_true():
    """Test cut with true."""
    prolog = PrologInterpreter()
    prolog.consult_string("""
    test_cut_with_true :- !, true.
    """)

    results = prolog.query("test_cut_with_true.")
    assert results


@pytest.mark.larl_exclude
def test_cut_pattern():
    """Test the exact pattern from mi."""
    prolog = PrologInterpreter()
    prolog.consult_string("""
    test_pattern(true, X, X) :- !.
    """)

    results = prolog.query("test_pattern(true, [], Y).")
    assert results
