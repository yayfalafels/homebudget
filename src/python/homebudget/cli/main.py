"""HomeBudget CLI entry point."""

from __future__ import annotations

from pathlib import Path

import click

from homebudget.__version__ import __version__
from homebudget.cli.batch import batch
from homebudget.cli.expense import expense
from homebudget.cli.income import income
from homebudget.cli.sync import sync
from homebudget.cli.transfer import transfer
from homebudget.cli.ui import ui


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="homebudget")
@click.option(
    "--db",
    "db_path",
    type=click.Path(path_type=Path),
    help="Path to the HomeBudget database.",
)
@click.pass_context
def main(ctx: click.Context, db_path: Path | None) -> None:
    """HomeBudget CLI entry point."""
    ctx.obj = {
        "db_path": db_path,
    }


main.add_command(batch)
main.add_command(expense)
main.add_command(income)
main.add_command(sync)
main.add_command(transfer)
main.add_command(ui)


if __name__ == "__main__":
    main()
