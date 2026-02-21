"""Transfer CLI commands."""

from __future__ import annotations

import csv
import datetime as dt
import json
from decimal import Decimal
from pathlib import Path

import click

from homebudget.cli.common import get_client, parse_date, parse_decimal, resolve_forex_inputs
from homebudget.models import TransferDTO
from homebudget.exceptions import NotFoundError


@click.group()
def transfer() -> None:
    """Transfer commands."""


@transfer.command("add")
@click.option("--date", "date_value", required=True, help="Transfer date in YYYY-MM-DD.")
@click.option("--from-account", required=True, help="Source account name.")
@click.option("--to-account", required=True, help="Destination account name.")
@click.option("--amount", "user_amount_str", default=None, help="Transfer amount.")
@click.option("--notes", default=None, help="Notes for the transfer.")
@click.option("--currency", default=None, help="Currency code for the transfer.")
@click.option("--currency-amount", "user_currency_amount_str", default=None, help="Foreign currency amount.")
@click.option("--exchange-rate", default=None, help="Foreign exchange rate to base currency.")
@click.pass_context
def add_transfer(
    ctx: click.Context,
    date_value: str,
    from_account: str,
    to_account: str,
    user_amount_str: str | None,
    notes: str | None,
    currency: str | None,
    user_currency_amount_str: str | None,
    exchange_rate: str | None,
) -> None:
    """Add a transfer.
    
    User can specify amount in two ways:
    - --amount: Amount in base currency if base is in either account, else in from_account currency.
    - --currency-amount + --exchange-rate + --currency: Amount in a foreign currency.
    """
    date = parse_date(date_value, "--date")
    user_amount = parse_decimal(user_amount_str, "--amount")
    user_currency_amount = parse_decimal(user_currency_amount_str, "--currency-amount")
    user_exchange_rate = parse_decimal(exchange_rate, "--exchange-rate")
    if date is None:
        raise click.ClickException("Date is required.")
    # resolve_forex_inputs processes user inputs and returns DTO-ready values
    dto_amount, dto_currency, dto_currency_amount = resolve_forex_inputs(
        amount=user_amount,
        currency=currency,
        currency_amount=user_currency_amount,
        exchange_rate=user_exchange_rate,
        default_currency_amount=False,  # Let client handle forex inference
        allow_empty=False,
        label="Transfer add",
    )
    transfer_dto = TransferDTO(
        date=date,
        from_account=from_account,
        to_account=to_account,
        amount=dto_amount,
        notes=notes,
        currency=dto_currency,
        currency_amount=dto_currency_amount,
    )
    with get_client(ctx) as client:
        try:
            record = client.add_transfer(transfer_dto)
        except NotFoundError as e:
            raise click.ClickException(
                f"Transfer add failed: {from_account!r} or {to_account!r} account not found. "
                "Check the account names and try again."
            )
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


@transfer.command("batch-import")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, path_type=Path), help="Path to CSV or JSON file.")
@click.option("--format", "file_format", required=True, type=click.Choice(["csv", "json"], case_sensitive=False), help="File format (csv or json).")
@click.option("--stop-on-error", is_flag=True, help="Stop processing on first error (default: continue and report errors).")
@click.option("--error-report", type=click.Path(path_type=Path), help="Write error details to this file.")
@click.pass_context
def batch_import_transfers(
    ctx: click.Context,
    file_path: Path,
    file_format: str,
    stop_on_error: bool,
    error_report: Path | None,
) -> None:
    """Import multiple transfers from CSV or JSON file.
    
    CSV format: date,from_account,to_account,amount,notes,currency,currency_amount
    JSON format: Array of objects with same fields
    
    Example CSV:
        2026-02-05,TWH - Personal,30 CC Hashemis,100.00,Credit card payment
    
    Example JSON:
        [{"date": "2026-02-05", "from_account": "...", ...}]
    """
    transfers = []
    errors = []
    
    try:
        if file_format.lower() == "csv":
            with file_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for line_num, row in enumerate(reader, start=2):
                    try:
                        transfer = TransferDTO(
                            date=dt.datetime.strptime(row["date"], "%Y-%m-%d").date(),
                            from_account=row["from_account"],
                            to_account=row["to_account"],
                            amount=Decimal(row["amount"]),
                            notes=row.get("notes") or None,
                            currency=row.get("currency") or None,
                            currency_amount=Decimal(row["currency_amount"]) if row.get("currency_amount") else None,
                        )
                        transfers.append(transfer)
                    except Exception as e:
                        errors.append(f"Line {line_num}: {e}")
                        if stop_on_error:
                            raise click.ClickException(f"Error at line {line_num}: {e}")
        else:  # JSON
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise click.ClickException("JSON file must contain an array of transfer objects")
            
            for index, item in enumerate(data, start=1):
                try:
                    transfer = TransferDTO(
                        date=dt.datetime.strptime(item["date"], "%Y-%m-%d").date(),
                        from_account=item["from_account"],
                        to_account=item["to_account"],
                        amount=Decimal(item["amount"]),
                        notes=item.get("notes") or None,
                        currency=item.get("currency") or None,
                        currency_amount=Decimal(item["currency_amount"]) if item.get("currency_amount") else None,
                    )
                    transfers.append(transfer)
                except Exception as e:
                    errors.append(f"Item {index}: {e}")
                    if stop_on_error:
                        raise click.ClickException(f"Error at item {index}: {e}")
        
        if not transfers and not errors:
            click.echo("No transfers to import")
            return
        
        if errors and not transfers:
            click.echo(f"Failed to parse any transfers. {len(errors)} errors.")
            if error_report:
                error_report.write_text("\n".join(errors), encoding="utf-8")
                click.echo(f"Error details written to {error_report}")
            return
        
        # Import batch
        with get_client(ctx) as client:
            result = client.add_transfers_batch(transfers, continue_on_error=not stop_on_error)
        
        # Display results
        click.echo(f"\nBatch import completed")
        click.echo(f"  Successful: {len(result.successful)}")
        click.echo(f"  Failed: {len(result.failed)}")
        
        if result.failed:
            click.echo("\nFailed records:")
            for transfer_dto, exception in result.failed:
                click.echo(f"  {transfer_dto.date} {transfer_dto.from_account} → {transfer_dto.to_account}: {exception}")
        
        # Write error report if requested
        if error_report and (errors or result.failed):
            all_errors = errors[:]
            for transfer_dto, exception in result.failed:
                all_errors.append(f"Failed to insert: {transfer_dto.date} {transfer_dto.from_account} → {transfer_dto.to_account} - {exception}")
            error_report.write_text("\n".join(all_errors), encoding="utf-8")
            click.echo(f"\nError details written to {error_report}")
        
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to process file: {e}")
