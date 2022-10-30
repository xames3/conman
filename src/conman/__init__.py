"""ConMan: An easy and flexible Docker based container manager.

ConMan is an open-source project that is available for the Unix
platforms which is currently maintained on GitHub. ConMan is a python
based wrapper for managing docker based containers and images on your
Unix system.

See https://github.com/xames3/conman/ for more help.
"""

from .cli import main as main
from .logger import basic_config as basic_config
from .logger import get_logger as get_logger

# As per Semantic Versioning (SemVer), Major version zero (0.y.z) is
# for initial development. Anything MAY change at any time. The public
# API SHOULD NOT be considered stable. Version 1.0.0 defines the public
# API. The way in which the version number is incremented after this
# release is dependent on this public API and how it changes.
__version__ = "0.0.1.dev0"
