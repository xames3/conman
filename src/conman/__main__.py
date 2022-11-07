"""\
ConMan entry point API
======================

The ``conman.__main__`` module calls the ``conman.cli.main()`` to act
as an entrypoint for the ConMan application. The function returns an
exit code of 0 if the commands are executed successfully else it'll
return 1 and an error log will be displayed.

For more information about how the command line interface works, please
see ``conman.cli.py``.
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
