"""Main Prolog interpreter interface."""

import io
import sys
from pathlib import Path
from typing import Iterator

from lark.exceptions import LarkError

from vibeprolog.exceptions import PrologError, PrologThrow
from vibeprolog.engine import CutException, PrologEngine
from vibeprolog.parser import PrologParser, Clause, Directive
from vibeprolog.terms import Compound, Variable
from vibeprolog.unification import Substitution, apply_substitution


class PrologInterpreter:
    """Main interface for the Prolog interpreter."""

    def __init__(self, argv: list[str] | None = None) -> None:
        self.parser = PrologParser()
        self.clauses = []
        self._argv: list[str] = argv or []
        self.engine = None
        self._initialization_goals: list[Compound] = []

    @property
    def argv(self) -> list[str]:
        return self._argv

    @argv.setter
    def argv(self, value: list[str]) -> None:
        self._argv = value
        if self.engine is not None:
            self.engine.argv = value

    def _raise_syntax_error(self, exc: Exception, location: str) -> None:
        """
        Centralized helper to convert parsing exceptions into Prolog syntax errors
        and raise a PrologThrow with the resulting error term.
        """
        error_term = PrologError.syntax_error(str(exc), location)
        raise PrologThrow(error_term)

    def _process_directive(self, directive: Directive) -> None:
        """Process a directive, collecting initialization goals."""
        from vibeprolog.terms import Atom

        if isinstance(directive.goal, Compound) and directive.goal.functor == "initialization":
            if len(directive.goal.args) != 1:
                error_term = PrologError.type_error("callable", directive.goal, "initialization/1")
                raise PrologThrow(error_term)

            goal = directive.goal.args[0]

            # Check if goal is a variable (instantiation error)
            if isinstance(goal, Variable):
                error_term = PrologError.instantiation_error("initialization/1")
                raise PrologThrow(error_term)

            # Check if goal is callable (not a number or other non-callable)
            if not self._is_callable_term(goal):
                error_term = PrologError.type_error("callable", goal, "initialization/1")
                raise PrologThrow(error_term)

            self._initialization_goals.append(goal)
        # Other directives can be added here in the future

    def _execute_initialization_goals(self) -> None:
        """Execute collected initialization goals in order."""
        for goal in self._initialization_goals:
            # Execute the goal using the query mechanism
            # We need to consume all solutions to ensure backtracking happens
            # For initialization, we want exceptions to propagate
            try:
                # Consume all solutions to ensure the goal executes completely
                for _ in self._query_for_initialization([goal]):
                    pass
            except Exception:
                # Re-raise any exceptions from initialization goals
                raise
        # Clear the initialization goals after execution
        self._initialization_goals.clear()

    def _query_for_initialization(self, goals: list[Compound]) -> Iterator[Substitution]:
        """Query that allows exceptions to propagate (for initialization goals)."""
        # Don't catch PrologThrow for initialization goals
        yield from self.engine._solve_goals(goals, Substitution())

    def _is_callable_term(self, term) -> bool:
        """Check if a term is callable (can be used as a goal)."""
        from vibeprolog.terms import Atom, Number
        from vibeprolog.parser import List

        # Variables are not callable (checked separately)
        if isinstance(term, Variable):
            return False
        # Numbers are not callable
        if isinstance(term, Number):
            return False
        # Empty lists are not callable
        if isinstance(term, List) and not term.elements and term.tail is None:
            return False
        # Atoms and compounds are callable
        return True

    def consult(self, filepath: str | Path):
        """Load Prolog clauses from a file."""
        filepath = Path(filepath)
        with open(filepath, "r") as f:
            content = f.read()

        try:
            parsed_items = self.parser.parse(content, "consult/1")
        except (ValueError, LarkError) as exc:
            error_term = PrologError.syntax_error(str(exc), "consult/1")
            raise PrologThrow(error_term)

        # Separate clauses from directives
        for item in parsed_items:
            if isinstance(item, Clause):
                self.clauses.append(item)
            elif isinstance(item, Directive):
                self._process_directive(item)

        self.engine = PrologEngine(self.clauses, self.argv)

        # Execute initialization goals after all clauses are loaded
        if self._initialization_goals:
            self._execute_initialization_goals()

    def consult_string(self, prolog_code: str):
        """Load Prolog clauses from a string."""
        try:
            parsed_items = self.parser.parse(prolog_code, "consult/1")
        except (ValueError, LarkError) as exc:
            error_term = PrologError.syntax_error(str(exc), "consult/1")
            raise PrologThrow(error_term)

        # Separate clauses from directives
        for item in parsed_items:
            if isinstance(item, Clause):
                self.clauses.append(item)
            elif isinstance(item, Directive):
                self._process_directive(item)

        self.engine = PrologEngine(self.clauses, self.argv)

        # Execute initialization goals after all clauses are loaded
        if self._initialization_goals:
            self._execute_initialization_goals()

    def query(
        self, query_str: str, limit: int | None = None, capture_output: bool = False
    ) -> list[dict[str, any]] | tuple[list[dict[str, any]], bool]:
        """
        Execute a Prolog query and return all solutions.

        Args:
            query_str: Prolog query string (without ?-)
            limit: Maximum number of solutions to return (None for all)
            capture_output: If True, return tuple of (solutions, had_output)

        Returns:
            List of dictionaries mapping variable names to their values
            If capture_output=True, returns (solutions, had_output) where had_output is True if stdout was produced
        """
        if self.engine is None:
            # Initialize empty engine for built-in predicates
            self.engine = PrologEngine(self.clauses, self.argv)

        # Parse the query
        goals = self._parse_query(query_str)

        # Collect variable names from the query
        var_names = self._collect_variables(goals)

        # Capture stdout if requested
        if capture_output:
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

        # Execute query
        solutions = []
        try:
            for i, subst in enumerate(self.engine.query(goals)):
                if limit is not None and i >= limit:
                    break

                # Build solution dictionary
                solution = {}
                for var_name in var_names:
                    var = Variable(var_name)
                    value = apply_substitution(var, subst)
                    solution[var_name] = self._term_to_python(value)

                solutions.append(solution)
        except CutException:
            # Cut can bubble up after yielding committed results; treat it as end-of-search
            pass
        finally:
            if capture_output:
                sys.stdout = old_stdout
                output_text = captured_output.getvalue()
                had_output = len(output_text) > 0
                # Print the captured output
                if had_output:
                    print(output_text, end="")

        if capture_output:
            return solutions, had_output
        return solutions

    def query_once(
        self, query_str: str, capture_output: bool = False
    ) -> dict[str, any] | None | tuple[dict[str, any] | None, bool]:
        """
        Execute a Prolog query and return first solution.

        Args:
            query_str: Prolog query string
            capture_output: If True, return tuple of (solution, had_output)

        Returns:
            None if no solution found.
            If capture_output=False: dict of variable bindings or None
            If capture_output=True: (dict or None, had_output)
        """
        if capture_output:
            solutions, had_output = self.query(query_str, limit=1, capture_output=True)
            return (solutions[0] if solutions else None, had_output)
        else:
            solutions = self.query(query_str, limit=1)
            return solutions[0] if solutions else None

    def has_solution(self, query_str: str) -> bool:
        """Check if a query has at least one solution."""
        return self.query_once(query_str) is not None

    def _parse_query(self, query_str: str) -> list[Compound]:
        """Parse a query string into a list of goals."""
        # Add ?- and . to make it a valid query
        if not query_str.strip().endswith("."):
            query_str = query_str.strip() + "."

        # Parse as a fact and extract the goals
        # We'll use a dummy rule structure
        prolog_code = f"dummy :- {query_str}"
        try:
            clauses = self.parser.parse(prolog_code, "query/1")
        except (ValueError, LarkError) as exc:
            self._raise_syntax_error(exc, "query/1")

        if clauses and clauses[0].body:
            # Flatten conjunction into list of goals
            return self._flatten_conjunction(clauses[0].body[0])

        # Single goal case
        prolog_code = query_str
        try:
            clauses = self.parser.parse(prolog_code, "query/1")
        except (ValueError, LarkError) as exc:
            self._raise_syntax_error(exc, "query/1")
        if clauses:
            return [clauses[0].head]

        raise ValueError(f"Failed to parse query: {query_str}")

    def _flatten_conjunction(self, term) -> list[Compound]:
        """Flatten a conjunction (,) into a list of goals."""
        if isinstance(term, Compound) and term.functor == ",":
            # Recursively flatten left and right
            left = self._flatten_conjunction(term.args[0])
            right = self._flatten_conjunction(term.args[1])
            return left + right
        else:
            return [term]

    def _collect_variables(self, goals: list) -> set[str]:
        """Collect all variable names from goals."""
        from vibeprolog.parser import List

        variables = set()

        def collect_from_term(term):
            if isinstance(term, Variable):
                if not term.name.startswith("_"):  # Skip anonymous variables
                    variables.add(term.name)
            elif isinstance(term, Compound):
                for arg in term.args:
                    collect_from_term(arg)
            elif isinstance(term, List):
                for elem in term.elements:
                    collect_from_term(elem)
                if term.tail is not None:
                    collect_from_term(term.tail)
            elif isinstance(term, list):
                for item in term:
                    collect_from_term(item)

        for goal in goals:
            collect_from_term(goal)

        return variables

    def _term_to_python(self, term) -> any:
        """Convert a Prolog term to a Python value."""
        from vibeprolog.parser import List
        from vibeprolog.terms import Atom, Number, Compound, Variable

        if isinstance(term, Atom):
            return term.name
        elif isinstance(term, Number):
            return term.value
        elif isinstance(term, Variable):
            return f"_{term.name}"  # Unbound variable
        elif isinstance(term, List):
            # Convert list to Python list
            result = [self._term_to_python(elem) for elem in term.elements]
            if term.tail is not None and not (
                isinstance(term.tail, List) and not term.tail.elements
            ):
                # List with tail
                tail_val = self._term_to_python(term.tail)
                if isinstance(tail_val, list):
                    result.extend(tail_val)
                else:
                    result.append(("|", tail_val))
            return result
        elif isinstance(term, Compound):
            # Convert compound to tuple or dict
            if not term.args:
                return term.functor
            args = [self._term_to_python(arg) for arg in term.args]
            return {term.functor: args}
        else:
            return str(term)
