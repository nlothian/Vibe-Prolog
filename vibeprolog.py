#!/usr/bin/env python3
"""Prolog CLI - A command line utility for running Prolog programs."""

import argparse
import sys
from pathlib import Path

from vibeprolog import PrologInterpreter
from vibeprolog.interpreter import clear_ast_caches


def load_program(prolog: PrologInterpreter, filename: str, verbose: bool = False) -> bool:
    """Load a Prolog program from a file.

    Args:
        prolog: The Prolog interpreter instance
        filename: Path to the Prolog file
        verbose: Whether to print verbose output

    Returns:
        True if successful, False otherwise
    """
    file_path = Path(filename)

    if not file_path.exists():
        print(f"Error: File '{filename}' not found", file=sys.stderr)
        return False

    if not file_path.is_file():
        print(f"Error: '{filename}' is not a file", file=sys.stderr)
        return False

    try:
        if verbose:
            print(f"Loading program from '{filename}'...")

        with open(file_path, 'r') as f:
            program = f.read()

        prolog.consult_string(program)

        if verbose:
            print(f"Successfully loaded '{filename}'")

        return True

    except Exception as e:
        print(f"Error loading program: {e}", file=sys.stderr)
        return False


def execute_query(prolog: PrologInterpreter, query: str, once: bool = False, verbose: bool = False, show_bindings: bool = False) -> int:
    """Execute a single query and print results.

    Args:
        prolog: The Prolog interpreter instance
        query: The query string to execute
        once: Whether to stop after first solution
        verbose: Whether to print verbose output
        show_bindings: Whether to always show variable bindings (even when output was produced)

    Returns:
        0 if query succeeded, 1 if failed
    """
    # Ensure query ends with period
    if not query.strip().endswith('.'):
        query = query.strip() + '.'

    try:
        if verbose:
            print(f"Query: {query}")

        if once:
            result, had_output = prolog.query_once(query, capture_output=True)
            if result is not None:
                # Only show bindings if: show_bindings flag OR no output was produced
                should_show = show_bindings or not had_output

                if result:  # Has bindings
                    if should_show:
                        for var, value in sorted(result.items()):
                            print(f"{var} = {format_value(value)}")
                else:
                    if should_show:
                        print("true.")
                return 0
            else:
                print("false.")
                return 1
        else:
            results, had_output = prolog.query(query, capture_output=True)
            if results:
                # Only show bindings if: show_bindings flag OR no output was produced
                should_show = show_bindings or not had_output

                for i, result in enumerate(results, 1):
                    if result:  # Has bindings
                        if should_show:
                            if len(results) > 1:
                                print(f"Solution {i}:")
                            for var, value in sorted(result.items()):
                                print(f"{var} = {format_value(value)}")
                            if len(results) > 1:
                                print()
                    else:
                        if should_show:
                            print("true.")
                return 0
            else:
                print("false.")
                return 1

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
    except Exception as e:
        print(f"Error executing query: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


def format_value(value) -> str:
    """Format a Prolog value for display."""
    if isinstance(value, list):
        return '[' + ', '.join(format_value(v) for v in value) + ']'
    elif isinstance(value, tuple):
        if len(value) == 2 and value[0] not in ['_var', '_compound']:
            # Looks like a functor
            return f"{value[0]}({', '.join(format_value(v) for v in value[1:])})"
        return str(value)
    else:
        return str(value)


def interactive_mode(prolog: PrologInterpreter, verbose: bool = False):
    """Start an interactive REPL for queries.

    Args:
        prolog: The Prolog interpreter instance
        verbose: Whether to print verbose output
    """
    print("Prolog Interactive Mode")
    print("Enter queries ending with '.' or 'quit.' to exit")
    print()

    while True:
        try:
            # Read query
            query = input("?- ").strip()

            if not query:
                continue

            # Check for exit commands
            if query in ['quit.', 'exit.', 'halt.', 'quit', 'exit', 'halt']:
                print("Goodbye!")
                break

            # Execute query
            execute_query(prolog, query, once=False, verbose=verbose)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if verbose:
                import traceback
                traceback.print_exc()


def main():
    """Main entry point for the Prolog CLI."""
    parser = argparse.ArgumentParser(
        description="Prolog CLI - Run Prolog programs from the command line",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start interactive mode without loading a file
  %(prog)s

  # Load a program and start interactive mode
  %(prog)s examples.pl

  # Execute a specific query without a file
  %(prog)s -q "member(X, [1,2,3])"

  # Execute a specific query with a loaded program
  %(prog)s examples.pl -q "member(X, [1,2,3])"

  # Get only the first solution
  %(prog)s examples.pl -q "member(X, [1,2,3])" --once

  # Verbose mode
  %(prog)s examples.pl -q "parent(X, Y)" -v

  # Pass arguments to Prolog program
  %(prog)s program.pl arg1 arg2 arg3
        """
    )

    parser.add_argument(
        'file',
        nargs='?',
        help='Prolog program file to load (.pl) - optional for interactive mode'
    )

    parser.add_argument(
        'program_args',
        nargs='*',
        help='Arguments to pass to the Prolog program'
    )

    parser.add_argument(
        '-q', '--query',
        help='Execute a specific query and exit',
        metavar='QUERY'
    )

    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Start interactive mode (default if no query specified)'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Only find the first solution (use with --query)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--show-bindings',
        action='store_true',
        help='Always show variable bindings even when query produces output (default: suppress bindings when output is produced)'
    )

    parser.add_argument(
        '--builtin-conflict',
        choices=['skip', 'error', 'shadow'],
        default='skip',
        help='How to handle library definitions that conflict with built-in predicates: '
             'skip (default) silently keeps the built-in, '
             'error raises permission_error, '
             'shadow lets modules override built-ins within their namespace while user scope keeps the built-in'
    )

    parser.add_argument(
        '--clear-ast-cache',
        action='store_true',
        help='Clear cached AST artifacts before running the interpreter'
    )

    args = parser.parse_args()

    # Shadow mode is now implemented

    if args.clear_ast_cache:
        clear_ast_caches()

    # Create interpreter
    prolog = PrologInterpreter(argv=args.program_args, builtin_conflict=args.builtin_conflict)

    # Load the program if a file was provided
    if args.file:
        if not load_program(prolog, args.file, args.verbose):
            return 1

    # Execute query or start interactive mode
    if args.query:
        return execute_query(prolog, args.query, args.once, args.verbose, args.show_bindings)
    else:
        # Default to interactive mode
        interactive_mode(prolog, args.verbose)
        return 0


if __name__ == "__main__":
    sys.exit(main())
