"""Tests for a minimal meta-interpreter."""

import pytest
from vibeprolog import PrologInterpreter


class TestMinimalMetaInterpreter:
    """Tests for the minimal meta-interpreter in minimal_mi_test.pl."""

    @pytest.fixture(scope="class")
    def prolog(self):
        """Fixture to create and load the Prolog interpreter once per class."""
        interpreter = PrologInterpreter()
        # Load the minimal_mi_test.pl file from the tests directory
        try:
            interpreter.consult("tests/minimal_mi_test.pl")
        except FileNotFoundError:
            pytest.skip("Could not find minimal_mi_test.pl")
        return interpreter

    @pytest.mark.larl_exclude
    def test_mi_true(self, prolog):
        """Test mi(true, [], Expl) should succeed with an empty explanation."""
        result = prolog.query_once("mi(true, [], Expl).")
        assert result is not None
        assert result['Expl'] == []

    @pytest.mark.larl_exclude
    def test_mi_fact(self, prolog):
        """Test mi(fact(a), [], Expl) should succeed for a simple fact."""
        result = prolog.query_once("mi(fact(a), [], Expl).")
        assert result is not None
        assert result['Expl'] == []

    @pytest.mark.larl_exclude
    def test_mi_rule(self, prolog):
        """Test mi(rule(X), [], Expl) should find solutions by interpreting the rule."""
        results = list(prolog.query("mi(rule(X), [], Expl)."))
        assert len(results) > 0
        # Assuming rule(X) :- fact(X) and fact(a) is defined.
        first_result = results[0]
        assert first_result['X'] == 'a'
        assert first_result['Expl'] == []

    @pytest.mark.larl_exclude
    def test_mi_integration(self, prolog, capsys):
        """Test the top-level test_mi predicate."""
        # This query prints output, so we capture it and check.
        result = prolog.query_once("test_mi.")
        assert result is not None, "test_mi should succeed."
