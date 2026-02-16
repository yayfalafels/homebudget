from __future__ import annotations

import click

from homebudget.__version__ import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="homebudget")
def main() -> None:
    """HomeBudget CLI entry point."""


if __name__ == "__main__":
    main()
