"""ConMan's command line utilities.

This module hosts the main argument parser object which allows user to
interact with ConMan's APIs over the command line.

Usage Example
-------------

    .. code-block:: console

        $ python3 -c "import conman; conman.cli.main()" --help

.. versionadded:: 0.1.1
    Fix text wrapping on smaller terminals by introducing a custom text
    wrapper to wrap long text messages.

.. versionadded:: 0.1.0
    Add support for dynamic version parsing and perform minor refactor
    of verbosity message.
    Add support for ``--help`` based help function.

.. versionchanged:: 0.1.0
    Refactor main parser's description to fit within terminal width. Use
    new function names.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import textwrap
import typing as t

from . import __version__ as version
from .logger import add_logging_options
from .logger import basic_config
from .main import configure_docker_run
from .main import run_container

# Maximum terminal width which allows hard-wrapping of the command line
# messages and descriptions over a set length. By default, the total
# command line width is used for the messages but for the smaller
# terminal widths, it automatically soft-wraps the messages.
_width: int = shutil.get_terminal_size().columns - 2
_width = _width if _width <= 78 else 78


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

    .. versionadded:: 0.1.1
        Fix text wrapping on smaller terminals.
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
        """Unwrap the lines to width of the terminal.

        .. versionadded:: 0.1.1
            Fix text wrapping on smaller terminals.
        """
        text = self._whitespace_matcher.sub(" ", text).strip()
        return textwrap.wrap(text, _width - 25)

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


class _TextWrapper(textwrap.TextWrapper):
    """Custom text wrapper to fix the linebreaks in the long texts.

    .. code-block:: python

        from conman.cli import _TextWrapper

        wrapper = _TextWrapper(width=80)
        wrapper.fill('Long text message more than 80 characters...')

    .. versionadded:: 0.1.1
        Added support for custom text wrapper.
    """

    # See https://stackoverflow.com/a/45287550/14316408 for help on
    # textwrapping.
    def wrap(self, text: str) -> list[str]:
        """Reformat text wrapping."""
        split_text = text.split("\n")
        lines = [
            line
            for paragraph in split_text
            for line in textwrap.TextWrapper.wrap(self, paragraph)
        ]
        return lines


_textwrap = _TextWrapper(width=_width)


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
    r"""Create subparser or positional argument object.

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

    .. versionadded:: 0.1.1
        Added support for wrapping long description, usage and help
        texts instead of forcing ``\n`` to unnaturally break the lines
        into desirable width.
    """
    parser = subparsers.add_parser(
        command,
        parents=parents,
        usage=_textwrap.fill(usage),
        description=_textwrap.fill(description),
        help=_textwrap.fill(help),
        add_help=False,
        formatter_class=_ConManArgumentFormatter,
        conflict_handler="resolve",
    )
    if configure:
        configure(parser)
    parser._optionals.title = title
    parser.set_defaults(callback=callback)


def add_general_options(
    parser: argparse.ArgumentParser | argparse._ActionsContainer,
) -> None:
    """Add general options to the parser object.

    :param parser: Parser instance to which the general options are
                   supposed to be added to.

    .. versionadded:: 0.1.0
        Add support for dynamic version parsing and perform minor
        refactor of verbosity message.
    """
    options = parser.add_argument_group("General Options")
    options.add_argument(
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message.",
    )
    options.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=(
            "Increase the logging verbosity. This option is additive, and "
            "can be used twice."
        ),
    )
    # See https://stackoverflow.com/a/8521644/812183 for adding version
    # specific argument to the parser.
    options.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"ConMan v{version}",
        help="Show ConMan's installed version and exit.",
    )


def create_main_parser() -> argparse.ArgumentParser:
    """Create and return the main parser object for ConMan's CLI.

    It powers the main argument parser for the ConMan module.

    :return: ArgumentParser object which stores all the properties of
             the main argument parser.

    .. versionadded:: 0.1.1
        Add support for text wrapping long text messages.

    .. versionchanged:: 0.1.0
        Refactor main parser's description to fit within terminal width.
        Use new function names.
    """
    main_parser = argparse.ArgumentParser(
        prog=prog,
        usage="%(prog)s <command> [options]",
        formatter_class=_ConManArgumentFormatter,
        conflict_handler="resolve",
        add_help=False,
        description=_textwrap.fill(
            "ConMan: An easy and flexible Docker based container manager.\n\n"
            "ConMan is an open-source project that is available for the Unix "
            "platforms which is currently maintained on GitHub. ConMan is a "
            "python based wrapper for managing docker based containers and "
            "images on your Unix system.",
        ),
        epilog=_textwrap.fill(
            'For information about a particular command, run "conman '
            '<command> --help". Read complete documentation at: '
            "https://github.com/xames3/conman.",
        ),
    )
    main_parser._positionals.title = "Commands"
    parent_parser = argparse.ArgumentParser(add_help=False)
    for parser in (main_parser, parent_parser):
        add_logging_options(parser)
        add_general_options(parser)
    subparsers = main_parser.add_subparsers(prog=prog)
    parents = [parent_parser]
    subcommand(
        subparsers=subparsers,
        parents=parents,
        command="run",
        title="Run Options",
        usage=(
            "%(prog)s [options] --image <image> --name <name> ...\n "
            "%(prog)s [options] --image <image> ..."
        ),
        description=(
            "Run docker containers.\n\nThis command performs `docker run` "
            "and/or `docker start` under the hood to run a new container "
            "or start an existing one respectively. The started containers "
            "have attached and open STDIN, STDOUT or STDERR by default along "
            "with pseudo-TTY allocated for the user's interaction."
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

    .. versionadded:: 0.1.0
        Add support for ``--help`` based help function.
    """
    parser = create_main_parser()
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
    if len(rest) == 1 and "-h" in rest:
        # This is to avoid any conflicts with docker's existing command
        # line arguments. By default, a few of the docker commands
        # use ``-h`` for their internal working.
        sys.stderr.write("ConMan doesn't support -h, did you mean --help?\n")
        return 1
    if hasattr(args, "callback"):
        try:
            args.callback(args, rest)
        except UnboundLocalError:
            logger.error("No arguments passed to the command")
            return 1
    else:
        parser.print_help()
    return 0
