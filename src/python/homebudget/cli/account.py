"""Account CLI commands."""

from __future__ import annotations

import datetime as dt

import click

from homebudget.cli.common import get_client, parse_date
from homebudget.exceptions import NotFoundError


@click.group()
def account() -> None:
    """Account commands."""


@account.command("balance")
@click.option("--account", required=True, help="Account name.")
@click.option("--date", "date_value", default=None, help="Query date in YYYY-MM-DD (defaults to today).")
@click.pass_context
def get_balance(
    ctx: click.Context,
    account: str,
    date_value: str | None,
) -> None:
    """Get account balance at a specific date.
    
    Calculates the account balance based on the most recent reconcile balance
    and all transactions up to the query date.
    
    Examples:
        hb account balance --account "Checking"
        hb account balance --account "Savings" --date 2026-01-15
    """
    query_date = parse_date(date_value, "--date") if date_value else dt.date.today()
    
    with get_client(ctx) as client:
        try:
            balance_record = client.get_account_balance(account, query_date)
        except NotFoundError as e:
            raise click.ClickException(str(e))
        
        # Format output
        click.echo(f"\nAccount Balance: {balance_record.accountName}")
        click.echo(f"Query Date: {balance_record.queryDate.isoformat()}")
        click.echo(f"Balance: {balance_record.balanceAmount:.2f}")
        click.echo(f"\nReconcile Date: {balance_record.reconcileDate.isoformat()}")
        click.echo(f"Reconcile Amount: {balance_record.reconcileAmount:.2f}")
