"""Shared CLI helpers."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Callable

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
    forex_rate_provider: Callable[[str], Decimal | float] | None = None,
) -> tuple[Decimal | None, str | None, Decimal | None]:
    """Resolve forex inputs into amount and currency_amount.

    Rules:
    - Either amount or currency_amount is required, unless allow_empty is True.
    - If currency_amount is provided, currency is required.
    - exchange_rate is optional when currency_amount is provided, but requires
      a forex_rate_provider to infer the rate.
    - amount and currency_amount are mutually exclusive.
    - When amount is provided, currency_amount defaults to amount.
    """
    if amount is not None and currency_amount is not None:
        raise click.UsageError(
            f"{label}: Provide --amount or --currency-amount, not both."
        )

    if currency_amount is not None:
        if not currency or not currency.strip():
            raise click.UsageError(
                f"{label}: --currency is required when --currency-amount is provided."
            )
        if exchange_rate is None:
            if forex_rate_provider is None:
                raise click.UsageError(
                    f"{label}: Provide --exchange-rate or enable forex rate inference."
                )
            exchange_rate = Decimal(str(forex_rate_provider(currency)))
        amount = currency_amount * exchange_rate

    if amount is None and currency_amount is None and not allow_empty:
        raise click.UsageError(f"{label}: Provide --amount or --currency-amount.")

    if amount is not None and currency_amount is None and default_currency_amount:
        currency_amount = amount

    return amount, currency, currency_amount


def get_client(ctx: click.Context) -> HomeBudgetClient:
    """Build a HomeBudget client from Click context.
    
    Sync is always enabled to ensure consistency between local and remote devices.
    UI control is enabled to ensure the HomeBudget UI is closed during database
    operations, preventing inconsistent data reads and database lock conflicts
    during batch changes.
    """
    payload = ctx.obj or {}
    return HomeBudgetClient(
        db_path=payload.get("db_path"),
        enable_sync=True,  # Sync is always enabled for CLI operations
        enable_ui_control=True,  # UI control enabled to prevent sync conflicts
        enable_forex_rates=True,  # Enable forex rate inference for non-base accounts
    )
