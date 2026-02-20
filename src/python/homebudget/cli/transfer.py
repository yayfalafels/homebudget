"""Transfer CLI commands."""

from __future__ import annotations

import click

from homebudget.cli.common import get_client, parse_date, parse_decimal, resolve_forex_inputs
from homebudget.models import TransferDTO


@click.group()
def transfer() -> None:
    """Transfer commands."""


@transfer.command("add")
@click.option("--date", "date_value", required=True, help="Transfer date in YYYY-MM-DD.")
@click.option("--from-account", required=True, help="Source account name.")
@click.option("--to-account", required=True, help="Destination account name.")
@click.option("--amount", "amount_value", default=None, help="Transfer amount.")
@click.option("--notes", default=None, help="Notes for the transfer.")
@click.option("--currency", default=None, help="Currency code for the transfer.")
@click.option("--currency-amount", default=None, help="Foreign currency amount.")
@click.option("--exchange-rate", default=None, help="Foreign exchange rate to base currency.")
@click.pass_context
def add_transfer(
    ctx: click.Context,
    date_value: str,
    from_account: str,
    to_account: str,
    amount_value: str | None,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
    exchange_rate: str | None,
) -> None:
    """Add a transfer."""
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
        label="Transfer add",
    )
    transfer_dto = TransferDTO(
        date=date,
        from_account=from_account,
        to_account=to_account,
        amount=amount,
        notes=notes,
        currency=currency,
        currency_amount=foreign_amount,
    )
    with get_client(ctx) as client:
        record = client.add_transfer(transfer_dto)
    click.echo(f"Added transfer {record.key}")


@transfer.command("list")
@click.option("--start-date", default=None, help="Start date in YYYY-MM-DD.")
@click.option("--end-date", default=None, help="End date in YYYY-MM-DD.")
@click.option("--limit", type=int, default=None, help="Limit results.")
@click.pass_context
def list_transfers(
    ctx: click.Context,
    start_date: str | None,
    end_date: str | None,
    limit: int | None,
) -> None:
    """List transfers."""
    start = parse_date(start_date, "--start-date")
    end = parse_date(end_date, "--end-date")
    with get_client(ctx) as client:
        records = client.list_transfers(start_date=start, end_date=end)
    if limit is not None:
        records = records[:limit]
    for record in records:
        notes = record.notes or ""
        click.echo(
            f"{record.key}\t{record.date.isoformat()}\t{record.amount}"
            f"\t{record.from_account}\t{record.to_account}\t{notes}"
        )


@transfer.command("get")
@click.argument("key", type=int)
@click.pass_context
def get_transfer(ctx: click.Context, key: int) -> None:
    """Get a transfer by key."""
    with get_client(ctx) as client:
        record = client.get_transfer(key)
    notes = record.notes or ""
    click.echo(
        f"{record.key}\t{record.date.isoformat()}\t{record.amount}\t"
        f"{record.from_account}\t{record.to_account}\t{notes}"
    )


@transfer.command("update")
@click.argument("key", type=int)
@click.option("--amount", "amount_value", default=None, help="Updated amount.")
@click.option("--notes", default=None, help="Updated notes.")
@click.option("--currency", default=None, help="Updated currency code.")
@click.option("--currency-amount", default=None, help="Updated foreign currency amount.")
@click.option("--exchange-rate", default=None, help="Foreign exchange rate to base currency.")
@click.pass_context
def update_transfer(
    ctx: click.Context,
    key: int,
    amount_value: str | None,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
    exchange_rate: str | None,
) -> None:
    """Update a transfer."""
    if amount_value is None and notes is None and currency is None and currency_amount is None:
        raise click.UsageError("Provide --amount, --notes, --currency, or --currency-amount.")
    amount = parse_decimal(amount_value, "--amount")
    foreign_amount = parse_decimal(currency_amount, "--currency-amount")
    rate = parse_decimal(exchange_rate, "--exchange-rate")
    if amount is None and foreign_amount is None and (currency is not None or rate is not None):
        raise click.UsageError(
            "Transfer update: Provide --amount or --currency-amount with --exchange-rate."
        )
    amount, currency, foreign_amount = resolve_forex_inputs(
        amount=amount,
        currency=currency,
        currency_amount=foreign_amount,
        exchange_rate=rate,
        default_currency_amount=False,
        allow_empty=notes is not None,
        label="Transfer update",
    )
    with get_client(ctx) as client:
        record = client.update_transfer(
            key=key, amount=amount, notes=notes, currency=currency, currency_amount=foreign_amount
        )
    click.echo(f"Updated transfer {record.key}")


@transfer.command("delete")
@click.argument("key", type=int)
@click.option("--yes", is_flag=True, help="Skip delete confirmation.")
@click.pass_context
def delete_transfer(ctx: click.Context, key: int, yes: bool) -> None:
    """Delete a transfer."""
    if not yes:
        confirm = click.confirm("Delete transfer?", default=False)
        if not confirm:
            click.echo("Delete cancelled.")
            return
    with get_client(ctx) as client:
        client.delete_transfer(key)
    click.echo(f"Deleted transfer {key}")
