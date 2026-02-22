"""Package version identifier."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 8):
    from importlib.metadata import version, PackageNotFoundError
else:
    from importlib_metadata import version, PackageNotFoundError

try:
    # Try to get version from installed package metadata
    __version__ = version("homebudget")
except PackageNotFoundError:
    # Fall back to reading VERSION file (for development/editable installs)
    _version_file = Path(__file__).parent.parent.parent.parent / "VERSION"
    __version__ = _version_file.read_text().strip()
