from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import click

from homebudget.client import HomeBudgetClient
from homebudget.models import ExpenseDTO


def _parse_date(value: str | None, field_name: str) -> dt.date | None:
    if value is None:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise click.BadParameter("Use YYYY-MM-DD format.", param_hint=field_name) from exc


def _parse_decimal(value: str | None, field_name: str) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value)
    except Exception as exc:
        raise click.BadParameter("Use a valid decimal value.", param_hint=field_name) from exc


def _get_client(ctx: click.Context) -> HomeBudgetClient:
    payload = ctx.obj or {}
    return HomeBudgetClient(
        db_path=payload.get("db_path"),
        enable_sync=payload.get("enable_sync", True),
    )


@click.group()
def expense() -> None:
    """Expense commands."""


@expense.command("add")
@click.option("--date", "date_value", required=True, help="Expense date in YYYY-MM-DD.")
@click.option("--category", required=True, help="Expense category.")
@click.option("--subcategory", required=True, help="Expense subcategory.")
@click.option("--amount", "amount_value", required=True, help="Expense amount.")
@click.option("--account", required=True, help="Account name.")
@click.option("--notes", default=None, help="Notes for the expense.")
@click.option("--currency", default=None, help="Currency code for the expense.")
@click.option("--currency-amount", default=None, help="Foreign currency amount.")
@click.pass_context
def add_expense(
    ctx: click.Context,
    date_value: str,
    category: str,
    subcategory: str,
    amount_value: str,
    account: str,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
) -> None:
    """Add an expense."""
    date = _parse_date(date_value, "--date")
    amount = _parse_decimal(amount_value, "--amount")
    foreign_amount = _parse_decimal(currency_amount, "--currency-amount")
    if date is None or amount is None:
        raise click.ClickException("Date and amount are required.")
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
    with _get_client(ctx) as client:
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
    start = _parse_date(start_date, "--start-date")
    end = _parse_date(end_date, "--end-date")
    with _get_client(ctx) as client:
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
    with _get_client(ctx) as client:
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
@click.pass_context
def update_expense(
    ctx: click.Context,
    key: int,
    amount_value: str | None,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
) -> None:
    """Update an expense."""
    if amount_value is None and notes is None and currency is None and currency_amount is None:
        raise click.UsageError("Provide --amount, --notes, --currency, or --currency-amount.")
    amount = _parse_decimal(amount_value, "--amount")
    foreign_amount = _parse_decimal(currency_amount, "--currency-amount")
    with _get_client(ctx) as client:
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
    with _get_client(ctx) as client:
        client.delete_expense(key)
    click.echo(f"Deleted expense {key}")
