"""I/O built-ins (write/1, writeln/1, format/N, nl/0).

Implements basic output predicates including formatted printing.
"""

from __future__ import annotations

from typing import Any, Callable

from lark.exceptions import LarkError

from vibeprolog.builtins import BuiltinRegistry, register_builtin
from vibeprolog.builtins.common import BuiltinArgs, EngineContext
from vibeprolog.exceptions import PrologError, PrologThrow
from vibeprolog.parser import List, PrologParser
from vibeprolog.operators import OperatorInfo, OperatorTable
from vibeprolog.streams import Stream
from vibeprolog.terms import Atom, Compound, Number, Variable
from vibeprolog.unification import Substitution, deref, unify
from vibeprolog.utils.list_utils import list_to_python, python_to_list
from vibeprolog.utils.term_utils import term_to_string
from vibeprolog.utils.variable_utils import collect_vars_in_order

_DEFAULT_OPERATOR_TABLE = OperatorTable()

USER_INPUT_STREAM = Atom("user_input")
USER_OUTPUT_STREAM = Atom("user_output")


class _TermReader:
    """Internal term-reading state machine (top-level)."""
    def __init__(self, stream: Stream, context: str):
        self.stream = stream
        self.context = context
        self.buffer: list[str] = []
        self.paren_depth = 0
        self.bracket_depth = 0
        self.brace_depth = 0
        self.in_single_quote = False
        self.in_double_quote = False
        self.escape_next = False
        self.line_comment = False
        self.started = False
        # Bind to the stream's pushback buffer (assumes it now exists via default_factory)
        self.pushback_buffer = self.stream.pushback_buffer

    def _next_char(self) -> str:
        if self.pushback_buffer:
            return self.pushback_buffer.pop()
        return self.stream.file_obj.read(1)

    def _push_back(self, ch: str) -> None:
        if ch:
            self.pushback_buffer.append(ch)

    def read(self) -> str | None:
        """Core loop copied from the old _read_term_text, refactored into a class."""
        while True:
            ch = self._next_char()
            if ch == "":
                if not self.buffer or not "".join(self.buffer).strip():
                    return None
                error_term = PrologError.syntax_error(
                    "unexpected end of file", self.context
                )
                raise PrologThrow(error_term)

            # Line comments
            if self.line_comment:
                if ch == "\n":
                    self.line_comment = False
                continue

            if not self.in_single_quote and not self.in_double_quote:
                if ch == "%":
                    self.line_comment = True
                    continue
                if ch == "/":
                    peek = self._next_char()
                    if peek == "*":
                        IOBuiltins._skip_block_comments(self._next_char, self._push_back, self.context)
                        continue
                    self._push_back(peek)

            # Beginning of token
            if not self.started and ch.isspace():
                continue

            self.started = True

            # Quoting handling
            if self.in_single_quote or self.in_double_quote:
                self.buffer.append(ch)
                if self.escape_next:
                    self.escape_next = False
                    continue
                if ch == "\\":
                    self.escape_next = True
                    continue

                if self.in_single_quote and ch == "'":
                    self.in_single_quote = False
                elif self.in_double_quote and ch == '"':
                    self.in_double_quote = False
                continue

            if ch == "'":
                self.buffer.append(ch)
                self.in_single_quote = True
                continue

            if ch == '"':
                self.buffer.append(ch)
                self.in_double_quote = True
                continue

            # Parentheses/brackets/braces tracking
            if ch == "(":
                self.paren_depth += 1
            elif ch == ")" and self.paren_depth > 0:
                self.paren_depth -= 1
            elif ch == "[":
                self.bracket_depth += 1
            elif ch == "]" and self.bracket_depth > 0:
                self.bracket_depth -= 1
            elif ch == "{":
                self.brace_depth += 1
            elif ch == "}" and self.brace_depth > 0:
                self.brace_depth -= 1

            self.buffer.append(ch)

            if (
                ch == "."
                and self.paren_depth == 0
                and self.bracket_depth == 0
                and self.brace_depth == 0
            ):
                # After a possible full term, skip trailing layout and determine next token
                next_non_layout, saw_layout = IOBuiltins._consume_layout(
                    self._next_char, self._push_back, self.context
                )
                if next_non_layout == "":
                    return "".join(self.buffer)
                prev_char = self.buffer[-2] if len(self.buffer) >= 2 else ""
                if not saw_layout and prev_char.isdigit() and (
                    next_non_layout.isdigit()
                    or next_non_layout in ("e", "E")
                ):
                    self._push_back(next_non_layout)
                    continue
                self._push_back(next_non_layout)
                return "".join(self.buffer)

class IOBuiltins:
    """Built-ins for standard output and formatting."""

    @staticmethod
    def register(registry: BuiltinRegistry, _engine: EngineContext | None) -> None:
        """Register I/O predicate handlers."""
        # Existing predicates
        register_builtin(registry, "write", 1, IOBuiltins._builtin_write)
        register_builtin(registry, "writeln", 1, IOBuiltins._builtin_writeln)
        register_builtin(registry, "format", 3, IOBuiltins._builtin_format)
        register_builtin(registry, "format", 2, IOBuiltins._builtin_format_stdout)
        register_builtin(
            registry,
            "format",
            1,
            lambda args, subst, engine: IOBuiltins._builtin_format_stdout(
                (args[0], List(())), subst, engine
            ),
        )
        register_builtin(registry, "nl", 0, IOBuiltins._builtin_newline)
        register_builtin(
            registry, "read_from_chars", 2, IOBuiltins._builtin_read_from_chars
        )
        register_builtin(
            registry, "write_term_to_chars", 3, IOBuiltins._builtin_write_term_to_chars
        )
        register_builtin(registry, "current_input", 1, IOBuiltins._builtin_current_input)
        register_builtin(registry, "current_output", 1, IOBuiltins._builtin_current_output)
        register_builtin(registry, "open", 3, IOBuiltins._builtin_open)
        register_builtin(registry, "close", 1, IOBuiltins._builtin_close)
        register_builtin(registry, "read", 1, IOBuiltins._builtin_read)
        register_builtin(registry, "read", 2, IOBuiltins._builtin_read_from_stream)
        register_builtin(registry, "get_char", 1, IOBuiltins._builtin_get_char)
        register_builtin(registry, "get_char", 2, IOBuiltins._builtin_get_char_from_stream)
        register_builtin(registry, "put_char", 1, IOBuiltins._builtin_put_char)
        register_builtin(registry, "put_char", 2, IOBuiltins._builtin_put_char_to_stream)

        # New ISO predicates
        register_builtin(registry, "read_term", 2, IOBuiltins._builtin_read_term)
        register_builtin(registry, "read_term", 3, IOBuiltins._builtin_read_term_from_stream)
        register_builtin(registry, "write_term", 2, IOBuiltins._builtin_write_term)
        register_builtin(registry, "write_term", 3, IOBuiltins._builtin_write_term_to_stream)
        register_builtin(registry, "writeq", 1, IOBuiltins._builtin_writeq)
        register_builtin(registry, "writeq", 2, IOBuiltins._builtin_writeq_to_stream)
        register_builtin(registry, "write_canonical", 1, IOBuiltins._builtin_write_canonical)
        register_builtin(registry, "write_canonical", 2, IOBuiltins._builtin_write_canonical_to_stream)
        register_builtin(registry, "print", 1, IOBuiltins._builtin_print)
        register_builtin(registry, "print", 2, IOBuiltins._builtin_print_to_stream)
        register_builtin(registry, "write", 2, IOBuiltins._builtin_write_to_stream)
        register_builtin(registry, "writeln", 2, IOBuiltins._builtin_writeln_to_stream)
        register_builtin(registry, "set_input", 1, IOBuiltins._builtin_set_input)
        register_builtin(registry, "set_output", 1, IOBuiltins._builtin_set_output)
        register_builtin(registry, "flush_output", 0, IOBuiltins._builtin_flush_output)
        register_builtin(registry, "flush_output", 1, IOBuiltins._builtin_flush_output_stream)
        register_builtin(registry, "at_end_of_stream", 0, IOBuiltins._builtin_at_end_of_stream)
        register_builtin(registry, "at_end_of_stream", 1, IOBuiltins._builtin_at_end_of_stream_stream)
        register_builtin(registry, "stream_property", 2, IOBuiltins._builtin_stream_property)
        register_builtin(registry, "set_stream_position", 2, IOBuiltins._builtin_set_stream_position)
        register_builtin(registry, "open", 4, IOBuiltins._builtin_open_with_options)
        register_builtin(registry, "close", 2, IOBuiltins._builtin_close_with_options)

    @staticmethod
    def _builtin_write(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        term = deref(args[0], subst)
        output = term_to_string(term)
        if engine is not None:
            current_output = getattr(engine, '_current_output_stream', USER_OUTPUT_STREAM)
            stream = engine.get_stream(current_output)
            if stream is not None:
                stream.file_obj.write(output)
                stream.file_obj.flush()
                return subst
        # Fallback to stdout
        print(output, end="")
        return subst

    @staticmethod
    def _builtin_writeln(
        args: BuiltinArgs, subst: Substitution, _engine: EngineContext | None
    ) -> Substitution | None:
        term = deref(args[0], subst)
        output = term_to_string(term)
        print(output)
        return subst

    @staticmethod
    def _builtin_write_to_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """write/2 - Write term to specified stream."""
        if engine is None:
            return None

        stream_term, term = args

        engine._check_instantiated(stream_term, subst, "write/2")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "write/2")

        stream_term = deref(stream_term, subst)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "write/2")
            raise PrologThrow(error_term)

        if stream.mode not in ("write", "append"):
            error_term = PrologError.permission_error("output", "stream", stream_term, "write/2")
            raise PrologThrow(error_term)

        term = deref(term, subst)
        output = term_to_string(term)
        stream.file_obj.write(output)
        stream.file_obj.flush()
        return subst

    @staticmethod
    def _builtin_writeln_to_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """writeln/2 - Write term with newline to specified stream."""
        if engine is None:
            return None

        stream_term, term = args

        engine._check_instantiated(stream_term, subst, "writeln/2")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "writeln/2")

        stream_term = deref(stream_term, subst)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "writeln/2")
            raise PrologThrow(error_term)

        if stream.mode not in ("write", "append"):
            error_term = PrologError.permission_error("output", "stream", stream_term, "writeln/2")
            raise PrologThrow(error_term)

        term = deref(term, subst)
        output = term_to_string(term)
        stream.file_obj.write(output)
        stream.file_obj.write("\n")
        stream.file_obj.flush()
        return subst

    @staticmethod
    def _builtin_format(
        args: BuiltinArgs, subst: Substitution, _engine: EngineContext | None
    ) -> Substitution | None:
        output, format_str, args_list = args
        output = deref(output, subst)
        if (
            not isinstance(output, Compound)
            or output.functor != "atom"
            or len(output.args) != 1
        ):
            return None

        rendered = IOBuiltins._format_to_string(format_str, args_list, subst)
        if rendered is None:
            return None

        return unify(output.args[0], Atom(rendered), subst)

    @staticmethod
    def _builtin_format_stdout(
        args: BuiltinArgs, subst: Substitution, _engine: EngineContext | None
    ) -> Substitution | None:
        format_str, args_list = args
        rendered = IOBuiltins._format_to_string(format_str, args_list, subst)
        if rendered is None:
            return None

        print(rendered, end="")
        return subst

    @staticmethod
    def _builtin_newline(
        _args: BuiltinArgs, subst: Substitution, _engine: EngineContext | None
    ) -> Substitution:
        print()
        return subst

    @staticmethod
    def _builtin_current_input(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        if engine is None:
            return None
        arg = deref(args[0], subst)
        # Get the current input stream
        current_input = getattr(engine, '_current_input_stream', USER_INPUT_STREAM)
        stream = engine.get_stream(current_input)
        if stream is None:
            return None
        return unify(arg, stream.handle, subst)

    @staticmethod
    def _builtin_current_output(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        if engine is None:
            return None
        arg = deref(args[0], subst)
        # Get the current output stream
        current_output = getattr(engine, '_current_output_stream', USER_OUTPUT_STREAM)
        stream = engine.get_stream(current_output)
        if stream is None:
            return None
        return unify(arg, stream.handle, subst)

    @staticmethod
    def _format_to_string(
        format_term: Any, args_term: Any, subst: Substitution
    ) -> str | None:
        format_term = deref(format_term, subst)
        args_term = deref(args_term, subst)

        if not isinstance(format_term, Atom):
            return None

        try:
            format_args = list_to_python(args_term, subst)
        except TypeError:
            return None

        coerced_args: list[str | int | float] = []
        for elem in format_args:
            elem = deref(elem, subst)
            if isinstance(elem, Number):
                coerced_args.append(elem.value)
            elif isinstance(elem, Atom):
                coerced_args.append(elem.name)
            elif isinstance(elem, Variable):
                coerced_args.append(f"_{elem.name}")
            else:
                coerced_args.append(str(elem))

        fmt = format_term.name
        result = ""
        i = 0
        arg_index = 0

        while i < len(fmt):
            if fmt[i] == "~":
                if i + 1 < len(fmt):
                    next_char = fmt[i + 1]

                    if next_char == "~":
                        result += "~"
                        i += 2
                    elif next_char == "w":
                        if arg_index < len(coerced_args):
                            result += str(coerced_args[arg_index])
                            arg_index += 1
                        i += 2
                    elif next_char == "d":
                        if arg_index < len(coerced_args):
                            result += str(int(coerced_args[arg_index]))
                            arg_index += 1
                        i += 2
                    elif next_char.isdigit():
                        j = i + 1
                        while j < len(fmt) and fmt[j].isdigit():
                            j += 1
                        if j < len(fmt) and fmt[j] == "f":
                            precision = int(fmt[i + 1 : j])
                            if arg_index < len(coerced_args):
                                result += (
                                    f"{float(coerced_args[arg_index]):.{precision}f}"
                                )
                                arg_index += 1
                            i = j + 1
                        else:
                            result += fmt[i]
                            i += 1
                    elif next_char == "f":
                        if arg_index < len(coerced_args):
                            result += str(float(coerced_args[arg_index]))
                            arg_index += 1
                        i += 2
                    elif next_char == "n":
                        result += "\n"
                        i += 2
                    else:
                        result += fmt[i]
                        i += 1
                else:
                    result += fmt[i]
                    i += 1
            else:
                result += fmt[i]
                i += 1

        return result

    @staticmethod
    def _builtin_read_from_chars(
        args: BuiltinArgs, subst: Substitution, _engine: EngineContext | None
    ) -> Substitution | None:
        """read_from_chars/2 - Parse a Prolog term from a string.

        read_from_chars(+Chars, -Term)
        Parses Chars (atom or list of chars) as a Prolog term and unifies with Term.
        """
        chars_term, term_var = args
        chars_term = deref(chars_term, subst)

        # Convert input to string
        if isinstance(chars_term, Atom):
            input_str = chars_term.name
        elif isinstance(chars_term, List):
            try:
                char_list = list_to_python(chars_term, subst)
                # Convert list of character atoms to string
                input_str = ''.join(
                    c.name if isinstance(c, Atom) else str(c)
                    for c in char_list
                )
            except (TypeError, AttributeError):
                return None
        else:
            return None

        # Parse the string as a Prolog term
        try:
            parser = PrologParser()
            # Remove trailing period if present (parse expects no period)
            input_str = input_str.strip()
            if input_str.endswith('.'):
                input_str = input_str[:-1].strip()

            parsed_term = parser.parse_term(input_str, "read_from_chars/2")
            return unify(term_var, parsed_term, subst)
        except (ValueError, LarkError, PrologThrow) as exc:
            if isinstance(exc, PrologThrow):
                raise exc
            else:
                error_term = PrologError.syntax_error(str(exc), "read_from_chars/2")
                raise PrologThrow(error_term)

    @staticmethod
    def _builtin_write_term_to_chars(
        args: BuiltinArgs, subst: Substitution, _engine: EngineContext | None
    ) -> Substitution | None:
        """write_term_to_chars/3 - Convert a Prolog term to a character list.

        write_term_to_chars(+Term, +Options, -Chars)
        Converts Term to a string representation according to Options and unifies with Chars.

        Supported options:
        - ignore_ops(true/false): Write in canonical form
        - numbervars(true/false): Convert $VAR(N) to variable names (A, B, C, ...)
        - quoted(true/false): Quote atoms that need quoting
        - variable_names([]): Variable name mappings (not yet implemented)
        """
        term, options_term, chars_var = args
        term = deref(term, subst)
        options_term = deref(options_term, subst)

        # Parse options
        try:
            options_list = list_to_python(options_term, subst)
        except TypeError:
            return None

        # Extract option values
        ignore_ops = False
        numbervars = False
        quoted = False

        for opt in options_list:
            opt = deref(opt, subst)
            if isinstance(opt, Compound):
                if opt.functor == "ignore_ops" and len(opt.args) == 1:
                    val = deref(opt.args[0], subst)
                    ignore_ops = isinstance(val, Atom) and val.name == "true"
                elif opt.functor == "numbervars" and len(opt.args) == 1:
                    val = deref(opt.args[0], subst)
                    numbervars = isinstance(val, Atom) and val.name == "true"
                elif opt.functor == "quoted" and len(opt.args) == 1:
                    val = deref(opt.args[0], subst)
                    quoted = isinstance(val, Atom) and val.name == "true"

        # Convert term to string
        operator_table = _engine.operator_table if _engine is not None else None

        output_str = IOBuiltins._term_to_chars_string(
            term, subst, ignore_ops, numbervars, quoted, None, operator_table
        )

        # Convert string to list of character atoms
        char_list = [Atom(c) for c in output_str]
        chars_list = python_to_list(char_list)

        return unify(chars_var, chars_list, subst)

    @staticmethod
    def _builtin_parse_write_options(options_term, subst: Substitution) -> dict:
        """Parse write_term/2 options into a dict, returning defaults if omitted.
        Raises PrologThrow on errors to align with existing error handling."""
        options_deref = deref(options_term, subst)
        if not isinstance(options_deref, List):
            error_term = PrologError.type_error("list", options_term, "write_term/2")
            raise PrologThrow(error_term)


        # Defaults
        parsed = {
            "quoted": False,
            "ignore_ops": False,
            "numbervars": False,
            "max_depth": None,
        }

        for opt in options_deref.elements:
            opt = deref(opt, subst)
            if isinstance(opt, Compound):
                if opt.functor == "quoted" and len(opt.args) == 1:
                    val = deref(opt.args[0], subst)
                    parsed["quoted"] = isinstance(val, Atom) and val.name == "true"
                elif opt.functor == "ignore_ops" and len(opt.args) == 1:
                    val = deref(opt.args[0], subst)
                    parsed["ignore_ops"] = isinstance(val, Atom) and val.name == "true"
                elif opt.functor == "numbervars" and len(opt.args) == 1:
                    val = deref(opt.args[0], subst)
                    parsed["numbervars"] = isinstance(val, Atom) and val.name == "true"
                elif opt.functor == "max_depth" and len(opt.args) == 1:
                    val = deref(opt.args[0], subst)
                    if isinstance(val, Number) and isinstance(val.value, int) and val.value >= 0:
                        parsed["max_depth"] = val.value
                    else:
                        error_term = PrologError.domain_error("write_option", opt, "write_term/2")
                        raise PrologThrow(error_term)
                else:
                    error_term = PrologError.domain_error("write_option", opt, "write_term/2")
                    raise PrologThrow(error_term)
            else:
                error_term = PrologError.domain_error("write_option", opt, "write_term/2")
                raise PrologThrow(error_term)
        return parsed
    @staticmethod
    def _builtin_write_term(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """write_term/2 - Write term to current output with options."""
        if engine is None:
            return None

        term, options_term = args
        term = deref(term, subst)
        options_term = deref(options_term, subst)

        # Use shared helper to parse options
        parsed = IOBuiltins._builtin_parse_write_options(options_term, subst)
        quoted = parsed["quoted"]
        ignore_ops = parsed["ignore_ops"]
        numbervars = parsed["numbervars"]
        max_depth = parsed["max_depth"]

        # Write to current output
        operator_table = engine.operator_table if engine is not None else None
        output_str = IOBuiltins._term_to_chars_string_with_options(
            term, subst, ignore_ops, numbervars, quoted, max_depth, operator_table
        )
        print(output_str, end="")
        return subst

    @staticmethod
    def _builtin_write_term_to_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """write_term/3 - Write term to specified stream with options."""
        if engine is None:
            return None

        stream_term, term, options_term = args

        engine._check_instantiated(stream_term, subst, "write_term/3")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "write_term/3")

        stream_term = deref(stream_term, subst)
        term = deref(term, subst)
        options_term = deref(options_term, subst)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "write_term/3")
            raise PrologThrow(error_term)

        if stream.mode not in ("write", "append"):
            error_term = PrologError.permission_error("output", "stream", stream_term, "write_term/3")
            raise PrologThrow(error_term)

        # Use shared helper to parse options
        parsed = IOBuiltins._parse_write_term_options(options_term, subst)
        quoted = parsed["quoted"]
        ignore_ops = parsed["ignore_ops"]
        numbervars = parsed["numbervars"]
        max_depth = parsed["max_depth"]

        # Write to stream
        operator_table = engine.operator_table if engine is not None else None
        output_str = IOBuiltins._term_to_chars_string_with_options(
            term, subst, ignore_ops, numbervars, quoted, max_depth, operator_table
        )
        stream.file_obj.write(output_str)
        stream.file_obj.flush()
        return subst

    @staticmethod
    def _term_to_chars_string(
        term: Any,
        subst: Substitution,
        ignore_ops: bool,
        numbervars: bool,
        quoted: bool,
        max_depth: int | None,
        operator_table=None,
        current_depth: int = 0,
        parent_prec: int = 1200,
    ) -> str:
        """Convert a term to string with full options support including max_depth."""
        term = deref(term, subst)

        # Check max_depth
        if max_depth is not None and current_depth >= max_depth:
            return "..."

        # Handle $VAR(N) for numbervars
        if numbervars and isinstance(term, Compound) and term.functor == "$VAR" and len(term.args) == 1:
            arg = deref(term.args[0], subst)
            if isinstance(arg, Number) and isinstance(arg.value, int) and arg.value >= 0:
                # Convert to A, B, C, ..., Z, A1, B1, ...
                n = arg.value
                var_name = chr(ord('A') + (n % 26))
                if n >= 26:
                    var_name += str(n // 26)
                return var_name

        if isinstance(term, Atom):
            if quoted and IOBuiltins._needs_quoting(term.name):
                # Escape special characters
                escaped = term.name.replace('\\', '\\\\').replace("'", "\\'")
                return f"'{escaped}'"
            return term.name

        if isinstance(term, Number):
            val = term.value
            if isinstance(val, float):
                # Handle scientific notation
                s = str(val)
                if 'e' in s:
                    return s
                # Check if we need scientific notation
                if abs(val) >= 1e10 or (abs(val) < 1e-4 and val != 0):
                    return f"{val:e}"
                return s
            return str(val)

        if isinstance(term, Variable):
            return f"_{term.name}"

        if isinstance(term, List):
            # Handle empty list
            if not term.elements and term.tail is None:
                return "[]"

            # Handle list elements
            elements_str = [
                IOBuiltins._term_to_chars_string(
                    e, subst, ignore_ops, numbervars, quoted, max_depth, operator_table, current_depth + 1, 1200
                )
                for e in term.elements
            ]

            # Handle tail
            if term.tail is not None and not (
                isinstance(term.tail, List) and not term.tail.elements and term.tail.tail is None
            ):
                tail_str = IOBuiltins._term_to_chars_string(
                    term.tail, subst, ignore_ops, numbervars, quoted, max_depth, operator_table, current_depth + 1, 1200
                )
                return f"[{','.join(elements_str)}|{tail_str}]"

            return f"[{','.join(elements_str)}]"

        if isinstance(term, Compound):
            if not ignore_ops:
                operator_rendered = IOBuiltins._format_operator_term(
                    term, subst, ignore_ops, numbervars, quoted, parent_prec, max_depth, operator_table, current_depth
                )
                if operator_rendered is not None:
                    return operator_rendered
            if not term.args:
                if quoted and IOBuiltins._needs_quoting(term.functor):
                    escaped = term.functor.replace('\\', '\\\\').replace("'", "\\'")
                    return f"'{escaped}'"
                return term.functor
            args_str = ','.join(
                IOBuiltins._term_to_chars_string(
                    arg, subst, ignore_ops, numbervars, quoted, max_depth, operator_table, current_depth + 1, 1200
                )
                for arg in term.args
            )
            functor = term.functor
            if quoted and IOBuiltins._needs_quoting(functor):
                escaped = functor.replace('\\', '\\\\').replace("'", "\\'")
                functor = f"'{escaped}'"
            return f"{functor}({args_str})"

        return str(term)

    @staticmethod
    def _term_to_chars_string_with_options(
        term: Any,
        subst: Substitution,
        ignore_ops: bool,
        numbervars: bool,
        quoted: bool,
        max_depth: int | None,
        operator_table=None,
        current_depth: int = 0,
        parent_prec: int = 1200,
    ) -> str:
        """Convert a term to string with full options support including max_depth."""
        term = deref(term, subst)

        # Check max_depth
        if max_depth is not None and current_depth >= max_depth:
            return "..."

        # Handle $VAR(N) for numbervars
        if numbervars and isinstance(term, Compound) and term.functor == "$VAR" and len(term.args) == 1:
            arg = deref(term.args[0], subst)
            if isinstance(arg, Number) and isinstance(arg.value, int) and arg.value >= 0:
                # Convert to A, B, C, ..., Z, A1, B1, ...
                n = arg.value
                var_name = chr(ord('A') + (n % 26))
                if n >= 26:
                    var_name += str(n // 26)
                return var_name

        if isinstance(term, Atom):
            if quoted and IOBuiltins._needs_quoting(term.name):
                # Escape special characters
                escaped = term.name.replace('\\', '\\\\').replace("'", "\\'")
                return f"'{escaped}'"
            return term.name

        if isinstance(term, Number):
            val = term.value
            if isinstance(val, float):
                # Handle scientific notation
                s = str(val)
                if 'e' in s:
                    return s
                # Check if we need scientific notation
                if abs(val) >= 1e10 or (abs(val) < 1e-4 and val != 0):
                    return f"{val:e}"
                return s
            return str(val)

        if isinstance(term, Variable):
            return f"_{term.name}"

        if isinstance(term, List):
            # Handle empty list
            if not term.elements and term.tail is None:
                return "[]"

            # Handle list elements
            elements_str = [
                IOBuiltins._term_to_chars_string_with_options(
                    e, subst, ignore_ops, numbervars, quoted, max_depth, operator_table, current_depth + 1
                )
                for e in term.elements
            ]

            # Handle tail
            if term.tail is not None and not (
                isinstance(term.tail, List) and not term.tail.elements and term.tail.tail is None
            ):
                tail_str = IOBuiltins._term_to_chars_string_with_options(
                    term.tail, subst, ignore_ops, numbervars, quoted, max_depth, operator_table, current_depth + 1
                )
                return f"[{','.join(elements_str)}|{tail_str}]"

            return f"[{','.join(elements_str)}]"

        if isinstance(term, Compound):
            if not ignore_ops:
                operator_rendered = IOBuiltins._format_operator_term(
                    term, subst, ignore_ops, numbervars, quoted, parent_prec, max_depth, operator_table, current_depth
                )
                if operator_rendered is not None:
                    return operator_rendered
            if not term.args:
                if quoted and IOBuiltins._needs_quoting(term.functor):
                    escaped = term.functor.replace('\\', '\\\\').replace("'", "\\'")
                    return f"'{escaped}'"
                return term.functor
            args_str = ','.join(
                IOBuiltins._term_to_chars_string_with_options(
                    arg, subst, ignore_ops, numbervars, quoted, max_depth, operator_table, current_depth + 1
                )
                for arg in term.args
            )
            functor = term.functor
            if quoted and IOBuiltins._needs_quoting(functor):
                escaped = functor.replace('\\', '\\\\').replace("'", "\\'")
                functor = f"'{escaped}'"
            return f"{functor}({args_str})"

        return str(term)

    @staticmethod
    def _format_operator_term(
        term: Compound,
        subst: Substitution,
        ignore_ops: bool,
        numbervars: bool,
        quoted: bool,
        parent_prec: int,
        max_depth: int | None,
        operator_table=None,
        current_depth: int = 0,
    ) -> str | None:
        op_info = IOBuiltins._lookup_operator(term.functor, len(term.args), operator_table)
        if op_info is None:
            return None

        if op_info.is_prefix:
            arg_limit = IOBuiltins._child_precedence_limit(op_info, "right")
            arg_str = IOBuiltins._term_to_chars_string_with_options(
                term.args[0], subst, ignore_ops, numbervars, quoted, max_depth, operator_table, current_depth + 1, arg_limit
            )
            rendered = IOBuiltins._render_prefix(term.functor, arg_str)
        else:
            left_limit = IOBuiltins._child_precedence_limit(op_info, "left")
            right_limit = IOBuiltins._child_precedence_limit(op_info, "right")
            left_str = IOBuiltins._term_to_chars_string_with_options(
                term.args[0], subst, ignore_ops, numbervars, quoted, max_depth, operator_table, current_depth + 1, left_limit
            )
            right_str = IOBuiltins._term_to_chars_string_with_options(
                term.args[1], subst, ignore_ops, numbervars, quoted, max_depth, operator_table, current_depth + 1, right_limit
            )
            rendered = IOBuiltins._render_infix(term.functor, left_str, right_str)

        # Wrap only when the current operator binds looser than the parent context.
        if op_info.precedence > parent_prec:
            return f"({rendered})"
        return rendered

    @staticmethod
    def _lookup_operator(functor: str, arity: int, operator_table) -> OperatorInfo | None:
        table = operator_table if operator_table is not None else _DEFAULT_OPERATOR_TABLE
        matches = table.get_matching(functor)
        if arity == 1:
            for info in matches:
                if info.is_prefix or info.is_postfix:
                    return info
        elif arity == 2:
            for info in matches:
                if info.is_infix:
                    return info
        return None

    @staticmethod
    def _child_precedence_limit(info: OperatorInfo, position: str) -> int:
        if info.is_prefix:
            char = info.spec[1]
        else:
            char = info.spec[0] if position == "left" else info.spec[2]
        return info.precedence - 1 if char == "x" else info.precedence

    @staticmethod
    def _render_prefix(functor: str, arg_str: str) -> str:
        if functor and functor[0].isalpha():
            return f"{functor} {arg_str}"
        return f"{functor}{arg_str}"

    @staticmethod
    def _render_infix(functor: str, left: str, right: str) -> str:
        if functor in {":-", "?-"}:
            return f"{left} {functor} {right}"
        if functor and functor[0].isalpha():
            return f"{left} {functor} {right}"
        if functor == ",":
            return f"{left},{right}"
        if functor == ";":
            return f"{left};{right}"
        return f"{left}{functor}{right}"

    @staticmethod
    def _needs_quoting(atom: str) -> bool:
        """Check if an atom needs quoting."""
        if not atom:
            return True

        # An atom starting with a lowercase letter followed by alphanumerics or underscores does not need quoting.
        if atom[0].islower() and all(c.isalnum() or c == '_' for c in atom):
            return False

        # A set of common graphic/symbolic atoms that do not need quoting.
        # This set is not exhaustive but covers many common cases.
        unquoted_graphic_atoms = {
            '!', ';', ',', '+', '-', '*', '/', '//', '**', '=', ':-', '->', '\\=',
            '<', '>', '=<', '>=', '=:=', '=\\=', '==', '\\==',
            '@<', '@>', '@=<', '@>=', 'is', '=..', '\\+'
        }
        if atom in unquoted_graphic_atoms:
            return False

        # Atoms that are just `[]` or `{}`
        if atom in ('[]', '{}'):
            return False

        # Everything else needs quoting (e.g., starts with uppercase, contains spaces, looks like a number).
        return True

    @staticmethod
    def _consume_layout(
        next_char: Callable[[], str], push_back: Callable[[str], None], context: str
    ) -> tuple[str, bool]:
        """Skip layout and comments after a period and return the next char.

        Returns a tuple of (next_char, saw_layout) where saw_layout is True if any
        whitespace or comments were skipped before encountering the character.
        """

        saw_layout = False
        while True:
            ch = next_char()
            if ch == "":
                return "", saw_layout

            if ch.isspace():
                saw_layout = True
                continue

            if ch == "%":
                # Skip line comment
                saw_layout = True
                while True:
                    comment_char = next_char()
                    if comment_char in ("", "\n"):
                        break
                continue

            if ch == "/":
                peek = next_char()
                if peek == "*":
                    # Use shared helper to skip nested block comments
                    saw_layout = True
                    IOBuiltins._skip_block_comments(next_char, push_back, context)
                    continue
                push_back(peek)
                return ch, saw_layout

            return ch, saw_layout

    @staticmethod
    def _skip_block_comments(
        next_char: Callable[[], str], push_back: Callable[[str], None], context: str
    ) -> None:
        """Consume nested block comments /* ... */ starting after '/*' was seen.

        Raises a syntax_error on unterminated block comments.
        """
        depth = 1
        while depth > 0:
            c = next_char()
            if c == "":
                error_term = PrologError.syntax_error(
                    "Unterminated block comment", context
                )
                raise PrologThrow(error_term)
            if c == "/":
                nxt = next_char()
                if nxt == "*":
                    depth += 1
                    continue
                push_back(nxt)
            elif c == "*":
                nxt = next_char()
                if nxt == "/":
                    depth -= 1
                    continue
                push_back(nxt)

    @staticmethod
    def _read_term_text(stream: Stream, context: str) -> str | None:
        """Read characters from stream until a full term (ending with '.') is found.
        Delegates to a dedicated _TermReader for maintainability.
        """
        reader = _TermReader(stream, context)
        return reader.read()

    @staticmethod
    def _read_and_unify_stream(
        stream: Stream, term_arg: Any, subst: Substitution, context: str
    ) -> Substitution | None:
        term_text = IOBuiltins._read_term_text(stream, context)
        if term_text is None:
            return unify(term_arg, Atom("end_of_file"), subst)

        cleaned = term_text.strip()
        if cleaned.endswith("."):
            cleaned = cleaned[:-1].strip()

        try:
            parser = PrologParser()
            parsed_term = parser.parse_term(cleaned, context)
            return unify(term_arg, parsed_term, subst)
        except (ValueError, LarkError, PrologThrow) as exc:
            if isinstance(exc, PrologThrow):
                raise exc
            error_term = PrologError.syntax_error(str(exc), context)
            raise PrologThrow(error_term)

    @staticmethod
    def _read_term_with_options(
        stream: Stream, term_arg: Any, options_arg: Any, subst: Substitution, context: str
    ) -> Substitution | None:
        """Read term with options support for read_term/2-3."""

        # Parse options
        options_term = deref(options_arg, subst)
        if not isinstance(options_term, List):
            error_term = PrologError.type_error("list", options_term, context)
            raise PrologThrow(error_term)

        # Extract option values
        variable_names = False
        variables = False
        singletons = False

        for opt in options_term.elements:
            opt = deref(opt, subst)
            if isinstance(opt, Compound):
                if opt.functor == "variable_names" and len(opt.args) == 1:
                    variable_names = True
                    var_names_var = opt.args[0]
                elif opt.functor == "variables" and len(opt.args) == 1:
                    variables = True
                    vars_var = opt.args[0]
                elif opt.functor == "singletons" and len(opt.args) == 1:
                    singletons = True
                    singletons_var = opt.args[0]
                else:
                    error_term = PrologError.domain_error("read_option", opt, context)
                    raise PrologThrow(error_term)
            else:
                error_term = PrologError.domain_error("read_option", opt, context)
                raise PrologThrow(error_term)

        # Read the term
        term_text = IOBuiltins._read_term_text(stream, context)
        if term_text is None:
            return unify(term_arg, Atom("end_of_file"), subst)

        cleaned = term_text.strip()
        if cleaned.endswith("."):
            cleaned = cleaned[:-1].strip()

        try:
            parser = PrologParser()
            parsed_term = parser.parse_term(cleaned, context)

            # Collect variable information
            all_vars = collect_vars_in_order(parsed_term, subst)

            # Apply options
            new_subst = unify(term_arg, parsed_term, subst)
            if new_subst is None:
                return None

            if variable_names:
                # Create variable name mappings: Name=Var
                var_name_pairs = []
                for var_name in all_vars:
                    var_term = Variable(var_name)
                    pair = Compound("=", (Atom(var_name), var_term))
                    var_name_pairs.append(pair)
                var_names_list = python_to_list(var_name_pairs)
                new_subst = unify(var_names_var, var_names_list, new_subst)
                if new_subst is None:
                    return None

            if variables:
                # List of all variables in order
                var_terms = [Variable(name) for name in all_vars]
                vars_list = python_to_list(var_terms)
                new_subst = unify(vars_var, vars_list, new_subst)
                if new_subst is None:
                    return None

            if singletons:
                # Variables that appear only once
                var_counts = {}
                def count_vars(term):
                    term = deref(term, new_subst)
                    if isinstance(term, Variable):
                        var_counts[term.name] = var_counts.get(term.name, 0) + 1
                    elif isinstance(term, Compound):
                        for arg in term.args:
                            count_vars(arg)
                    elif isinstance(term, List):
                        for elem in term.elements:
                            count_vars(elem)
                        if term.tail:
                            count_vars(term.tail)

                count_vars(parsed_term)
                singleton_vars = [Variable(name) for name, count in var_counts.items() if count == 1]
                singletons_list = python_to_list(singleton_vars)
                new_subst = unify(singletons_var, singletons_list, new_subst)
                if new_subst is None:
                    return None

            return new_subst

        except (ValueError, LarkError, PrologThrow) as exc:
            if isinstance(exc, PrologThrow):
                raise exc
            error_term = PrologError.syntax_error(str(exc), context)
            raise PrologThrow(error_term)

    @staticmethod
    def _builtin_read(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        if engine is None:
            return None

        term_arg = args[0]
        current_input = getattr(engine, '_current_input_stream', USER_INPUT_STREAM)
        stream = engine.get_stream(current_input)
        if stream is None:
            error_term = PrologError.existence_error("stream", current_input, "read/1")
            raise PrologThrow(error_term)

        if stream.mode not in ("read", "append"):
            error_term = PrologError.permission_error("input", "stream", stream.handle, "read/1")
            raise PrologThrow(error_term)

        return IOBuiltins._read_and_unify_stream(stream, term_arg, subst, "read/1")

    @staticmethod
    def _builtin_read_from_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        if engine is None:
            return None

        stream_term, term_arg = args

        engine._check_instantiated(stream_term, subst, "read/2")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "read/2")

        stream_term = deref(stream_term, subst)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "read/2")
            raise PrologThrow(error_term)

        if stream.mode not in ("read", "append"):
            error_term = PrologError.permission_error("input", "stream", stream_term, "read/2")
            raise PrologThrow(error_term)

        return IOBuiltins._read_and_unify_stream(stream, term_arg, subst, "read/2")

    @staticmethod
    def _builtin_open_with_options(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """open/4 - Open file with additional options."""
        if engine is None:
            return None

        filename_term, mode_term, stream_var, options_term = args

        # Validate arguments
        engine._check_instantiated(filename_term, subst, "open/4")
        engine._check_type(filename_term, Atom, "atom", subst, "open/4")
        engine._check_instantiated(mode_term, subst, "open/4")
        engine._check_type(mode_term, Atom, "atom", subst, "open/4")
        engine._check_instantiated(options_term, subst, "open/4")

        # Get values
        filename_term = deref(filename_term, subst)
        mode_term = deref(mode_term, subst)
        options_term = deref(options_term, subst)

        filename = filename_term.name
        mode = mode_term.name

        # Validate mode
        if mode not in ('read', 'write', 'append'):
            error_term = PrologError.domain_error("io_mode", mode_term, "open/4")
            raise PrologThrow(error_term)

        # Parse options (for now, ignore them as they're not implemented)
        if not isinstance(options_term, List):
            error_term = PrologError.type_error("list", options_term, "open/4")
            raise PrologThrow(error_term)

        # For now, delegate to open/3 (options ignored)
        return IOBuiltins._builtin_open((filename_term, mode_term, stream_var), subst, engine)

    @staticmethod
    def _builtin_close_with_options(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """close/2 - Close stream with options."""
        if engine is None:
            return None

        stream_term, options_term = args

        engine._check_instantiated(stream_term, subst, "close/2")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "close/2")
        engine._check_instantiated(options_term, subst, "close/2")

        # Parse options (for now, ignore them as they're not implemented)
        options_term = deref(options_term, subst)
        if not isinstance(options_term, List):
            error_term = PrologError.type_error("list", options_term, "close/2")
            raise PrologThrow(error_term)

        # For now, delegate to close/1 (options ignored)
        return IOBuiltins._builtin_close((stream_term,), subst, engine)

    @staticmethod
    def _builtin_read_term(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """read_term/2 - Read term from current input with options."""
        if engine is None:
            return None

        term_arg, options_arg = args

        # Check options is instantiated
        engine._check_instantiated(options_arg, subst, "read_term/2")

        stream = engine.get_stream(USER_INPUT_STREAM)
        if stream is None:
            error_term = PrologError.existence_error("stream", USER_INPUT_STREAM, "read_term/2")
            raise PrologThrow(error_term)

        if stream.mode not in ("read", "append"):
            error_term = PrologError.permission_error("input", "stream", stream.handle, "read_term/2")
            raise PrologThrow(error_term)

        return IOBuiltins._read_term_with_options(stream, term_arg, options_arg, subst, "read_term/2")

    @staticmethod
    def _builtin_read_term_from_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """read_term/3 - Read term from specified stream with options."""
        if engine is None:
            return None

        stream_term, term_arg, options_arg = args

        engine._check_instantiated(stream_term, subst, "read_term/3")
        engine._check_instantiated(options_arg, subst, "read_term/3")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "read_term/3")

        stream_term = deref(stream_term, subst)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "read_term/3")
            raise PrologThrow(error_term)

        if stream.mode not in ("read", "append"):
            error_term = PrologError.permission_error("input", "stream", stream_term, "read_term/3")
            raise PrologThrow(error_term)

        return IOBuiltins._read_term_with_options(stream, term_arg, options_arg, subst, "read_term/3")

    @staticmethod
    def _builtin_open(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """open/3 - Open a file stream.

        open(FileName, Mode, Stream)
        Opens FileName in the specified Mode and unifies Stream with the stream handle.

        Modes: 'read', 'write', 'append'
        """
        if engine is None:
            return None

        filename_term, mode_term, stream_var = args

        # Validate argument types
        engine._check_instantiated(filename_term, subst, "open/3")
        engine._check_type(filename_term, Atom, "atom", subst, "open/3")
        engine._check_instantiated(mode_term, subst, "open/3")
        engine._check_type(mode_term, Atom, "atom", subst, "open/3")

        # Arguments are valid, now get their Python values
        filename_term = deref(filename_term, subst)
        mode_term = deref(mode_term, subst)

        filename = filename_term.name
        mode = mode_term.name

        # Validate mode
        if mode not in ('read', 'write', 'append'):
            # Domain error for invalid mode
            error_term = PrologError.domain_error("io_mode", mode_term, "open/3")
            raise PrologThrow(error_term)

        # Convert mode to Python file mode
        python_mode = {'read': 'r', 'write': 'w', 'append': 'a'}[mode]

        def _try_open(path: str):
            return open(path, python_mode, encoding='utf-8')

        def _escape_control_chars(path: str) -> str | None:
            """Re-escape control characters that may have been unescaped by the parser."""
            control_map = {
                "\n": "\\n",
                "\r": "\\r",
                "\t": "\\t",
                "\b": "\\b",
                "\f": "\\f",
                "\v": "\\v",
                "\a": "\\a",
            }
            if not any(ord(ch) < 32 for ch in path):
                return None
            return "".join(control_map.get(ch, f"\\x{ord(ch):02x}") if ord(ch) < 32 else ch for ch in path)

        file_obj = None
        actual_filename = filename
        try:
            # Try to open the file
            file_obj = _try_open(actual_filename)
        except OSError as exc:
            # On Windows paths embedded in quoted atoms can carry escaped control
            # characters that were unescaped by the parser (e.g., \t -> tab).
            # Retry with control characters re-escaped to recover the original path.
            escaped = _escape_control_chars(actual_filename)
            if escaped is not None and escaped != filename:
                try:
                    file_obj = _try_open(escaped)
                    actual_filename = escaped
                except OSError as fallback_exc:
                    exc = fallback_exc
            if file_obj is None:
                if isinstance(exc, FileNotFoundError):
                    # Existence error for source_sink
                    error_term = PrologError.existence_error("source_sink", filename_term, "open/3")
                    raise PrologThrow(error_term)
                if isinstance(exc, PermissionError):
                    # Permission error
                    error_term = PrologError.permission_error("open", "source_sink", filename_term, "open/3")
                    raise PrologThrow(error_term)
                raise exc
        # Note: Do not catch generic OSError outside this block to avoid masking IO errors.

        # Generate unique stream handle
        stream_handle = engine._generate_stream_handle()

        # Create and register stream
        stream = Stream(handle=stream_handle, file_obj=file_obj, mode=mode, filename=actual_filename)
        # Register into the engine's stream registry (add_stream is the public API)
        engine.add_stream(stream)

        # Unify the stream variable with the handle
        return unify(stream_var, stream_handle, subst)

    @staticmethod
    def _builtin_close(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """close/1 - Close a stream.

        close(Stream)
        Closes the specified stream and removes it from the active streams.
        """
        if engine is None:
            return None

        stream_term = args[0]

        engine._check_instantiated(stream_term, subst, "close/1")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "close/1")

        stream_term = deref(stream_term, subst)

        # Check if it's a standard stream - these cannot be closed
        if stream_term.name in ("user_input", "user_output", "user_error"):
            # Existence error for stream (ISO says standard streams don't exist for closing)
            error_term = PrologError.existence_error("stream", stream_term, "close/1")
            raise PrologThrow(error_term)

        # Get the stream from registry
        stream = engine.get_stream(stream_term)
        if stream is None:
            # Existence error for stream
            error_term = PrologError.existence_error("stream", stream_term, "close/1")
            raise PrologThrow(error_term)

        # Close the stream
        stream.close()

        # Remove from registry
        engine.remove_stream(stream_term)

        return subst

    @staticmethod
    def _builtin_get_char(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """get_char/1 - Read a character from current input stream.

        get_char(Char)
        Reads a single character from the current input stream and unifies it with Char.
        Returns 'end_of_file' on EOF.
        """
        if engine is None:
            return None

        char_var = args[0]
        stream = engine.get_stream(USER_INPUT_STREAM)
        if stream is None:
            error_term = PrologError.existence_error("stream", USER_INPUT_STREAM, "get_char/1")
            raise PrologThrow(error_term)

        if stream.mode not in ("read", "append"):
            error_term = PrologError.permission_error("input", "stream", stream.handle, "get_char/1")
            raise PrologThrow(error_term)

        return IOBuiltins._read_char_from_stream(stream, char_var, subst, "get_char/1")

    @staticmethod
    def _builtin_get_char_from_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """get_char/2 - Read a character from specified stream.

        get_char(Stream, Char)
        Reads a single character from Stream and unifies it with Char.
        Returns 'end_of_file' on EOF.
        """
        if engine is None:
            return None

        stream_term, char_var = args

        engine._check_instantiated(stream_term, subst, "get_char/2")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "get_char/2")

        stream_term = deref(stream_term, subst)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "get_char/2")
            raise PrologThrow(error_term)

        if stream.mode not in ("read", "append"):
            error_term = PrologError.permission_error("input", "stream", stream_term, "get_char/2")
            raise PrologThrow(error_term)

        return IOBuiltins._read_char_from_stream(stream, char_var, subst, "get_char/2")

    @staticmethod
    def _read_char_from_stream(
        stream: Stream, char_var: Any, subst: Substitution, context: str
    ) -> Substitution | None:
        """Helper to read a single character from a stream."""
        try:
            # Check pushback buffer first
            if stream.pushback_buffer:
                ch = stream.pushback_buffer.pop()
            else:
                ch = stream.file_obj.read(1)

            if ch == "":
                # EOF
                return unify(char_var, Atom("end_of_file"), subst)
            else:
                # Return single character as atom
                return unify(char_var, Atom(ch), subst)
        except (OSError, IOError) as e:
            # Handle I/O errors
            error_term = PrologError.permission_error("input", "stream", stream.handle, context)
            raise PrologThrow(error_term)

    @staticmethod
    def _builtin_put_char(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """put_char/1 - Write a character to current output stream.

        put_char(Char)
        Writes a single character Char to the current output stream.
        """
        if engine is None:
            return None

        char_term = args[0]

        engine._check_instantiated(char_term, subst, "put_char/1")

        char_term = deref(char_term, subst)

        # Validate that it's a single character atom
        if not isinstance(char_term, Atom):
            error_term = PrologError.type_error("in_character", char_term, "put_char/1")
            raise PrologThrow(error_term)

        if len(char_term.name) != 1:
            error_term = PrologError.type_error("in_character", char_term, "put_char/1")
            raise PrologThrow(error_term)

        stream = engine.get_stream(USER_OUTPUT_STREAM)
        if stream is None:
            error_term = PrologError.existence_error("stream", USER_OUTPUT_STREAM, "put_char/1")
            raise PrologThrow(error_term)

        if stream.mode not in ("write", "append"):
            error_term = PrologError.permission_error("output", "stream", stream.handle, "put_char/1")
            raise PrologThrow(error_term)

        return IOBuiltins._write_char_to_stream(stream, char_term.name, "put_char/1")

    @staticmethod
    def _builtin_put_char_to_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """put_char/2 - Write a character to specified stream.

        put_char(Stream, Char)
        Writes a single character Char to Stream.
        """
        if engine is None:
            return None

        stream_term, char_term = args

        engine._check_instantiated(stream_term, subst, "put_char/2")
        engine._check_instantiated(char_term, subst, "put_char/2")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "put_char/2")

        stream_term = deref(stream_term, subst)
        char_term = deref(char_term, subst)

        # Validate that it's a single character atom
        if not isinstance(char_term, Atom):
            error_term = PrologError.type_error("in_character", char_term, "put_char/2")
            raise PrologThrow(error_term)

        if len(char_term.name) != 1:
            error_term = PrologError.type_error("in_character", char_term, "put_char/2")
            raise PrologThrow(error_term)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "put_char/2")
            raise PrologThrow(error_term)

        if stream.mode not in ("write", "append"):
            error_term = PrologError.permission_error("output", "stream", stream_term, "put_char/2")
            raise PrologThrow(error_term)

        return IOBuiltins._write_char_to_stream(stream, char_term.name, "put_char/2")

    @staticmethod
    def _builtin_set_input(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """set_input/1 - Change current input stream."""
        if engine is None:
            return None

        stream_term = args[0]

        engine._check_instantiated(stream_term, subst, "set_input/1")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "set_input/1")

        stream_term = deref(stream_term, subst)

        # Check if the stream exists
        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "set_input/1")
            raise PrologThrow(error_term)

        # Check if it's an input stream
        if stream.mode not in ("read", "append"):
            error_term = PrologError.permission_error("input", "stream", stream_term, "set_input/1")
            raise PrologThrow(error_term)

        # Set as current input stream
        engine._current_input_stream = stream_term
        return subst

    @staticmethod
    def _builtin_set_output(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """set_output/1 - Change current output stream."""
        if engine is None:
            return None

        stream_term = args[0]

        engine._check_instantiated(stream_term, subst, "set_output/1")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "set_output/1")

        stream_term = deref(stream_term, subst)

        # Check if the stream exists
        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "set_output/1")
            raise PrologThrow(error_term)

        # Check if it's an output stream
        if stream.mode not in ("write", "append"):
            error_term = PrologError.permission_error("output", "stream", stream_term, "set_output/1")
            raise PrologThrow(error_term)

        # Set as current output stream
        engine._current_output_stream = stream_term
        return subst

    @staticmethod
    def _builtin_flush_output(
        _args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """flush_output/0 - Flush current output stream buffer."""
        if engine is None:
            return None

        current_output = getattr(engine, '_current_output_stream', USER_OUTPUT_STREAM)
        stream = engine.get_stream(current_output)
        if stream is None:
            error_term = PrologError.existence_error("stream", current_output, "flush_output/0")
            raise PrologThrow(error_term)

        try:
            stream.file_obj.flush()
        except (OSError, IOError) as e:
            error_term = PrologError.permission_error("output", "stream", stream.handle, "flush_output/0")
            raise PrologThrow(error_term)

        return subst

    @staticmethod
    def _builtin_flush_output_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """flush_output/1 - Flush specified stream buffer."""
        if engine is None:
            return None

        stream_term = args[0]

        engine._check_instantiated(stream_term, subst, "flush_output/1")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "flush_output/1")

        stream_term = deref(stream_term, subst)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "flush_output/1")
            raise PrologThrow(error_term)

        if stream.mode not in ("write", "append"):
            error_term = PrologError.permission_error("output", "stream", stream_term, "flush_output/1")
            raise PrologThrow(error_term)

        try:
            stream.file_obj.flush()
        except (OSError, IOError) as e:
            error_term = PrologError.permission_error("output", "stream", stream_term, "flush_output/1")
            raise PrologThrow(error_term)

        return subst

    @staticmethod
    def _is_at_eof(stream: Stream) -> bool:
        """Private helper to determine if a stream is at EOF, accounting for peek/seek/dunno-what-backs."""
        try:
            if hasattr(stream.file_obj, 'peek'):
                peeked = stream.file_obj.peek(1)
                return len(peeked) == 0
            elif hasattr(stream.file_obj, 'tell') and hasattr(stream.file_obj, 'read'):
                pos = stream.file_obj.tell()
                ch = stream.file_obj.read(1)
                at_eof = len(ch) == 0
                if not at_eof:
                    stream.file_obj.seek(pos)
                    stream.pushback_buffer.append(ch)
                return at_eof
        except (OSError, IOError):
            return False
        return False

    def _builtin_at_end_of_stream(
        _args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """at_end_of_stream/0 - Test if current input is at EOF."""
        if engine is None:
            return None

        current_input = getattr(engine, '_current_input_stream', USER_INPUT_STREAM)
        stream = engine.get_stream(current_input)
        if stream is None:
            error_term = PrologError.existence_error("stream", current_input, "at_end_of_stream/0")
            raise PrologThrow(error_term)

        if stream.mode not in ("read", "append"):
            error_term = PrologError.permission_error("input", "stream", stream.handle, "at_end_of_stream/0")
            raise PrologThrow(error_term)

        try:
            at_eof = IOBuiltins._is_at_eof(stream)
            return subst if at_eof else None
        except (OSError, IOError):
            return None

    @staticmethod
    def _builtin_stream_property(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """stream_property/2 - Query stream properties (can backtrack over all streams)."""
        if engine is None:
            return None

        stream_term, property_term = args

        # Get all streams
        all_streams = list(engine._streams.values())

        for stream in all_streams:
            # Try to unify stream
            stream_subst = unify(stream_term, stream.handle, subst)
            if stream_subst is None:
                continue

            # Extract properties
            properties = []

            # type property
            if stream.mode in ("read", "append"):
                properties.append(Compound("type", (Atom("text"),)))
            else:
                properties.append(Compound("type", (Atom("text"),)))  # Default to text for now

            # mode property
            properties.append(Compound("mode", (Atom(stream.mode),)))

            # alias property (if it's a standard stream)
            if stream.handle.name in ("user_input", "user_output", "user_error"):
                properties.append(Compound("alias", (stream.handle,)))

            # position property (if seekable)
            if hasattr(stream.file_obj, 'tell'):
                try:
                    pos = stream.file_obj.tell()
                    properties.append(Compound("position", (Number(pos),)))
                except (OSError, IOError):
                    pass

            # end_of_stream property
            try:
                at_eof = IOBuiltins._is_at_eof(stream)
                if at_eof:
                    properties.append(Compound("end_of_stream", (Atom("at"),)))
                else:
                    properties.append(Compound("end_of_stream", (Atom("not"),)))
            except (OSError, IOError):
                properties.append(Compound("end_of_stream", (Atom("not"),)))

            # eof_action property (default to error for now)
            properties.append(Compound("eof_action", (Atom("error"),)))

            # reposition property (can seek)
            can_seek = hasattr(stream.file_obj, 'seek') and hasattr(stream.file_obj, 'tell')
            properties.append(Compound("reposition", (Atom("true") if can_seek else Atom("false"),)))

            # file_name property (if it's a file)
            if stream.filename:
                properties.append(Compound("file_name", (Atom(stream.filename),)))

            # Try to unify with each property
            for prop in properties:
                prop_subst = unify(property_term, prop, stream_subst)
                if prop_subst is not None:
                    return prop_subst

        return None

    @staticmethod
    def _builtin_set_stream_position(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """set_stream_position/2 - Seek to position in stream."""
        if engine is None:
            return None

        stream_term, position_term = args

        engine._check_instantiated(stream_term, subst, "set_stream_position/2")
        engine._check_instantiated(position_term, subst, "set_stream_position/2")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "set_stream_position/2")

        stream_term = deref(stream_term, subst)
        position_term = deref(position_term, subst)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "set_stream_position/2")
            raise PrologThrow(error_term)

        # Check if stream supports seeking
        if not hasattr(stream.file_obj, 'seek'):
            error_term = PrologError.permission_error("reposition", "stream", stream_term, "set_stream_position/2")
            raise PrologThrow(error_term)

        # Validate position
        if not isinstance(position_term, Number) or not isinstance(position_term.value, int) or position_term.value < 0:
            error_term = PrologError.domain_error("stream_position", position_term, "set_stream_position/2")
            raise PrologThrow(error_term)

        try:
            stream.file_obj.seek(position_term.value)
        except (OSError, IOError, ValueError) as e:
            error_term = PrologError.domain_error("stream_position", position_term, "set_stream_position/2")
            raise PrologThrow(error_term)

        return subst

    @staticmethod
    def _builtin_at_end_of_stream_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """at_end_of_stream/1 - Test if specified stream is at EOF."""
        if engine is None:
            return None

        stream_term = args[0]

        engine._check_instantiated(stream_term, subst, "at_end_of_stream/1")
        engine._check_type(stream_term, Atom, "stream_or_alias", subst, "at_end_of_stream/1")

        stream_term = deref(stream_term, subst)

        stream = engine.get_stream(stream_term)
        if stream is None:
            error_term = PrologError.existence_error("stream", stream_term, "at_end_of_stream/1")
            raise PrologThrow(error_term)

        if stream.mode not in ("read", "append"):
            error_term = PrologError.permission_error("input", "stream", stream_term, "at_end_of_stream/1")
            raise PrologThrow(error_term)

        try:
            at_eof = IOBuiltins._is_at_eof(stream)
            return subst if at_eof else None
        except (OSError, IOError):
            return None

    @staticmethod
    def _builtin_writeq(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """writeq/1 - Write term with atoms quoted when necessary."""
        if engine is None:
            return None

        term = args[0]
        # Delegate to write_term with quoted(true)
        options = List([Compound("quoted", (Atom("true"),))])
        return IOBuiltins._builtin_write_term((term, options), subst, engine)

    @staticmethod
    def _builtin_writeq_to_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """writeq/2 - Write term with quotes to specified stream."""
        if engine is None:
            return None

        stream_term, term = args
        # Delegate to write_term with quoted(true)
        options = List([Compound("quoted", (Atom("true"),))])
        return IOBuiltins._builtin_write_term_to_stream((stream_term, term, options), subst, engine)

    @staticmethod
    def _builtin_write_canonical(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """write_canonical/1 - Write term in canonical form."""
        if engine is None:
            return None

        term = args[0]
        # Delegate to write_term with quoted(true) and ignore_ops(true)
        options = List([
            Compound("quoted", (Atom("true"),)),
            Compound("ignore_ops", (Atom("true"),))
        ])
        return IOBuiltins._builtin_write_term((term, options), subst, engine)

    @staticmethod
    def _builtin_write_canonical_to_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """write_canonical/2 - Write term canonically to specified stream."""
        if engine is None:
            return None

        stream_term, term = args
        # Delegate to write_term with quoted(true) and ignore_ops(true)
        options = List([
            Compound("quoted", (Atom("true"),)),
            Compound("ignore_ops", (Atom("true"),))
        ])
        return IOBuiltins._builtin_write_term_to_stream((stream_term, term, options), subst, engine)

    @staticmethod
    def _builtin_print(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """print/1 - Pretty-print term."""
        if engine is None:
            return None

        term = args[0]
        # For now, delegate to write/1 (hook support can be added later)
        return IOBuiltins._builtin_write((term,), subst, engine)

    @staticmethod
    def _builtin_print_to_stream(
        args: BuiltinArgs, subst: Substitution, engine: EngineContext | None
    ) -> Substitution | None:
        """print/2 - Pretty-print to specified stream."""
        # Delegation recommended by review to avoid duplication
        return IOBuiltins._builtin_write_to_stream(args, subst, engine)

    @staticmethod
    def _write_char_to_stream(stream: Stream, char: str, context: str) -> Substitution | None:
        """Helper to write a single character to a stream."""
        try:
            stream.file_obj.write(char)
            stream.file_obj.flush()  # Ensure immediate output
            return {}
        except (OSError, IOError) as e:
            # Handle I/O errors
            error_term = PrologError.permission_error("output", "stream", stream.handle, context)
            raise PrologThrow(error_term)


__all__ = ["IOBuiltins"]
