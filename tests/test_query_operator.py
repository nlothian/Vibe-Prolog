"""Tests for the ISO-required ?- (query prefix) operator.

The ?- operator should be parsed as a prefix operator with precedence 1200
and associativity fx, allowing ISO-compliant parsing of queries via the
operator table rather than as a special case in the grammar.
"""

import pytest
from vibeprolog.parser import PrologParser, Clause, Compound, Atom, Variable, Number, List
from vibeprolog.interpreter import PrologInterpreter
from vibeprolog.exceptions import PrologThrow
from vibeprolog.operator_defaults import DEFAULT_OPERATORS


class TestQueryOperatorParsing:
    """Tests for parsing the ?- operator as a prefix operator."""

    def test_query_operator_in_operator_table(self):
        """Verify that ?- is defined in the default operator table."""
        # DEFAULT_OPERATORS imported at module scope to comply with E402
        
        # Check that ?- is in the operator table
        query_ops = [op for op in DEFAULT_OPERATORS if op[2] == '?-']
        assert len(query_ops) == 1
        precedence, assoc, name = query_ops[0]
        assert precedence == 1200
        assert assoc == "fx"
        assert name == "?-"

    def test_parse_simple_query(self):
        """Test parsing a simple query: ?- goal."""
        parser = PrologParser()
        clauses = parser.parse("?- true.")
        
        assert len(clauses) == 1
        clause = clauses[0]
        assert isinstance(clause, Clause)
        # The parsed head is a compound with functor ?-
        assert isinstance(clause.head, Compound)
        assert clause.head.functor == "?-"
        assert len(clause.head.args) == 1
        assert isinstance(clause.head.args[0], Atom)
        assert clause.head.args[0].name == "true"

    def test_parse_query_with_compound_goal(self):
        """Test parsing a query with a compound goal."""
        parser = PrologParser()
        clauses = parser.parse("?- member(X, [1, 2, 3]).")
        
        assert len(clauses) == 1
        clause = clauses[0]
        assert isinstance(clause.head, Compound)
        assert clause.head.functor == "?-"
        
        # The goal should be member(X, [1, 2, 3])
        goal = clause.head.args[0]
        assert isinstance(goal, Compound)
        assert goal.functor == "member"
        assert len(goal.args) == 2
        assert isinstance(goal.args[0], Variable)
        assert goal.args[0].name == "X"

    def test_parse_query_with_conjunction(self):
        """Test parsing a query with multiple goals (conjunction)."""
        parser = PrologParser()
        clauses = parser.parse("?- X = 5, write(X).")
        
        assert len(clauses) == 1
        clause = clauses[0]
        assert isinstance(clause.head, Compound)
        assert clause.head.functor == "?-"
        
        # The argument should be a conjunction (comma operator)
        goal = clause.head.args[0]
        assert isinstance(goal, Compound)
        assert goal.functor == ","

    def test_parse_query_with_nested_operations(self):
        """Test parsing a query with nested operators and operator precedence."""
        parser = PrologParser()
        clauses = parser.parse("?- X = (1 + 2 * 3).")
        
        assert len(clauses) == 1
        clause = clauses[0]
        assert clause.head.functor == "?-"
        
        # Verify the arithmetic expression respects operator precedence
        goal = clause.head.args[0]
        assert goal.functor == "="
        right = goal.args[1]  # (1 + 2 * 3)
        # Should be + with args [1, *(2, 3)]
        assert right.functor == "+"
        assert isinstance(right.args[0], Number)
        assert right.args[0].value == 1
        assert right.args[1].functor == "*"

    def test_parse_multiple_queries_in_source(self):
        """Test parsing multiple queries in a single source."""
        parser = PrologParser()
        source = """
        ?- true.
        fact(a).
        ?- goal(X).
        """
        clauses = parser.parse(source)
        
        assert len(clauses) == 3
        # First item: ?- true
        assert clauses[0].head.functor == "?-"
        # Second item: fact(a)
        assert isinstance(clauses[1].head, Compound)
        assert clauses[1].head.functor == "fact"
        # Third item: ?- goal(X)
        assert clauses[2].head.functor == "?-"

    @pytest.mark.larl_exclude
    def test_parse_query_with_cut(self):
        """Test parsing a query with a cut operator."""
        parser = PrologParser()
        clauses = parser.parse("?- member(X, [1, 2, 3]), !.")
        
        assert len(clauses) == 1
        clause = clauses[0]
        assert clause.head.functor == "?-"

    def test_parse_query_with_disjunction(self):
        """Test parsing a query with disjunction (;)."""
        parser = PrologParser()
        clauses = parser.parse("?- (X = 1 ; X = 2).")
        
        assert len(clauses) == 1
        clause = clauses[0]
        assert clause.head.functor == "?-"
        
        goal = clause.head.args[0]
        assert isinstance(goal, Compound)
        assert goal.functor == ";"

    def test_parse_query_with_negation(self):
        """Test parsing a query with negation as failure."""
        parser = PrologParser()
        clauses = parser.parse("?- \\+ fail.")
        
        assert len(clauses) == 1
        clause = clauses[0]
        assert clause.head.functor == "?-"
        
        goal = clause.head.args[0]
        assert isinstance(goal, Compound)
        assert goal.functor == "\\+"

    def test_parse_query_with_if_then_else(self):
        """Test parsing a query with if-then-else construct."""
        parser = PrologParser()
        clauses = parser.parse("?- (X = 1 -> write(yes) ; write(no)).")
        
        assert len(clauses) == 1
        clause = clauses[0]
        assert clause.head.functor == "?-"
        
        goal = clause.head.args[0]
        assert goal.functor == ";"

    def test_parse_query_with_list(self):
        """Test parsing a query with list operations."""
        parser = PrologParser()
        clauses = parser.parse("?- append([1, 2], [3, 4], X).")
        
        assert len(clauses) == 1
        clause = clauses[0]
        goal = clause.head.args[0]
        assert goal.functor == "append"
        assert isinstance(goal.args[0], List)
        assert goal.args[0].elements == (Number(1), Number(2))

    def test_parse_query_with_curly_braces(self):
        """Test parsing a query with curly braces (DCG notation)."""
        parser = PrologParser()
        clauses = parser.parse("?- {X = 5}.")
        
        assert len(clauses) == 1
        clause = clauses[0]
        goal = clause.head.args[0]
        # Curly braces create a compound term with functor {}
        assert goal.functor == "{}"


class TestQueryOperatorInterpreter:
    """Tests for query operator behavior in the interpreter."""

    def test_query_operator_with_has_solution(self):
        """Test that queries can be executed using the interpreter."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            parent(tom, bob).
            parent(bob, ann).
        """)
        
        # The interpreter should be able to execute a query
        result = prolog.has_solution("parent(tom, bob)")
        assert result is True

    def test_query_operator_with_query_method(self):
        """Test using the query method."""
        prolog = PrologInterpreter()
        prolog.consult_string("""
            member_test(X) :- member(X, [a, b, c]).
        """)
        
        results = list(prolog.query("member_test(X)"))
        assert len(results) == 3

    def test_query_operator_syntax_through_consult(self):
        """Test that ?- syntax in source is handled during consultation."""
        prolog = PrologInterpreter()
        
        # Consult source with ?- directive (which is often used as initialization)
        # Note: in this implementation, ?- at the top level is parsed but treated as a clause,
        # not as an implicit directive to execute
        prolog.consult_string("""
            fact(a).
            ?- true.
        """)
        
        # The fact should still be loaded
        assert prolog.has_solution("fact(a)")


class TestQueryOperatorWithCurrentOp:
    """Tests for interaction with current_op/3 predicate."""

    def test_current_op_recognizes_query_operator(self):
        """Test that current_op/3 can query the ?- operator."""
        prolog = PrologInterpreter()
        
        # Query the operator properties
        results = list(prolog.query("current_op(Precedence, Type, '?-')"))
        
        assert len(results) > 0
        result = results[0]
        assert result['Precedence'] == 1200
        assert result['Type'] == 'fx'

    def test_query_operator_precedence_relative_to_others(self):
        """Test that ?- has correct precedence relative to other 1200 operators."""
        prolog = PrologInterpreter()
        
        # Get all 1200 precedence operators
        results = list(prolog.query("current_op(1200, Type, Name)"))
        
        # Should include ?-, :-, and -->
        operators = set()
        for r in results:
            name = r['Name']
            if isinstance(name, Atom):
                operators.add(name.name)
            else:
                operators.add(str(name))
        
        assert '?-' in operators
        assert ':-' in operators


class TestOperatorTableIntegration:
    """Tests for integration with the operator table system."""

    def test_query_operator_in_custom_operator_table(self):
        """Test that ?- works with a custom operator table."""
        from vibeprolog.operators import OperatorTable
        from vibeprolog.parser import PrologParser
        
        op_table = OperatorTable()
        parser = PrologParser(op_table)
        
        # Parse with custom operator table
        clauses = parser.parse("?- test(X).")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "?-"

    def test_query_operator_cannot_be_removed(self):
        """Test that the ?- operator is fundamental and behaves correctly."""
        prolog = PrologInterpreter()

        # Attempt to redefine ?- operator (though this is not recommended)
        with pytest.raises(PrologThrow):
            prolog.consult_string(":- op(1200, fx, '?-').")

        # Should still work
        clauses = prolog.parser.parse("?- goal.")
        assert len(clauses) == 1
        assert clauses[0].head.functor == "?-"


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing code."""

    def test_existing_query_syntax_still_works(self):
        """Verify that the interpreter's query method still works."""
        prolog = PrologInterpreter()
        prolog.consult_string("fact(1).")
        
        # This is how queries are normally executed
        result = prolog.query_once("fact(X)")
        assert result is not None
        # The result may contain a Number object or a raw value
        x_val = result['X']
        if isinstance(x_val, Number):
            assert x_val.value == 1
        else:
            assert x_val == 1

    def test_directives_and_queries_can_coexist(self):
        """Test that directives (:- ) and queries (?-) can appear in the same file."""
        prolog = PrologInterpreter()
        
        source = """
        :- dynamic(fact/1).
        fact(a).
        ?- write(test).
        """
        
        # Should parse without error
        prolog.consult_string(source)
        assert prolog.has_solution("fact(a)")

    def test_facts_and_rules_unaffected(self):
        """Ensure normal facts and rules still parse correctly."""
        parser = PrologParser()
        
        source = """
        parent(tom, bob).
        grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
        ?- member(X, [1, 2, 3]).
        """
        
        clauses = parser.parse(source)
        assert len(clauses) == 3
        
        # First two should be normal facts/rules
        assert clauses[0].head.functor == "parent"
        assert clauses[1].head.functor == "grandparent"
        # Third should be a query
        assert clauses[2].head.functor == "?-"


class TestErrorHandling:
    """Tests for error handling with the query operator."""

    def test_incomplete_query_is_syntax_error(self):
        """Test that incomplete queries produce syntax errors."""
        parser = PrologParser()
        
        with pytest.raises(PrologThrow):
            parser.parse("?- goal")  # Missing period

    def test_malformed_query_goal_is_syntax_error(self):
        """Test that malformed goals in queries are caught."""
        parser = PrologParser()
        
        # This should raise a syntax error during parsing
        with pytest.raises(PrologThrow):
            parser.parse("?- (unclosed(goal).")
