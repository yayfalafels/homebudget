"""Income CLI commands."""

from __future__ import annotations

import click

from homebudget.cli.common import get_client, parse_date, parse_decimal
from homebudget.models import IncomeDTO


@click.group()
def income() -> None:
    """Income commands."""


@income.command("add")
@click.option("--date", "date_value", required=True, help="Income date in YYYY-MM-DD.")
@click.option("--name", required=True, help="Income name.")
@click.option("--amount", "amount_value", required=True, help="Income amount.")
@click.option("--account", required=True, help="Account name.")
@click.option("--notes", default=None, help="Notes for the income.")
@click.option("--currency", default=None, help="Currency code for the income.")
@click.option("--currency-amount", default=None, help="Foreign currency amount.")
@click.pass_context
def add_income(
    ctx: click.Context,
    date_value: str,
    name: str,
    amount_value: str,
    account: str,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
) -> None:
    """Add income."""
    date = parse_date(date_value, "--date")
    amount = parse_decimal(amount_value, "--amount")
    foreign_amount = parse_decimal(currency_amount, "--currency-amount")
    if date is None or amount is None:
        raise click.ClickException("Date and amount are required.")
    income_dto = IncomeDTO(
        date=date,
        name=name,
        amount=amount,
        account=account,
        notes=notes,
        currency=currency,
        currency_amount=foreign_amount,
    )
    with get_client(ctx) as client:
        record = client.add_income(income_dto)
    click.echo(f"Added income {record.key}")


@income.command("list")
@click.option("--start-date", default=None, help="Start date in YYYY-MM-DD.")
@click.option("--end-date", default=None, help="End date in YYYY-MM-DD.")
@click.option("--account", default=None, help="Filter by account name.")
@click.option("--limit", type=int, default=None, help="Limit results.")
@click.pass_context
def list_incomes(
    ctx: click.Context,
    start_date: str | None,
    end_date: str | None,
    account: str | None,
    limit: int | None,
) -> None:
    """List income records."""
    start = parse_date(start_date, "--start-date")
    end = parse_date(end_date, "--end-date")
    with get_client(ctx) as client:
        records = client.list_incomes(start_date=start, end_date=end)
    if account:
        records = [record for record in records if record.account == account]
    if limit is not None:
        records = records[:limit]
    for record in records:
        notes = record.notes or ""
        click.echo(
            f"{record.key}\t{record.date.isoformat()}\t{record.amount}"
            f"\t{record.account}\t{record.name}\t{notes}"
        )


@income.command("get")
@click.argument("key", type=int)
@click.pass_context
def get_income(ctx: click.Context, key: int) -> None:
    """Get an income record by key."""
    with get_client(ctx) as client:
        record = client.get_income(key)
    notes = record.notes or ""
    click.echo(
        f"{record.key}\t{record.date.isoformat()}\t{record.amount}"
        f"\t{record.account}\t{record.name}\t{notes}"
    )


@income.command("update")
@click.argument("key", type=int)
@click.option("--amount", "amount_value", default=None, help="Updated amount.")
@click.option("--notes", default=None, help="Updated notes.")
@click.option("--currency", default=None, help="Updated currency code.")
@click.option("--currency-amount", default=None, help="Updated foreign currency amount.")
@click.pass_context
def update_income(
    ctx: click.Context,
    key: int,
    amount_value: str | None,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
) -> None:
    """Update income."""
    if amount_value is None and notes is None and currency is None and currency_amount is None:
        raise click.UsageError("Provide --amount, --notes, --currency, or --currency-amount.")
    amount = parse_decimal(amount_value, "--amount")
    foreign_amount = parse_decimal(currency_amount, "--currency-amount")
    with get_client(ctx) as client:
        record = client.update_income(
            key=key, amount=amount, notes=notes, currency=currency, currency_amount=foreign_amount
        )
    click.echo(f"Updated income {record.key}")


@income.command("delete")
@click.argument("key", type=int)
@click.option("--yes", is_flag=True, help="Skip delete confirmation.")
@click.pass_context
def delete_income(ctx: click.Context, key: int, yes: bool) -> None:
    """Delete income."""
    if not yes:
        confirm = click.confirm("Delete income?", default=False)
        if not confirm:
            click.echo("Delete cancelled.")
            return
    with get_client(ctx) as client:
        client.delete_income(key)
    click.echo(f"Deleted income {key}")
