"""System integration tests for forex rate fetching and caching."""

from __future__ import annotations

import datetime as dt
import json
from decimal import Decimal
from pathlib import Path

import pytest


FOREX_MODULE_NAME = "homebudget.forex"
BASE_CURRENCY = "USD"
TARGET_CURRENCY = "SGD"
INVALID_CURRENCY = "XXX"
CACHE_FILE_NAME = "forex-rates.json"
CACHE_TTL_HOURS = 1
STALE_OFFSET_HOURS = 2
RATE_SGD = Decimal("1.35")
FALLBACK_RATE = 1.0
CACHE_VERSION = 1


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _iso_hours_ago(hours: int) -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        - dt.timedelta(hours=hours)
    ).isoformat()


def _write_cache(path: Path, timestamp: str, rates: dict[str, float]) -> None:
    payload = {
        "metadata": {"version": CACHE_VERSION, "last_update": timestamp},
        "timestamp": timestamp,
        "base": BASE_CURRENCY,
        "rates": rates,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def _get_manager(cache_path: Path):
    forex_module = pytest.importorskip(
        FOREX_MODULE_NAME,
        reason="Forex rate manager not implemented",
    )
    return forex_module.ForexRateManager(
        config={"cache_ttl_hours": CACHE_TTL_HOURS},
        cache_path=cache_path,
    )


@pytest.mark.sit
def test_forex_rate_fetch_writes_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_path = tmp_path / CACHE_FILE_NAME
    manager = _get_manager(cache_path)

    def _fake_fetch(_: str) -> dict[str, float]:
        return {TARGET_CURRENCY: float(RATE_SGD)}

    monkeypatch.setattr(manager, "_fetch_from_api", _fake_fetch)

    rate = manager.get_rate(BASE_CURRENCY, TARGET_CURRENCY)

    assert rate == float(RATE_SGD)
    assert cache_path.exists()
    with cache_path.open("r", encoding="utf-8") as handle:
        cached = json.load(handle)
    assert cached["base"] == BASE_CURRENCY
    assert TARGET_CURRENCY in cached["rates"]


@pytest.mark.sit
def test_forex_rate_uses_cache_within_ttl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_path = tmp_path / CACHE_FILE_NAME
    _write_cache(cache_path, _iso_now(), {TARGET_CURRENCY: float(RATE_SGD)})
    manager = _get_manager(cache_path)

    def _fail_fetch(_: str) -> dict[str, float]:
        raise AssertionError("API fetch should not be called for valid cache")

    monkeypatch.setattr(manager, "_fetch_from_api", _fail_fetch)

    rate = manager.get_rate(BASE_CURRENCY, TARGET_CURRENCY)
    assert rate == float(RATE_SGD)


@pytest.mark.sit
def test_forex_rate_uses_stale_cache_on_api_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_path = tmp_path / CACHE_FILE_NAME
    _write_cache(
        cache_path,
        _iso_hours_ago(STALE_OFFSET_HOURS),
        {TARGET_CURRENCY: float(RATE_SGD)},
    )
    manager = _get_manager(cache_path)

    def _fail_fetch(_: str) -> dict[str, float]:
        raise RuntimeError("API unavailable")

    monkeypatch.setattr(manager, "_fetch_from_api", _fail_fetch)

    rate = manager.get_rate(BASE_CURRENCY, TARGET_CURRENCY)
    assert rate == float(RATE_SGD)


@pytest.mark.sit
def test_forex_rate_falls_back_without_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_path = tmp_path / CACHE_FILE_NAME
    manager = _get_manager(cache_path)

    def _fail_fetch(_: str) -> dict[str, float]:
        raise RuntimeError("API unavailable")

    monkeypatch.setattr(manager, "_fetch_from_api", _fail_fetch)

    rate = manager.get_rate(BASE_CURRENCY, TARGET_CURRENCY)
    assert rate == FALLBACK_RATE
    assert not cache_path.exists()


@pytest.mark.sit
def test_forex_rate_rejects_invalid_currency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_path = tmp_path / CACHE_FILE_NAME
    manager = _get_manager(cache_path)

    def _fake_fetch(_: str) -> dict[str, float]:
        return {TARGET_CURRENCY: float(RATE_SGD)}

    monkeypatch.setattr(manager, "_fetch_from_api", _fake_fetch)

    with pytest.raises(ValueError):
        manager.get_rate(INVALID_CURRENCY, TARGET_CURRENCY)