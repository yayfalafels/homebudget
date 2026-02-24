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


@account.command("list")
@click.option("--currency", default=None, help="Filter by currency code (e.g., USD, SGD).")
@click.option("--type", "account_type", default=None, help="Filter by account type (e.g., Cash, Credit).")
@click.pass_context
def list_accounts(
    ctx: click.Context,
    currency: str | None,
    account_type: str | None,
) -> None:
    """List all accounts with current balances.
    
    Displays an account summary table with name, type, balance, and currency.
    Optionally filter by currency or account type.
    
    Examples:
        hb account list
        hb account list --currency USD
        hb account list --type Cash
        hb account list --currency SGD --type Credit
    """
    with get_client(ctx) as client:
        accounts = client.get_accounts(currency=currency, account_type=account_type)
        
        if not accounts:
            click.echo("No accounts found.")
            return
        
        # Format as table
        click.echo("\nAccounts:")
        click.echo("-" * 80)
        click.echo(f"{'Name':<30} {'Type':<20} {'Balance':<15} {'Currency':<10}")
        click.echo("-" * 80)
        
        for account in accounts:
            click.echo(
                f"{account.name:<30} {account.accountType:<20} {account.balance:>14.2f} {account.currency:<10}"
            )
        
        click.echo("-" * 80)

