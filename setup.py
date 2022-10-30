"""ConMan setup.

This will install the ``conman`` package in the python 3.7+ environment.
Before proceeding, please ensure you have a virtual environment setup &
running.

See https://github.com/xames3/conman/ for more help.

.. versionadded:: 0.0.2
    Added typing support for ``pkg_resources``.
"""

import platform
import site
import sys

from pkg_resources import parse_version

try:
    import setuptools
except ImportError:
    raise RuntimeError(
        "Could not install package in the environment as setuptools is "
        "missing. Please create a new virtual environment before proceeding."
    )

_current_py_version: str = platform.python_version()
_min_py_version: str = "3.7"

if parse_version(_current_py_version) < parse_version(_min_py_version):
    raise SystemExit(
        "Could not install ``conman`` in the environment! It requires python "
        f"version 3.7+, you are using {_current_py_version}..."
    )

# BUG: Cannot install into user directory with editable source.
# Using this solution: https://stackoverflow.com/a/68487739/14316408
# to solve the problem with installation. As of October, 2022 the issue
# is still open on GitHub: https://github.com/pypa/pip/issues/7953.

site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

if __name__ == "__main__":
    setuptools.setup()
