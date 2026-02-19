"""Shared CLI helpers."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import click

from homebudget.client import HomeBudgetClient


def parse_date(value: str | None, field_name: str) -> dt.date | None:
    """Parse an ISO date string into a date."""
    if value is None:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise click.BadParameter("Use YYYY-MM-DD format.", param_hint=field_name) from exc


def parse_decimal(value: str | None, field_name: str) -> Decimal | None:
    """Parse a decimal string into a Decimal."""
    if value is None:
        return None
    try:
        return Decimal(value)
    except Exception as exc:
        raise click.BadParameter("Use a valid decimal value.", param_hint=field_name) from exc


def resolve_forex_inputs(
    *,
    amount: Decimal | None,
    currency: str | None,
    currency_amount: Decimal | None,
    exchange_rate: Decimal | None,
    default_currency_amount: bool,
    allow_empty: bool,
    label: str,
) -> tuple[Decimal | None, str | None, Decimal | None]:
    """Resolve forex inputs into amount and currency_amount.

    Rules:
    - Either amount or currency_amount is required, unless allow_empty is True.
    - If currency_amount is provided, exchange_rate and currency are required.
    - amount and currency_amount are mutually exclusive.
    - When amount is provided, currency_amount defaults to amount.
    """
    if amount is not None and currency_amount is not None:
        raise click.UsageError(
            f"{label}: Provide --amount or --currency-amount with --exchange-rate, not both."
        )

    if currency_amount is not None:
        if exchange_rate is None:
            raise click.UsageError(
                f"{label}: --exchange-rate is required when --currency-amount is provided."
            )
        if not currency or not currency.strip():
            raise click.UsageError(
                f"{label}: --currency is required when --currency-amount is provided."
            )
        amount = currency_amount * exchange_rate

    if amount is None and currency_amount is None and not allow_empty:
        raise click.UsageError(f"{label}: Provide --amount or --currency-amount.")

    if amount is not None and currency_amount is None and default_currency_amount:
        currency_amount = amount

    return amount, currency, currency_amount


def get_client(ctx: click.Context) -> HomeBudgetClient:
    """Build a HomeBudget client from Click context.
    
    When sync is enabled, UI control is enabled to ensure the HomeBudget UI
    is closed during database operations, preventing inconsistent data reads
    and database lock conflicts during batch changes.
    """
    payload = ctx.obj or {}
    enable_sync = payload.get("enable_sync", True)
    return HomeBudgetClient(
        db_path=payload.get("db_path"),
        enable_sync=enable_sync,
        enable_ui_control=enable_sync,  # UI control enabled when sync is enabled
    )
