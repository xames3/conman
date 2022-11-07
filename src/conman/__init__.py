"""\
ConMan
=======

ConMan: An easy and flexible Docker based container manager.

ConMan is an open-source project that is available for the Unix
platforms which is currently maintained on GitHub. ConMan is a python
based wrapper for managing docker based containers and images on your
Unix system.

Usage Example::
---------------

    .. code-block:: console

        $ conman <command> [options]

What Is Docker you ask?

Docker is an open-source utility that eliminates repetitive tasks in
software development. It allows a developer to create a container, a
controlled environment to run a process. The container uses an image,
a replica of a specific operating environment. Although it sounds like
server virtualization, Docker containers are streamlined to execute a
command with minimal resources by loading only the libraries and
dependencies that are required.

What is ConMan capable of?

    - Well, as of the current release, ConMan is capable of creating
      and running new containers in sudo mode.

See https://github.com/xames3/conman/ for more help.

:copyright: (c) 2022 Akshay Mestry (XAMES3). All rights reserved.
:license: MIT, see LICENSE for more details.
"""

# According to Semantic Versioning (SemVer), major version zero (0.y.z)
# is for initial development. Anything MAY change at any time.
# The public API SHOULD NOT be considered stable.
__version__ = "1.0.0"

from .cli import create_main_parser as create_main_parser
from .cli import main as main
from .cli import subcommand as subcommand
from .core import ConMan as ConMan
from .core import ImmutableDict as ImmutableDict
from .core import ImmutableDictMixin as ImmutableDictMixin
from .core import Run as Run
from .logger import create_logger as create_logger
from .logger import get_logger as get_logger
