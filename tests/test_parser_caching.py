import pytest
from vibeprolog import PrologInterpreter
from vibeprolog.parser import PrologParser


@pytest.mark.larl_exclude
def test_consult_reuses_cached_parser(monkeypatch, tmp_path):
    build_count = 0
    original_create = PrologParser._create_parser

    def counting_create(self, grammar, *, backend):
        nonlocal build_count
        build_count += 1
        return original_create(self, grammar, backend=backend)

    monkeypatch.setattr(PrologParser, "_create_parser", counting_create)

    prolog = PrologInterpreter(builtin_conflict="skip")
    module_path = tmp_path / "simple.pl"
    module_path.write_text(":- module(simple, []).\n:- dynamic p/1, q/0.\np(a).\nq :- p(_).")

    prolog.consult(module_path)
    first_builds = build_count

    prolog.consult(module_path)
    assert build_count == first_builds


def test_operator_changes_invalidate_parser_cache(monkeypatch, tmp_path):
    build_count = 0
    original_create = PrologParser._create_parser

    def counting_create(self, grammar, *, backend):
        nonlocal build_count
        build_count += 1
        return original_create(self, grammar, backend=backend)

    monkeypatch.setattr(PrologParser, "_create_parser", counting_create)

    prolog = PrologInterpreter(builtin_conflict="skip")

    base_path = tmp_path / "base.pl"
    base_path.write_text("base_fact.\n")
    prolog.consult(base_path)
    builds_after_base = build_count

    op_path = tmp_path / "custom_ops.pl"
    op_path.write_text(
        ":- op(400, yfx, ##).\n"
        ":- dynamic(value/1, a/1, '##'/2).\n"
        "value(X) :- a ## X.\n"
        "a ## X :- X is 1.\n"
    )

    prolog.consult(op_path)
    builds_after_op_first = build_count

    prolog.consult(op_path)
    assert build_count == builds_after_op_first
    assert builds_after_op_first > builds_after_base


def test_import_scanner_uses_lightweight_parser(monkeypatch, tmp_path):
    prolog = PrologInterpreter(builtin_conflict="skip")

    parse_called = False

    def fail_parse(*args, **kwargs):
        nonlocal parse_called
        parse_called = True
        raise AssertionError("Fallback import parser should not be used for simple directives")

    monkeypatch.setattr(prolog._import_scanner_parser, "parse", fail_parse)

    dep_path = tmp_path / "dep.pl"
    dep_path.write_text("dep_fact.\n")

    main_path = tmp_path / "main.pl"
    main_path.write_text(f":- ensure_loaded('{dep_path}').\nmain.\n")

    prolog.consult(main_path)

    assert parse_called is False
