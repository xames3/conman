"""\
ConMan core API
===============

ConMan's essential abstractions that execute commands.

The ``conman.core`` module offers abstractions for running various
Docker commands from the command line. The commands are implemented
throughout the entire module in the form of various classes, with each
having a specific function. 

.. versionchanged:: 1.0.0
    Rewritten entire module from scratch to support more OO programming
    paradigms, better design pattern strategies and overcome code
    duplication [DRY].
"""

from __future__ import annotations

import abc
import argparse
import os
import subprocess
import sys
import time
import typing as t

from .logger import create_logger
from .logger import get_logger

if t.TYPE_CHECKING:
    from logging import Logger

F = t.TypeVar("F", bound="ImmutableDictMixin")
K = t.TypeVar("K")
V = t.TypeVar("V")

_log = get_logger(__name__)


def is_immutable(self: F) -> t.NoReturn:
    """Raise error when called.

    .. versionadded:: 1.0.0
    """
    raise TypeError(f"{type(self).__name__!r} objects are immutable")


class ImmutableDictMixin:
    """Make a ``dict`` object immutable.

    .. versionadded:: 1.0.0
    """

    def __delitem__(self, key: K) -> t.NoReturn:
        """Override ``__delitem__`` implementation."""
        is_immutable(self)

    def setdefault(self, key: K, default: t.Optional[V] = None) -> t.NoReturn:
        """If ``key`` is in the dictionary, return its value. If not,
        insert key with a value of ``default`` and return default. The
        ``default`` defaults to ``None``.
        """
        is_immutable(self)

    def update(self, *args: t.Any, **kwargs: V) -> t.NoReturn:
        """Update the dictionary with the key/value pairs from other,
        overwriting existing keys. Return ``None``.
        """
        is_immutable(self)

    def pop(self, key: K, default: t.Optional[V] = None) -> t.NoReturn:
        """If ``key`` is in the dictionary, remove it and return its
        value, else return ``default``. If ``default`` is not given and
        ``key`` is not in the dictionary, a KeyError is raised.
        """
        is_immutable(self)

    def popitem(self) -> t.NoReturn:
        """Remove and return a (key, value) pair from the dictionary."""
        is_immutable(self)

    def clear(self) -> t.NoReturn:
        """Remove all items from the dictionary."""
        is_immutable(self)


class ImmutableDict(ImmutableDictMixin, dict[K, V]):  # type: ignore[misc]
    """An immutable dictionary.

    .. versionadded:: 1.0.0
    """

    def __repr__(self) -> str:
        """Dictionary representation as string."""
        return f"{type(self).__name__}({dict.__repr__(self)})"

    def copy(self) -> dict[K, V]:
        """Return a shallow mutable copy of this object."""
        return dict(self)

    def __copy__(self) -> "ImmutableDict[K, V]":
        return self


_commands: ImmutableDict[str, t.Type["Command"]] = ImmutableDict()


class ConMan:
    """Base application class.

    .. code-block:: python

        import argparse
        from conman.core import ConMan

        parser = argparse.ArgumentParser()
        args, rest = parser.parse_known_args()

        app = ConMan()
        app.start()
        app.run(args, rest)

    .. versionadded:: 1.0.0
    """

    _max_attempt: int = 10

    def __init__(self) -> None:
        """Initialize docker class."""
        for command, klass in _commands.items():
            setattr(self, command, klass())

    def start(self) -> None:
        """Start docker daemon if not running."""
        _log.debug("Checking if the docker daemon is running...")
        if self.not_running:
            _log.warning("Docker daemon is not running. Starting Docker...")
            subprocess.run(["open", "--background", "-a", "Docker"])
            _attempt = 1
            while _attempt < self._max_attempt:
                if self.not_running:
                    time.sleep(2.0)
                    _attempt += 1
                else:
                    break
            _log.info("Docker daemon is running...")

    @property
    def not_running(self) -> int:
        """Check if the docker daemon is running."""
        return subprocess.run(["docker", "ps"], stderr=-3, stdout=-3).returncode

    def logger(self, **options: t.Any) -> Logger:
        """Return a logger object."""
        return create_logger(**options)


class Command(abc.ABC):
    """The base command class which implements the minimal API
    abstractions for rest of the commands.

    .. versionadded:: 1.0.0
        Added support for abstracting commands, thereby reducing code
        duplication and increasing code extension.

    :var usage: Usage of the command to show on the command line.
    :var description: Description of the command and its underlying
                      implementation/specification.
    :var help: Help text about the command.
    """

    usage: str
    description: str
    help: str

    @classmethod
    def __init_subclass__(cls) -> None:
        """Maintain record of all the commands."""
        _commands[cls.__name__.lower()] = cls

    @abc.abstractmethod
    def __call__(
        self, argv: argparse.Namespace, options: list[str]
    ) -> t.NoReturn:
        """Implement ``__call__`` implicitly."""
        raise NotImplementedError

    @abc.abstractclassmethod
    def add_options(
        cls, parser: argparse.ArgumentParser | argparse._ActionsContainer
    ) -> None:
        """Implement ``add_options`` implicitly."""
        raise NotImplementedError


class Run(Command):
    """Docker ``run`` command implementation.

    This class emulates the ``docker run`` command to spin a new docker
    container. The docker run command first creates a writable container
    layer over the specified image, and then starts it using the provided
    arguments.

    Docker runs processes in isolated containers. A container is a
    process which runs on a host. The host may be local or remote. The
    scope of this class is to run a container on the local OR host
    machine.

    When the user executes this class, it spins a docker container with
    some basic utilities in place like hostname, logging configuration
    and working directory. However, these configurations can be
    overridden if needed.

    .. versionadded:: 1.0.0
    """

    usage: str = (
        "%(prog)s [options] --image <image> --name <name> ...\n "
        "%(prog)s [options] --image <image> ..."
    )
    description: str = (
        "Run docker containers.\n\nThis command performs `docker run` "
        "and/or `docker start` under the hood to run a new container "
        "or start an existing one respectively. The started containers "
        "have attached and open STDIN, STDOUT or STDERR by default along "
        "with pseudo-TTY allocated for the user's interaction."
    )
    help: str = "Run docker containers."

    def __call__(
        self, argv: argparse.Namespace, options: list[str]
    ) -> t.NoReturn:
        """Run a docker container.

        :param argv: ArgumentParser namespace object.
        :param options: Extra docker arguments which are not natively
                        supported by this class.
        """
        if argv.image is None:
            sys.stderr.write("ConMan `run` requires --image argument.\n")
            raise SystemExit(1)
        self.name = argv.name
        if self.container_exists:
            _log.info(f"Container: {self.name!r} already exists, starting...")
            cmd = ["docker", "start", "-ia", self.name]
        else:
            if self.name is None:
                _log.info("Spawning a temporary container...")
                tmp_cmd = "--rm"
            else:
                _log.info(f"Spawning new container: {self.name!r}...")
                tmp_cmd = f"--name {self.name}"
            cmd = [
                "docker",
                "run",
                "-ti",
                *tmp_cmd.split(),
                "--hostname",
                argv.hostname,
                "--workdir",
                argv.workdir,
                *options,
                argv.image,
                argv.command,
            ]
        cmd = list(filter(None, cmd))
        _log.debug(f"Executing docker command: {' '.join(cmd)}")
        os.execvp(cmd[0], cmd)

    @property
    def container_exists(self) -> int:
        """Check if the container exists or not.

        .. versionchanged:: 1.0.0
            Return exit code 0 if name of the container is None.

        :return: Exit code of the result.
        """
        if self.name is None:
            return 0
        _log.info(f"Checking if the container: {self.name!r} exists...")
        containers = subprocess.Popen(["docker", "ps", "-a"], stdout=-1).stdout
        awk = subprocess.Popen(
            ["awk", "{if(NR>1) print $NF}"], stdin=containers, stdout=-1
        )
        if containers:
            containers.close()
        return (
            1 if self.name in awk.communicate()[0].decode().splitlines() else 0
        )

    @classmethod
    def add_options(  # type: ignore[override]
        cls, parser: argparse.ArgumentParser | argparse._ActionsContainer
    ) -> None:
        """Add options for configuring docker ``run`` command.

        This method accepts a parser object, preferrably provide a
        ``main`` parser instance.

        .. versionadded:: 1.0.0
            Added support for ``-h`` for hostname.

        :param parser: Parser instance to which the docker run options
                       are supposed to be added to.
        """
        options = parser.add_argument_group("Run Options")
        options.add_argument(
            "-c",
            "--command",
            help="Command to execute in the running container.",
            metavar="<command>",
        )
        options.add_argument(
            "-h",
            "--hostname",
            default="ConMans-Docker-Container",
            help="Container host name (Default: %(default)s).",
            metavar="<name>",
        )
        options.add_argument(
            "-n",
            "--name",
            help="Name for the container.",
            metavar="<name>",
        )
        options.add_argument(
            "-w",
            "--workdir",
            default="/tmp/code",
            help=(
                "Working directory inside the container (Default: %(default)s)."
            ),
            metavar="<path>",
        )
        options.add_argument(
            "--image",
            help="Image to be used for creating the development container.",
            metavar="<image>",
        )
