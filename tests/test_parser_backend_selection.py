from pathlib import Path

from vibeprolog import PrologInterpreter
from vibeprolog.parser import PrologParser


def test_consult_prefers_lalr_backend(monkeypatch):
    backends: list[str] = []
    original_create = PrologParser._create_parser

    def tracking_create(self, grammar, *, backend):
        backends.append(backend)
        return original_create(self, grammar, backend=backend)

    monkeypatch.setattr(PrologParser, "_create_parser", tracking_create)

    prolog = PrologInterpreter(builtin_conflict="skip")
    library_path = Path(__file__).resolve().parents[1] / "library" / "lists.pl"

    prolog.consult(library_path)

    assert backends, "Expected at least one parser backend to be built"
    assert backends[0] == "lalr"
    if "earley" in backends:
        earley_index = backends.index("earley")
        assert all(backend == "lalr" for backend in backends[:earley_index])
