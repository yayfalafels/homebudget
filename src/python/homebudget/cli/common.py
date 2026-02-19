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
