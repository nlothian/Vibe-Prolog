"""Operator table and helpers for dynamic operator directives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from vibeprolog.exceptions import PrologError, PrologThrow
from vibeprolog.operator_defaults import DEFAULT_OPERATORS
from vibeprolog.parser import List
from vibeprolog.terms import Atom, Compound, Number, Variable
from vibeprolog.utils.list_utils import list_to_python
from .utils import reconstruct_operator_name_from_term


@dataclass(frozen=True)
class OperatorInfo:
    """Operator metadata."""

    precedence: int
    spec: str  # One of: xfx, xfy, yfx, fx, fy, xf, yf

    @property
    def is_prefix(self) -> bool:
        return self.spec in ("fx", "fy")

    @property
    def is_postfix(self) -> bool:
        return self.spec in ("xf", "yf")

    @property
    def is_infix(self) -> bool:
        return self.spec in ("xfx", "xfy", "yfx", "yfy")


class OperatorTable:
    """Holds operator definitions and validates op/3 directives.

    Supports three builtin_conflict modes:
    - 'skip': Silently ignore attempts to redefine protected operators (default)
    - 'error': Raise permission_error when attempting to redefine protected operators
    - 'shadow': Allow modules to shadow protected operators with module-scoped definitions
    """

    def __init__(self, builtin_conflict: str = "skip") -> None:
        """Initialize the operator table.

        Args:
            builtin_conflict: How to handle redefinition of protected operators.
                - 'skip': Silently ignore attempts to redefine protected operators
                - 'error': Raise permission_error on redefinition attempts
                - 'shadow': Allow module-scoped redefinitions of protected operators
        """
        self._table: dict[tuple[str, str], OperatorInfo] = {}
        self._protected_ops: set[str] = {
            ",",
            ";",
            "->",
            ":-",
            "?-",
            ":",
            "|",
            "{}",
            "(",
            ")",
            "[",
            "]",
        }
        self._builtin_conflict = builtin_conflict
        self._module_operators: dict[str, dict[tuple[str, str], OperatorInfo]] = {}
        self._shadowed_operators: set[tuple[str, str, str]] = set()
        self._version = 0
        self._seed_defaults()

    @property
    def version(self) -> int:
        """Return a monotonic counter that increments on table changes."""

        return self._version

    def _seed_defaults(self) -> None:
        """Populate ISO-ish default operators."""
        for precedence, spec, name in DEFAULT_OPERATORS:
            self._table[(name, spec)] = OperatorInfo(precedence, spec)

    def clone(self) -> "OperatorTable":
        """Create a deep copy of the operator table."""
        clone = OperatorTable(self._builtin_conflict)
        clone._table = dict(self._table)
        clone._module_operators = {
            mod: dict(ops) for mod, ops in self._module_operators.items()
        }
        clone._shadowed_operators = set(self._shadowed_operators)
        clone._version = self._version
        return clone

    def set_builtin_conflict(self, mode: str) -> None:
        """Set the builtin_conflict mode.

        Args:
            mode: One of 'skip', 'error', or 'shadow'
        """
        self._builtin_conflict = mode

    def get_matching(self, name: str) -> list[OperatorInfo]:
        """Return all OperatorInfo entries for a given operator name."""
        return [info for (op, _), info in self._table.items() if op == name]

    def iter_current_ops(self) -> Iterable[Tuple[str, OperatorInfo]]:
        for (name, _), info in sorted(self._table.items(), key=lambda item: (item[1].precedence, item[0])):
            yield name, info

    def lookup(self, name: str, spec: str) -> OperatorInfo | None:
        return self._table.get((name, spec))

    def define(
        self,
        precedence_term,
        spec_term,
        name_term,
        context: str,
        module_name: str | None = None,
    ) -> None:
        """Apply op/3 directive semantics.

        Args:
            precedence_term: The precedence (0-1200)
            spec_term: The associativity specifier (xfx, xfy, yfx, etc.)
            name_term: The operator name (atom or list of atoms)
            context: Context string for error messages
            module_name: If provided, the operator is defined within this module's scope
        """
        precedence_value = self._parse_precedence(precedence_term, context)
        spec = self._parse_specifier(spec_term, context)
        names = self._parse_operator_names(name_term, context)

        for name in names:
            self._define_single(precedence_value, spec, name, context, module_name)

    def _parse_precedence(self, precedence_term, context: str) -> int:
        if isinstance(precedence_term, Variable):
            error_term = PrologError.instantiation_error(context)
            raise PrologThrow(error_term)
        if not isinstance(precedence_term, Number):
            error_term = PrologError.type_error("integer", precedence_term, context)
            raise PrologThrow(error_term)
        if not isinstance(precedence_term.value, int):
            error_term = PrologError.type_error("integer", precedence_term, context)
            raise PrologThrow(error_term)
        precedence = precedence_term.value
        if precedence < 0 or precedence > 1200:
            error_term = PrologError.domain_error("operator_priority", precedence_term, context)
            raise PrologThrow(error_term)
        return precedence

    def _parse_specifier(self, spec_term, context: str) -> str:
        valid_specs = {"xfx", "xfy", "yfx", "yfy", "fx", "fy", "xf", "yf"}
        if isinstance(spec_term, Variable):
            error_term = PrologError.instantiation_error(context)
            raise PrologThrow(error_term)
        if not isinstance(spec_term, Atom):
            error_term = PrologError.type_error("atom", spec_term, context)
            raise PrologThrow(error_term)
        spec = spec_term.name
        if spec not in valid_specs:
            error_term = PrologError.domain_error("operator_specifier", spec_term, context)
            raise PrologThrow(error_term)
        return spec

    def _parse_operator_names(self, name_term, context: str) -> list[str]:

        if isinstance(name_term, Variable):
            error_term = PrologError.instantiation_error(context)
            raise PrologThrow(error_term)
        if isinstance(name_term, Atom):
            return [name_term.name]
        if isinstance(name_term, List):
            try:
                elements = list_to_python(name_term)
            except TypeError:
                error_term = PrologError.type_error("list", name_term, context)
                raise PrologThrow(error_term)

            names: list[str] = []
            for element in elements:
                if isinstance(element, Variable):
                    error_term = PrologError.instantiation_error(context)
                    raise PrologThrow(error_term)
                symbol_name = reconstruct_operator_name_from_term(element)
                if symbol_name is None:
                    error_term = PrologError.type_error("atom", element, context)
                    raise PrologThrow(error_term)
                names.append(symbol_name)
            return names

        flattened = reconstruct_operator_name_from_term(name_term)
        if flattened is not None:
            return [flattened]

        error_term = PrologError.type_error("atom", name_term, context)
        raise PrologThrow(error_term)

    def _define_single(
        self,
        precedence_value: int,
        spec: str,
        name: str,
        context: str,
        module_name: str | None = None,
    ) -> None:
        """Define a single operator with proper handling of protected operators.

        Args:
            precedence_value: The precedence (0-1200)
            spec: The associativity specifier
            name: The operator name
            context: Context string for error messages
            module_name: If provided, the operator is scoped to this module
        """
        key = (name, spec)
        changed = False

        if name in self._protected_ops:
            error_term = PrologError.permission_error(
                "modify", "operator", Atom(name), context
            )
            raise PrologThrow(error_term)

        if precedence_value == 0:
            removed = self._table.pop(key, None)
            changed = changed or (removed is not None)
            if module_name is not None and module_name in self._module_operators:
                removed_module = self._module_operators[module_name].pop(key, None)
                changed = changed or (removed_module is not None)
            if changed:
                self._version += 1
            return

        info = OperatorInfo(precedence_value, spec)
        previous = self._table.get(key)
        self._table[key] = info
        changed = changed or (previous != info)
        if module_name is not None:
            module_ops = self._module_operators.setdefault(module_name, {})
            module_previous = module_ops.get(key)
            module_ops[key] = info
            changed = changed or (module_previous != info)
        if changed:
            self._version += 1

    def get_module_operators(self, module_name: str) -> dict[tuple[str, str], OperatorInfo]:
        """Get all operators defined in a specific module.

        Args:
            module_name: The module name

        Returns:
            Dictionary mapping (name, spec) to OperatorInfo for this module
        """
        return self._module_operators.get(module_name, {})

    def iter_operators_for_module(
        self, module_name: str | None
    ) -> Iterable[Tuple[str, OperatorInfo]]:
        """Iterate over operators visible in a given module context.

        This combines global operators with module-scoped operators (shadows).
        Module-scoped operators take precedence over global ones.

        Args:
            module_name: The module context, or None for global-only operators

        Yields:
            Tuples of (name, OperatorInfo) for all visible operators
        """
        # Start with global operators
        combined: dict[tuple[str, str], OperatorInfo] = dict(self._table)

        # Overlay module-scoped operators if a module is specified
        if module_name is not None and module_name in self._module_operators:
            for key, info in self._module_operators[module_name].items():
                combined[key] = info

        for (name, _), info in sorted(
            combined.items(), key=lambda item: (item[1].precedence, item[0])
        ):
            yield name, info

    def is_shadowed(self, module_name: str, name: str, spec: str) -> bool:
        """Check if an operator is shadowed in a given module.

        Args:
            module_name: The module name
            name: The operator name
            spec: The operator specifier

        Returns:
            True if the operator is shadowed in this module
        """
        return (module_name, name, spec) in self._shadowed_operators

    def is_protected(self, name: str) -> bool:
        """Return True if the operator name is protected."""
        return name in self._protected_ops


__all__ = ["OperatorInfo", "OperatorTable"]
