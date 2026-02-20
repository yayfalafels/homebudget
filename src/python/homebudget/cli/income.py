"""Income CLI commands."""

from __future__ import annotations

import csv
import datetime as dt
import json
from decimal import Decimal
from pathlib import Path

import click

from homebudget.cli.common import get_client, parse_date, parse_decimal, resolve_forex_inputs
from homebudget.models import IncomeDTO
from homebudget.exceptions import NotFoundError


@click.group()
def income() -> None:
    """Income commands."""


@income.command("add")
@click.option("--date", "date_value", required=True, help="Income date in YYYY-MM-DD.")
@click.option("--name", required=True, help="Income name.")
@click.option("--amount", "amount_value", default=None, help="Income amount.")
@click.option("--account", required=True, help="Account name.")
@click.option("--notes", default=None, help="Notes for the income.")
@click.option("--currency", default=None, help="Currency code for the income.")
@click.option("--currency-amount", default=None, help="Foreign currency amount.")
@click.option("--exchange-rate", default=None, help="Foreign exchange rate to base currency.")
@click.pass_context
def add_income(
    ctx: click.Context,
    date_value: str,
    name: str,
    amount_value: str | None,
    account: str,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
    exchange_rate: str | None,
) -> None:
    """Add income."""
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
        label="Income add",
    )
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
        try:
            record = client.add_income(income_dto)
        except NotFoundError as e:
            raise click.ClickException(
                f"Income add failed: {account!r} account not found. Check the account name and try again."
            )
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
@click.option("--exchange-rate", default=None, help="Foreign exchange rate to base currency.")
@click.pass_context
def update_income(
    ctx: click.Context,
    key: int,
    amount_value: str | None,
    notes: str | None,
    currency: str | None,
    currency_amount: str | None,
    exchange_rate: str | None,
) -> None:
    """Update income."""
    if amount_value is None and notes is None and currency is None and currency_amount is None:
        raise click.UsageError("Provide --amount, --notes, --currency, or --currency-amount.")
    amount = parse_decimal(amount_value, "--amount")
    foreign_amount = parse_decimal(currency_amount, "--currency-amount")
    rate = parse_decimal(exchange_rate, "--exchange-rate")
    if amount is None and foreign_amount is None and (currency is not None or rate is not None):
        raise click.UsageError(
            "Income update: Provide --amount or --currency-amount with --exchange-rate."
        )
    amount, currency, foreign_amount = resolve_forex_inputs(
        amount=amount,
        currency=currency,
        currency_amount=foreign_amount,
        exchange_rate=rate,
        default_currency_amount=False,
        allow_empty=notes is not None,
        label="Income update",
    )
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


@income.command("batch-import")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, path_type=Path), help="Path to CSV or JSON file.")
@click.option("--format", "file_format", required=True, type=click.Choice(["csv", "json"], case_sensitive=False), help="File format (csv or json).")
@click.option("--stop-on-error", is_flag=True, help="Stop processing on first error (default: continue and report errors).")
@click.option("--error-report", type=click.Path(path_type=Path), help="Write error details to this file.")
@click.pass_context
def batch_import_incomes(
    ctx: click.Context,
    file_path: Path,
    file_format: str,
    stop_on_error: bool,
    error_report: Path | None,
) -> None:
    """Import multiple income records from CSV or JSON file.
    
    CSV format: date,name,amount,account,notes,currency,currency_amount
    JSON format: Array of objects with same fields
    
    Example CSV:
        2026-02-01,Salary,5000.00,TWH - Personal,Monthly salary
    
    Example JSON:
        [{"date": "2026-02-01", "name": "Salary", ...}]
    """
    incomes = []
    errors = []
    
    try:
        if file_format.lower() == "csv":
            with file_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for line_num, row in enumerate(reader, start=2):
                    try:
                        income = IncomeDTO(
                            date=dt.datetime.strptime(row["date"], "%Y-%m-%d").date(),
                            name=row["name"],
                            amount=Decimal(row["amount"]),
                            account=row["account"],
                            notes=row.get("notes") or None,
                            currency=row.get("currency") or None,
                            currency_amount=Decimal(row["currency_amount"]) if row.get("currency_amount") else None,
                        )
                        incomes.append(income)
                    except Exception as e:
                        errors.append(f"Line {line_num}: {e}")
                        if stop_on_error:
                            raise click.ClickException(f"Error at line {line_num}: {e}")
        else:  # JSON
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise click.ClickException("JSON file must contain an array of income objects")
            
            for index, item in enumerate(data, start=1):
                try:
                    income = IncomeDTO(
                        date=dt.datetime.strptime(item["date"], "%Y-%m-%d").date(),
                        name=item["name"],
                        amount=Decimal(item["amount"]),
                        account=item["account"],
                        notes=item.get("notes") or None,
                        currency=item.get("currency") or None,
                        currency_amount=Decimal(item["currency_amount"]) if item.get("currency_amount") else None,
                    )
                    incomes.append(income)
                except Exception as e:
                    errors.append(f"Item {index}: {e}")
                    if stop_on_error:
                        raise click.ClickException(f"Error at item {index}: {e}")
        
        if not incomes and not errors:
            click.echo("No income records to import")
            return
        
        if errors and not incomes:
            click.echo(f"Failed to parse any income records. {len(errors)} errors.")
            if error_report:
                error_report.write_text("\n".join(errors), encoding="utf-8")
                click.echo(f"Error details written to {error_report}")
            return
        
        # Import batch
        with get_client(ctx) as client:
            result = client.add_incomes_batch(incomes, continue_on_error=not stop_on_error)
        
        # Display results
        click.echo(f"\nBatch import completed")
        click.echo(f"  Successful: {len(result.successful)}")
        click.echo(f"  Failed: {len(result.failed)}")
        
        if result.failed:
            click.echo("\nFailed records:")
            for income_dto, exception in result.failed:
                click.echo(f"  {income_dto.date} {income_dto.name}: {exception}")
        
        # Write error report if requested
        if error_report and (errors or result.failed):
            all_errors = errors[:]
            for income_dto, exception in result.failed:
                all_errors.append(f"Failed to insert: {income_dto.date} {income_dto.name} - {exception}")
            error_report.write_text("\n".join(all_errors), encoding="utf-8")
            click.echo(f"\nError details written to {error_report}")
        
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to process file: {e}")
