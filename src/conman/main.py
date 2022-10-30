"""Main ConMan utilities which executes commands on the CLI."""

import argparse
import os
import subprocess
import time
import typing as t

from .logger import get_logger

_daemon_wait: float = 20.0

_logger = get_logger(__name__)


def _docker_is_not_running() -> int:
    """Check if the docker daemon is running or not."""
    _logger.debug("Checking if the docker daemon is running...")
    return subprocess.run(["docker", "ps"], stderr=-3, stdout=-3).returncode


def _start_docker() -> None:
    """Start docker daemon if not running."""
    if _docker_is_not_running():
        _logger.warning("Docker daemon is not running. Starting Docker...")
        subprocess.run(["open", "--background", "-a", "Docker"])
        _logger.info(
            "Docker daemon is starting in the background, "
            f"expected start time {_daemon_wait} secs"
        )
        # TODO (xames3): This can be optimized to not wait implicitly.
        time.sleep(_daemon_wait)
    _logger.info("Docker daemon is running...")


def _container_exists(name: str) -> int:
    """Check if the named container exists or not."""
    _logger.info("Checking if the container exists...")
    docker_ps = subprocess.Popen(["docker", "ps", "-a"], stdout=-1)
    awk = subprocess.Popen(
        ["awk", "{if(NR>1) print $NF}"], stdin=docker_ps.stdout, stdout=-1
    )
    docker_ps.stdout.close()
    return 1 if name in awk.communicate()[0].decode().splitlines() else 0


def run_container(argv: argparse.Namespace, options: list[str]) -> t.NoReturn:
    """Run docker containers on demand.

    This function uses the ``docker run`` command to spin a new
    container. The docker run command first creates a writeable container
    layer over the specified image, and then starts it using the specified
    command.

    Docker runs processes in isolated containers. A container is a
    process which runs on a host. The host may be local or remote. When
    an operator executes docker run, the container process that runs is
    isolated in that it has its own file system, its own networking, and
    its own isolated process tree separate from the host.

    We spin a docker container with some basic utilities in place like
    the hostname and working directory. However, these configurations can
    be overridden if needed.

    :param argv: ArgumentParser Namespaces.
    :param rest: Extra docker arguments which are not supported natively
        by xacker.

    .. versionchanged:: 2.0.0
        The argv parameter is now a Namespace object unlike before.

    .. versionchanged:: 2.0.0
        Function now checks if docker is running or not. If not, then
        start docker first.
    """
    if _docker_is_not_running():
        _start_docker()
    name = argv.name
    if _container_exists(name):
        _logger.info(f"Container: {name} already exists! Starting now...")
        cmd = ["docker", "start", "-ia", name]
        os.execvp(cmd[0], cmd)
    if name is None:
        _logger.info("Spawning a temporary container...")
        name = "--rm"
    else:
        name = f"--name {name}"
        _logger.info(f"Spawning new container: {name[7:]}...")
    cmd = [
        "docker",
        "run",
        "-ti",
        *name.split(),
        "--hostname",
        argv.hostname,
        "--workdir",
        argv.workdir,
        *options,
        argv.image,
        argv.command,
    ]
    cmd = list(filter(None, cmd))
    _logger.debug(f"Executing docker command: {' '.join(cmd)}")
    os.execvp(cmd[0], cmd)


def configure_docker_run(
    parser: t.Union[argparse.ArgumentParser, argparse._ActionsContainer]
) -> None:
    """Parser for configuring docker run command."""
    parser.add_argument(
        "-c",
        "--command",
        help="Command to execute in the running container.",
        metavar="<command>",
    )
    parser.add_argument(
        "-n",
        "--name",
        help="Name for the container.",
        metavar="<name>",
    )
    parser.add_argument(
        "-w",
        "--workdir",
        default="/tmp/code",
        help="Working directory inside the container (Default: %(default)s).",
        metavar="<path>",
    )
    parser.add_argument(
        "--hostname",
        default="XAs-Docker-Container",
        help="Container host name (Default: %(default)s).",
        metavar="<hostname>",
    )
    parser.add_argument(
        "--image",
        help="Image to be used for creating the development container.",
        metavar="<image>",
    )
