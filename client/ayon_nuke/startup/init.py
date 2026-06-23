# Luma: backfill Python 3.8+ typing names on Nuke 13 (Py3.7) BEFORE any other
# import. This MUST stay inline and first -- it cannot be moved into a function
# or an `ayon_nuke` submodule, because importing the `ayon_nuke` package runs
# its __init__ -> addon -> `ayon_core` -> the launcher's `ayon_api`, which is
# exactly the import we must patch `typing` ahead of. Only top-level modules
# (`typing`, vendored `typing_extensions`) are touched here. See CLAUDE.md.
import sys as _sys

if _sys.version_info < (3, 8):
    import typing as _typing
    try:
        import typing_extensions as _te  # vendored 4.7.1, front of PYTHONPATH
    except Exception:
        _te = None
    if _te is not None:
        for _name in (getattr(_te, "__all__", None) or dir(_te)):
            if not _name.startswith("_") and not hasattr(_typing, _name):
                try:
                    setattr(_typing, _name, getattr(_te, _name))
                except Exception:
                    pass

from ayon_core.pipeline import install_host
from ayon_nuke.api import NukeHost

# Attempt to register host.
try:
    host = NukeHost()
    install_host(host)

# Current environment might not be 100% fully AYON compatible.
# e.g. on farm, using Deadline or RoyalRender native Nuke plugin.
# If an incomplete AYON environment is provided, the host
# will not be able to install.
# We still allow Nuke to start as-is, might be enough for rendering.
# Otherwise it'll raise on AYON dependency with more meaningful error.
except Exception as error:
    print(
        f"Cannot initialize AYON Nuke host: {error}. "
        "This might result in unexpected results."
    )
