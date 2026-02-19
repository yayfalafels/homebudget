"""Expense CLI commands."""

from __future__ import annotations

import click

from homebudget.cli.common import get_client, parse_date, parse_decimal, resolve_forex_inputs
from homebudget.models import ExpenseDTO


@click.group()
def expense() -> None:
    """Expense commands."""


@expense.command("add")
@click.option("--date", "date_value", required=True, help="Expense date in YYYY-MM-DD.")
@click.option("--category", required=True, help="Expense category.")
@click.option("--subcategory", required=True, help="Expense subcategory.")
@click.option("--amount", "amount_value", default=None, help="Expense amount.")
@click.option("--account", required=True, help="Account name.")
@click.option("--notes", default=None, help="Notes for the expense.")
@click.option("--currency", default=None, help="Currency code for the expense.")
@click.option("--currency-amount", default=None, help="Foreign currency amount.")
@click.option("--exchange-rate", default=None, help="Foreign exchange rate to base currency.")
@click.pass_context
def add_expense(
    ctx: click.Context,
    date_value: str,
    category: str,
    subcategory: str,
    amount_value: str | None,
    account: str,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
    exchange_rate: str | None,
) -> None:
    """Add an expense."""
    date = parse_date(date_value, "--date")
    amount = parse_decimal(amount_value, "--amount")
    foreign_amount = parse_decimal(currency_amount, "--currency-amount")
    rate = parse_decimal(exchange_rate, "--exchange-rate")
    if date is None:
        raise click.ClickException("Date is required.")
    amount, currency, foreign_amount = resolve_forex_inputs(
        amount=amount,
        currency=currency,
        currency_amount=foreign_amount,
        exchange_rate=rate,
        default_currency_amount=True,
        allow_empty=False,
        label="Expense add",
    )
    expense_dto = ExpenseDTO(
        date=date,
        category=category,
        subcategory=subcategory,
        amount=amount,
        account=account,
        notes=notes,
        currency=currency,
        currency_amount=foreign_amount,
    )
    with get_client(ctx) as client:
        record = client.add_expense(expense_dto)
    click.echo(f"Added expense {record.key}")


@expense.command("list")
@click.option("--start-date", default=None, help="Start date in YYYY-MM-DD.")
@click.option("--end-date", default=None, help="End date in YYYY-MM-DD.")
@click.option("--account", default=None, help="Filter by account name.")
@click.option("--limit", type=int, default=None, help="Limit results.")
@click.pass_context
def list_expenses(
    ctx: click.Context,
    start_date: str | None,
    end_date: str | None,
    account: str | None,
    limit: int | None,
) -> None:
    """List expenses."""
    start = parse_date(start_date, "--start-date")
    end = parse_date(end_date, "--end-date")
    with get_client(ctx) as client:
        records = client.list_expenses(start_date=start, end_date=end)
    if account:
        records = [record for record in records if record.account == account]
    if limit is not None:
        records = records[:limit]
    for record in records:
        notes = record.notes or ""
        click.echo(
            f"{record.key}\t{record.date.isoformat()}\t{record.amount}"
            f"\t{record.account}\t{record.category}\t{record.subcategory}\t{notes}"
        )


@expense.command("get")
@click.argument("key", type=int)
@click.pass_context
def get_expense(ctx: click.Context, key: int) -> None:
    """Get an expense by key."""
    with get_client(ctx) as client:
        record = client.get_expense(key)
    notes = record.notes or ""
    click.echo(
        f"{record.key}\t{record.date.isoformat()}\t{record.amount}\t"
        f"{record.account}\t{record.category}\t{record.subcategory}\t{notes}"
    )


@expense.command("update")
@click.argument("key", type=int)
@click.option("--amount", "amount_value", default=None, help="Updated amount.")
@click.option("--notes", default=None, help="Updated notes.")
@click.option("--currency", default=None, help="Updated currency code.")
@click.option("--currency-amount", default=None, help="Updated foreign currency amount.")
@click.option("--exchange-rate", default=None, help="Foreign exchange rate to base currency.")
@click.pass_context
def update_expense(
    ctx: click.Context,
    key: int,
    amount_value: str | None,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
    exchange_rate: str | None,
) -> None:
    """Update an expense."""
    if amount_value is None and notes is None and currency is None and currency_amount is None:
        raise click.UsageError("Provide --amount, --notes, --currency, or --currency-amount.")
    amount = parse_decimal(amount_value, "--amount")
    foreign_amount = parse_decimal(currency_amount, "--currency-amount")
    rate = parse_decimal(exchange_rate, "--exchange-rate")
    if amount is None and foreign_amount is None and (currency is not None or rate is not None):
        raise click.UsageError(
            "Expense update: Provide --amount or --currency-amount with --exchange-rate."
        )
    amount, currency, foreign_amount = resolve_forex_inputs(
        amount=amount,
        currency=currency,
        currency_amount=foreign_amount,
        exchange_rate=rate,
        default_currency_amount=False,
        allow_empty=notes is not None,
        label="Expense update",
    )
    with get_client(ctx) as client:
        record = client.update_expense(
            key=key, amount=amount, notes=notes, currency=currency, currency_amount=foreign_amount
        )
    click.echo(f"Updated expense {record.key}")


@expense.command("delete")
@click.argument("key", type=int)
@click.option("--yes", is_flag=True, help="Skip delete confirmation.")
@click.pass_context
def delete_expense(ctx: click.Context, key: int, yes: bool) -> None:
    """Delete an expense."""
    if not yes:
        confirm = click.confirm("Delete expense?", default=False)
        if not confirm:
            click.echo("Delete cancelled.")
            return
    with get_client(ctx) as client:
        client.delete_expense(key)
    click.echo(f"Deleted expense {key}")
