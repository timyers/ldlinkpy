from __future__ import annotations

DEFAULT_API_ROOT = "https://ldlink.nih.gov/LDlinkRest"
__version__ = "0.4.0"

from ldlinkpy.client import LDlinkClient
from ldlinkpy.endpoints.ldpair import ldpair
from ldlinkpy.endpoints.ldmatrix import ldmatrix
from ldlinkpy.endpoints.ldproxy import ldproxy
from ldlinkpy.endpoints.ldproxy_batch import ldproxy_batch
from ldlinkpy.endpoints.ldtrait import ldtrait
from ldlinkpy.endpoints.ldmatrix import ldmatrix
from ldlinkpy.endpoints.ldexpress import ldexpress
from ldlinkpy.endpoints.ldhap import ldhap
from ldlinkpy.endpoints.ldpop import ldpop
from ldlinkpy.endpoints.snpclip import snpclip
from ldlinkpy.endpoints.snpchip import snpchip
from ldlinkpy.lookups import (
    list_chip_platforms,
    list_chips,
    list_gtex_tissues,
    list_pop,
)

__all__ = [
    "DEFAULT_API_ROOT",
    "__version__",
    "LDlinkClient",
    "ldpair",
    "ldproxy",
    "ldproxy_batch",
    "ldtrait",
    "ldmatrix",
    "ldexpress",
    "ldhap",
    "ldpop",
    "snpclip",
    "snpchip",
    "list_chip_platforms",
    "list_chips",
    "list_pop",
    "list_gtex_tissues",
]
