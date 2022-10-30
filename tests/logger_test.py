import os.path as p

import pytest

from conman.logger import _setup_logs_dir


@pytest.mark.parametrize(
    ("override", "path", "expected"),
    (
        (True, None, None),
        (False, None, p.join(p.expanduser("~"), ".conman", "session.log")),
    )
)
def test_setup_logs_dir(override, path, expected):
    assert _setup_logs_dir(override, path) == expected
