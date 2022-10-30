"""ConMan's command line utilities.

This module hosts the main argument parser object which allows user to
interact with ConMan's services over the command line.

Usage Example
-------------

    $ python3 -c "import conman; conman.cli.main()" --help

Last updated on: October 30, 2022
Last udpated by: Akshay Mestry (XAMES3) <xa@mes3.dev>
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import textwrap
import typing as t

# from . import __version__ as version
from .logger import basic_config
from .logger import configure_logger
from .main import configure_docker_run
from .main import run_container

# Maximum terminal width which allows hard-wrapping of the command line
# messages and descriptions over a set length. By default, the total
# command line width is used for the messages but for the smaller
# terminal widths, it automatically soft-wraps the messages. Hence, we
# define a maximum terminal width of 79 characters to show and interact
# with the command line components.
_terminal_width: int = shutil.get_terminal_size().columns - 2
_terminal_width = _terminal_width if _terminal_width < 79 else 79


class _ConManArgumentFormatter(argparse.RawTextHelpFormatter):
    """Custom formatter for customizing command layout, usage message
    and wrapping lines.

    This class overrides the default behavior and adds custom usage
    message template. Also it sets a soft limit for wrapping the help
    and description strings.

    .. code-block:: python

        import argparse
        from conman.cli import _ConManArgumentFormatter as fmt

        parser = argparse.ArgumentParser(formatter_class=fmt)
        args = parser.parse_args()

    :param prog: Program name which acts as an entrypoint.
    :param indent_increment: Default indentation for the following
                             command line text, defaults to ``2``.
    :param max_help_position: Distance between command line arguments
                              and its description, defaults to ``50``.
                              This default value of 50 is forced to use
                              instead of 24.
    :param width: Maximum width of the command line messages, defaults
                  to ``None``.

    .. note::

        Be warned, by accessing names starting with an underscore you
        are venturing into the undocumented private API of the module,
        and your code may break in future updates.

    """

    def __init__(
        self,
        prog: str,
        indent_increment: int = 2,
        max_help_position: int = 50,
        width: t.Optional[int] = None,
    ) -> None:
        """Update the ``max_help_position`` to accomodate metavar."""
        super().__init__(prog, indent_increment, max_help_position, width)

    # See https://stackoverflow.com/a/35848313/14316408 for customizing
    # the usage section when looking for help.
    def add_usage(
        self,
        usage: t.Optional[str],
        actions: t.Iterable[argparse.Action],
        groups: t.Iterable[argparse._ArgumentGroup],
        prefix: t.Optional[str] = None,
    ) -> None:
        """Capitalize the usage text."""
        if prefix is None:
            sys.stdout.write("\n")
            prefix = "Usage:\n "
        return super().add_usage(usage, actions, groups, prefix)

    # See https://stackoverflow.com/a/35925919/14316408 for adding the
    # line wrapping logic for the description.
    def _split_lines(self, text: str, _: int) -> list[str]:
        """Unwrap the lines to width of the terminal."""
        text = self._whitespace_matcher.sub(" ", text).strip()
        return textwrap.wrap(text, _terminal_width)

    # See https://stackoverflow.com/a/13429281/14316408 for hiding the
    # metavar is subcommand listing.
    def _format_action(self, action: argparse.Action) -> str:
        """Hide Metavar in command listing."""
        parts = super()._format_action(action)
        if action.nargs == argparse.PARSER:
            parts = "\n".join(parts.splitlines()[1:])
        return parts

    # See https://stackoverflow.com/a/23941599/14316408 for disabling
    # the metavar for short options.
    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Disable Metavar for short options."""
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar
        parts: list[str] = []
        if action.nargs == 0:
            parts.extend(action.option_strings)
        else:
            default = action.dest.upper()
            args_string = self._format_args(action, default)
            for option_string in action.option_strings:
                parts.append(f"{option_string}")
            parts[-1] += f" {args_string}"
        return ", ".join(parts)


def _get_prog_name() -> str:
    """Get program name.

    This is inspired by ``pip`` module.

    :return: Entrypoint program name.
    """
    try:
        prog = os.path.basename(sys.argv[0])
        if prog in ("__main__.py", "-c"):
            return f"{sys.executable} -m conman"
        return prog
    except (AttributeError, TypeError, IndexError):
        pass
    return "conman"


# TIP: Better to assign it as a variable rather than implementing any
# unnecessary caching behaviors.
prog = _get_prog_name()


def subcommand(
    subparsers: argparse._SubParsersAction,
    parents: list[argparse.ArgumentParser],
    command: str,
    title: str,
    usage: str,
    help: str,
    description: str,
    callback: t.Callable[[argparse.Namespace, list[str]], t.NoReturn],
    configure: t.Callable[[argparse.ArgumentParser], None] = None,
) -> None:
    """Create subparser or positional argument object.

    This function creates new subcommands in the main argument parser
    instance.

    :param subparsers: Subparser instance action which we are going to
                       attach to.
    :param parents: List of parent argument parser instance. Usually
                    this is nothing but another parser instance. Parent
                    parsers, needed to ensure tree structure in
                    argparse.
    :param command: Subcommand instruction.
    :param title: Title for the optional arguments.
    :param usage: Usage message for the subcommand.
    :param help: Help text for the subcommand.
    :param description: Description for the subcommand.
    :param callback: Primary subcommand callback function reference.
    :param configure: Parser configuration objects, defaults to ``None``.
    """
    parser = subparsers.add_parser(
        command,
        usage=usage,
        formatter_class=_ConManArgumentFormatter,
        conflict_handler="resolve",
        description=description,
        help=help,
        parents=parents,
        add_help=False,
    )
    if configure:
        configure(parser)
    parser._optionals.title = title
    parser.set_defaults(callback=callback)


def configure_general(
    parser: argparse.ArgumentParser | argparse._ActionsContainer,
) -> None:
    """Add general options to the parser object."""
    parser = parser.add_argument_group("General Options")
    parser.add_argument(
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Increase the logging verbosity. This option is additive, and "
            "can be used twice. The logging verbosity can be overridden by "
            "setting CONMAN_LOGGING_LEVEL (corresponding to "
            "DEBUG, INFO, WARNING, ERROR and CRITICAL logging levels)."
        ),
    )
    # See https://stackoverflow.com/a/8521644/812183 for adding version
    # specific argument to the parser.
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"ConMan v0.0.1",
        help="Show ConMan's installed version and exit.",
    )


def _create_main_parser() -> argparse.ArgumentParser:
    """Create and return the main parser object for ConMan's CLI.

    It powers the main argument parser for the ConMan module.

    :return: ArgumentParser object which stores all the properties of
             the main argument parser.
    """
    main_parser = argparse.ArgumentParser(
        prog=prog,
        usage="%(prog)s <command> [options]",
        formatter_class=_ConManArgumentFormatter,
        conflict_handler="resolve",
        add_help=False,
        description=(
            "ConMan: An easy and flexible Docker based container manager.\n\n"
            "ConMan is an open-source project that is available for the Unix "
            "platforms which is currently maintained on GitHub. ConMan is a "
            "python based wrapper for managing docker based containers and "
            "images on your Unix system."
        ),
        epilog=(
            'For specific information about a particular command, run "'
            'conman <command> --help".\nRead complete documentation at: '
            "https://github.com/xames3/conman\n\nCopyright (c) 2022 "
            "Akshay Mestry (XAMES3). All rights reserved."
        ),
    )
    main_parser._positionals.title = "Commands"
    parent_parser = argparse.ArgumentParser(add_help=False)
    for parser in (main_parser, parent_parser):
        configure_logger(parser)
        configure_general(parser)
    subparsers = main_parser.add_subparsers(prog=prog)
    parents = [parent_parser]
    subcommand(
        subparsers=subparsers,
        parents=parents,
        command="run",
        title="Run Options",
        usage=(
            "%(prog)s run [options] --image <image> --name <name> ...\n "
            "%(prog)s run [options] --image <image> ..."
        ),
        description=(
            "Run docker containers.\n\nThis command performs ``docker run`` "
            "and/or ``docker start`` under the hood to run a\nnew container "
            "or start an existing one respectively. The started containers "
            "have attached\nand open STDIN, STDOUT or STDERR by default along "
            "with pseudo-TTY allocated for the\nuser's interaction."
        ),
        help="Run docker containers.",
        configure=configure_docker_run,
        callback=run_container,
    )
    return main_parser


def main() -> int:
    """Primary application entrypoint.

    This function is called at the entrypoint, meaning that when the
    user runs this function, it will display the command line interface
    for ConMan.

    Run as standalone python application.
    """
    parser = _create_main_parser()
    args, rest = parser.parse_known_args()
    log_options = {
        "fmt": args.log_format,
        "datefmt": args.log_datefmt,
        "level": args.verbose or args.log_level,
        "filename": args.log_path,
        "max_bytes": args.max_bytes,
        "backup_count": args.backup_count,
        "skip_logging": args.no_output,
        "color": args.no_color,
    }
    logger = basic_config(**log_options)
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Start command for ConMan: {' '.join(sys.argv)}")
    if hasattr(args, "callback"):
        try:
            args.callback(args, rest)
        except UnboundLocalError:
            logger.error("No arguments passed to the command")
            return 1
    else:
        parser.print_help()
    return 0
