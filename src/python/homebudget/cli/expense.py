"""Expense CLI commands."""

from __future__ import annotations

import csv
import datetime as dt
import json
from decimal import Decimal
from pathlib import Path

import click

from homebudget.cli.common import get_client, parse_date, parse_decimal, resolve_forex_inputs
from homebudget.models import ExpenseDTO
from homebudget.exceptions import NotFoundError


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
        try:
            record = client.add_expense(expense_dto)
        except NotFoundError as e:
            raise click.ClickException(
                f"Expense add failed: {account!r} account, {category!r} category, or {subcategory!r} subcategory not found. "
                "Check the names and try again."
            )
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


@expense.command("batch-import")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True, path_type=Path), help="Path to CSV or JSON file.")
@click.option("--format", "file_format", required=True, type=click.Choice(["csv", "json"], case_sensitive=False), help="File format (csv or json).")
@click.option("--stop-on-error", is_flag=True, help="Stop processing on first error (default: continue and report errors).")
@click.option("--error-report", type=click.Path(path_type=Path), help="Write error details to this file.")
@click.pass_context
def batch_import_expenses(
    ctx: click.Context,
    file_path: Path,
    file_format: str,
    stop_on_error: bool,
    error_report: Path | None,
) -> None:
    """Import multiple expenses from CSV or JSON file.
    
    CSV format: date,category,subcategory,amount,account,notes,currency,currency_amount
    JSON format: Array of objects with same fields
    
    Example CSV:
        2026-02-01,Food (Basic),Groceries,45.50,TWH - Personal,Weekly groceries
    
    Example JSON:
        [{"date": "2026-02-01", "category": "Food (Basic)", ...}]
    """
    expenses = []
    errors = []
    
    try:
        if file_format.lower() == "csv":
            with file_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for line_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                    try:
                        expense = ExpenseDTO(
                            date=dt.datetime.strptime(row["date"], "%Y-%m-%d").date(),
                            category=row["category"],
                            subcategory=row["subcategory"],
                            amount=Decimal(row["amount"]),
                            account=row["account"],
                            notes=row.get("notes") or None,
                            currency=row.get("currency") or None,
                            currency_amount=Decimal(row["currency_amount"]) if row.get("currency_amount") else None,
                        )
                        expenses.append(expense)
                    except Exception as e:
                        errors.append(f"Line {line_num}: {e}")
                        if stop_on_error:
                            raise click.ClickException(f"Error at line {line_num}: {e}")
        else:  # JSON
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise click.ClickException("JSON file must contain an array of expense objects")
            
            for index, item in enumerate(data, start=1):
                try:
                    expense = ExpenseDTO(
                        date=dt.datetime.strptime(item["date"], "%Y-%m-%d").date(),
                        category=item["category"],
                        subcategory=item["subcategory"],
                        amount=Decimal(item["amount"]),
                        account=item["account"],
                        notes=item.get("notes") or None,
                        currency=item.get("currency") or None,
                        currency_amount=Decimal(item["currency_amount"]) if item.get("currency_amount") else None,
                    )
                    expenses.append(expense)
                except Exception as e:
                    errors.append(f"Item {index}: {e}")
                    if stop_on_error:
                        raise click.ClickException(f"Error at item {index}: {e}")
        
        if not expenses and not errors:
            click.echo("No expenses to import")
            return
        
        if errors and not expenses:
            click.echo(f"Failed to parse any expenses. {len(errors)} errors.")
            if error_report:
                error_report.write_text("\n".join(errors), encoding="utf-8")
                click.echo(f"Error details written to {error_report}")
            return
        
        # Import batch
        with get_client(ctx) as client:
            result = client.add_expenses_batch(expenses, continue_on_error=not stop_on_error)
        
        # Display results
        click.echo(f"\nBatch import completed")
        click.echo(f"  Successful: {len(result.successful)}")
        click.echo(f"  Failed: {len(result.failed)}")
        
        if result.failed:
            click.echo("\nFailed records:")
            for expense_dto, exception in result.failed:
                click.echo(f"  {expense_dto.date} {expense_dto.category}: {exception}")
        
        # Write error report if requested
        if error_report and (errors or result.failed):
            all_errors = errors[:]
            for expense_dto, exception in result.failed:
                all_errors.append(f"Failed to insert: {expense_dto.date} {expense_dto.category} - {exception}")
            error_report.write_text("\n".join(all_errors), encoding="utf-8")
            click.echo(f"\nError details written to {error_report}")
        
    except click.ClickException:
        raise
    except Exception as e:
        raise click.ClickException(f"Failed to process file: {e}")
