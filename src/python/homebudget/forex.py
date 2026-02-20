"""Forex rate fetching and caching utilities."""

from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
import json
from pathlib import Path
import re
from typing import Any

from decimal import Decimal

import requests

CACHE_VERSION = 1
DEFAULT_CACHE_TTL_HOURS = 1
DEFAULT_TIMEOUT_SECONDS = 5
REF_CURRENCY = "USD"
CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True)
class ForexConfig:
    """Configuration for forex rate fetching."""

    cache_ttl_hours: int = DEFAULT_CACHE_TTL_HOURS
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


class ForexRateManager:
    """Fetch and cache forex rates using a public API."""

    EXCHANGE_RATE_API_URL = "https://api.exchangerate-api.com/v4/latest"

    def __init__(self, config: dict[str, Any], cache_path: str | Path) -> None:
        self.config = ForexConfig(
            cache_ttl_hours=int(config.get("cache_ttl_hours", DEFAULT_CACHE_TTL_HOURS)),
            timeout_seconds=int(config.get("timeout", DEFAULT_TIMEOUT_SECONDS)),
        )
        self.cache_path = Path(cache_path)
        self._cache: dict[str, Any] = self._load_cache()

    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Get a rate for from_currency to to_currency.

        Falls back to 1.0 if the rate cannot be resolved.
        """
        from_currency = self._validate_currency(from_currency)
        to_currency = self._validate_currency(to_currency)

        if from_currency == to_currency:
            return 1.0

        rates = self._get_rates()
        if not rates:
            return 1.0

        if from_currency != REF_CURRENCY and from_currency not in rates:
            raise ValueError(f"Invalid currency code: {from_currency}")
        if to_currency != REF_CURRENCY and to_currency not in rates:
            raise ValueError(f"Invalid currency code: {to_currency}")

        if from_currency == REF_CURRENCY:
            return float(rates.get(to_currency, 1.0))

        if to_currency == REF_CURRENCY:
            from_rate = rates.get(from_currency)
            if from_rate:
                return float(Decimal("1") / Decimal(str(from_rate)))
            return 1.0

        from_rate = rates.get(from_currency)
        to_rate = rates.get(to_currency)
        if from_rate and to_rate:
            return float(Decimal(str(to_rate)) / Decimal(str(from_rate)))
        return 1.0

    def _get_rates(self) -> dict[str, float]:
        if self._is_cache_valid():
            cached_rates = self._cache.get("rates", {})
            if cached_rates:
                return cached_rates

        try:
            rates = self._fetch_from_api(REF_CURRENCY)
            if rates:
                self._cache = self._build_cache(rates)
                self._save_cache(self._cache)
                return rates
        except Exception:
            pass

        cached_rates = self._cache.get("rates", {}) if self._cache else {}
        if cached_rates:
            return cached_rates
        return {}

    def _fetch_from_api(self, currency: str) -> dict[str, float]:
        url = f"{self.EXCHANGE_RATE_API_URL}/{currency}"
        response = requests.get(url, timeout=self.config.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        rates = payload.get("rates", {})
        if not isinstance(rates, dict):
            return {}
        return rates

    def _load_cache(self) -> dict[str, Any]:
        if not self.cache_path.exists():
            return {}
        try:
            with self.cache_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if not isinstance(payload, dict):
                return {}
            return payload
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_cache(self, payload: dict[str, Any]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def _build_cache(self, rates: dict[str, float]) -> dict[str, Any]:
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        return {
            "metadata": {"version": CACHE_VERSION, "last_update": timestamp},
            "timestamp": timestamp,
            "base": REF_CURRENCY,
            "rates": rates,
        }

    def _is_cache_valid(self) -> bool:
        timestamp = self._cache.get("timestamp") if self._cache else None
        if not timestamp:
            return False
        try:
            cached_at = dt.datetime.fromisoformat(timestamp)
        except ValueError:
            return False
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=dt.timezone.utc)
        now = dt.datetime.now(dt.timezone.utc)
        age = now - cached_at
        ttl = dt.timedelta(hours=self.config.cache_ttl_hours)
        return age <= ttl

    def _validate_currency(self, code: str) -> str:
        if not code or not CURRENCY_PATTERN.match(code):
            raise ValueError(f"Invalid currency code: {code}")
        return code
