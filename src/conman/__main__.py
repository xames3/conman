"""ConMan's entry point.

This module calls the ``conman.cli.main()`` to act as an entrypoint for
the ConMan application.

Usage Example
-------------

    .. code-block:: console

        $ conman --help

For more information about how the command line interface works, please
see ``conman.cli.py``.
"""

from .cli import main

if __name__ == "__main__":
    # There are 3 exit functions, in addition to raising ``SystemExit``.
    # The first one is ``os._exit``, which requires 1 integer argument,
    # and exits immediately with no cleanup. It's unlikely you'll ever
    # want to touch this one, but it is there.
    # 
    # The ``sys.exit`` is defined in sysmodule.c and just runs 
    # ``PyErr_SetObject(PyExc_SystemExit, exit_code)``; which is
    # effectively the same as directly raising ``SystemExit``.
    # In fine detail, raising ``SystemExit`` is probably faster,
    # since ``sys.exit`` requires an LOAD_ATTR and CALL_FUNCTION vs
    # RAISE_VARARGS opcalls. Also, raise ``SystemExit`` produces
    # slightly smaller bytecode (4bytes less), (1 byte extra if you use
    # ``from sys import exit`` since ``sys.exit`` is expected to return
    # ``None``, so includes an extra POP_TOP).
    # 
    # The last exit function is defined in ``site.py``, and aliased to
    # exit or quit in the REPL. It's actually an instance of the
    # ``Quitter`` class (so it can have a custom __repr__, so is
    # probably the slowest running. Also, it closes ``sys.stdin`` prior
    # to raising ``SystemExit``, so it's recommended for use only in
    # the REPL.
    raise SystemExit(main())
