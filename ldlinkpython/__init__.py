from __future__ import annotations

DEFAULT_API_ROOT = "https://ldlink.nih.gov/LDlinkRest"
__version__ = "0.1.0"

from ldlinkpython.client import LDlinkClient
from ldlinkpython.endpoints.ldproxy import ldproxy
from ldlinkpython.endpoints.ldtrait import ldtrait
from ldlinkpython.endpoints.ldmatrix import ldmatrix
from ldlinkpython.endpoints.ldexpress import ldexpress
from ldlinkpython.endpoints.ldhap import ldhap
from ldlinkpython.endpoints.ldpop import ldpop
from ldlinkpython.endpoints.snpclip import snpclip
from ldlinkpython.endpoints.snpchip import snpchip
from ldlinkpython.lookups import list_chip_platforms, list_chips

__all__ = [
    "DEFAULT_API_ROOT",
    "__version__",
    "LDlinkClient",
    "ldproxy",
    "ldexpress",
    "ldhap",
    "ldpop",
    "snpclip",
    "snpchip",
    "list_chip_platforms",
    "list_chips",
]
