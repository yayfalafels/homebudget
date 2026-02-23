# Forex Rates Feature Design

## Table of contents

- [Overview](#overview)
- [Terminology](#terminology)
- [Requirements](#requirements)
- [API service selection](#api-service-selection)
- [Data structure and storage](#data-structure-and-storage)
- [Caching and TTL strategy](#caching-and-ttl-strategy)
- [Fallback mechanism](#fallback-mechanism)
- [Integration points](#integration-points)
- [Architecture](#architecture)
- [Error handling](#error-handling)
- [Configuration](#configuration)
- [Appendix: Alternative API providers](#appendix-alternative-api-providers)

## Overview

The forex rates feature enables the HomeBudget wrapper to fetch current foreign exchange rates for non-base currency transactions. This feature supports the existing foreign currency input rules by providing automatic rate lookups and caching to handle offline scenarios and reduce API calls.

### Use case

When users record expenses or income in foreign currencies, for example: USD amounts in a SGD-base-currency account, they need to convert between currencies using current exchange rates. Instead of manually entering rates, this feature:

1. Fetches current rates from a public API
2. Caches rates locally with timestamps
3. Serves cached rates within an hour without additional API calls
4. Falls back to 1.0 when offline or data is unavailable

### Concept

The primary conversion path leverages USD as an intermediary:

- Fetch rates for all currencies against USD
- Calculate conversion between any two currencies using the formula: `CURRENCY_A.USD / CURRENCY_B.USD`
- Example: To convert SGD to USD, use the quoted rate directly. To convert SGD to EUR, calculate the EUR and SGD rates against USD

## Terminology

- **Base currency**: The primary currency of the user's budget (e.g., SGD)
- **Reference currency**: USD, used as a common denominator for all exchange rates fetched from the API. Referred to as "base" in API responses but distinct from the user's base currency.
- **Foreign currency**: Any currency other than the base currency (e.g., USD, EUR)
- **Forex rate**: also "exchange rate". The exchange rate between a foreign currency and the base currency, expressed as a decimal (e.g., 1 USD = 1.35 SGD → rate = 1.35)
- **Cache TTL**: Time-to-live for cached rates, after which they are considered stale and a fresh API fetch is triggered
- **Fallback rate**: The default rate of 1.0 used when no valid rate is available, meaning no conversion is applied

## Requirements

### Functional requirements

1. **Fetch rates on demand**: Users can request current forex rates for a given currency pair
2. **Cache locally**: Store fetched rates in JSON with last-fetched timestamp
3. **TTL enforcement**: Use cached rates if fetched within the last hour
4. **Fallback behavior**: Return 1.0 if:
   - Application is offline (cannot reach API)
   - No rate has been previously cached for a currency
   - Rate fetch fails with an error

5. **Calculate derived rates**: Support arbitrary currency pairs by using USD as a hub
6. **Configuration**: Allow users to configure API preferences and cache location

### Non-functional requirements

1. **Reliability**: Never block user operations due to rate fetch failures
2. **Performance**: Minimize API calls through effective caching
3. **Transparency**: Log fetch attempts, cache hits/misses, and fallbacks
4. **Testability**: Separate API logic, caching logic, and data persistence

## API service selection

### Candidate services

| Service | Free Tier | Auth Required | Data Freshness | Currencies | Uptime | Best For |
|---------|-----------|---------------|-----------------|-----------|--------|----------|
| **[ExchangeRate-API](https://www.exchangerate-api.com/)** | 1.5K req/mo | ❌ No | Daily | 161 | 99.99% | ✅ Recommended |
| **[exchangerate.host](https://exchangerate.host/)** | 100 req/mo | ✅ Yes | Hourly | 168 | 99.9% | Limited free |
| **[Open Exchange Rates](https://openexchangerates.org/)** | 1.0K req/mo | ✅ Yes | Variable | 200+ | Claimed | Backup only |

### Recommended choice: **[ExchangeRate-API](https://www.exchangerate-api.com/)**

**Rationale**:

- **No API key required** — free tier works without authentication or credit card
- Simple REST API: `https://api.exchangerate-api.com/v4/latest/{currency}`
- 1,500 requests/month free (50/day, adequate with 1-hour cache TTL)
- Daily updates on free tier (sufficient for budget tracking)
- Covers all major currencies including SGD
- Returns rates as decimal values, no parsing required
- JSON responses with predictable structure
- 15+ years of service (since 2010), 99.99% uptime measured by Pingdom
- Used by hundreds of thousands of developers

**Response structure**:
```json
{
  "base": "USD",
  "date": "2026-02-20",
  "rates": {
    "SGD": 1.35,
    "EUR": 0.92,
    "GBP": 0.79,
    "JPY": 150.0,
    ...
  }
}
```

### Sample API requests

**Get rates for USD (reference currency)**:
```bash
curl https://api.exchangerate-api.com/v4/latest/USD
```

Response:
```json
{
  "base": "USD",
  "date": "2026-02-20",
  "rates": {
    "SGD": 1.3502,
    "EUR": 0.9187,
    "GBP": 0.7925,
    "JPY": 150.45,
    ...
  }
}
```


**Python example**:
```python
import requests

url = "https://api.exchangerate-api.com/v4/latest/USD"
response = requests.get(url, timeout=5)
data = response.json()

sgd_rate = data["rates"]["SGD"]  # 1.3502
print(f"1 USD = {sgd_rate} SGD")
```

### Configuration for API selection

Users need only specify cache TTL in `hb-config.json`:

```json
{
  "forex": {
    "cache_ttl_hours": 1
  }
}
```

This is optional; if omitted, defaults to 1-hour TTL. ExchangeRate-API is used automatically without API key or signup.

## Data structure and storage

### Cache file format

Store rates in JSON in a dedicated Forex directory:

**File**: `{HomeBudgetData}/Forex/forex-rates.json`

```json
{
  "metadata": {
    "version": 1,
    "last_update": "2026-02-20T15:30:45Z"
  },
  "timestamp": "2026-02-20T15:30:45Z",
  "base": "USD",
  "rates": {
    "SGD": 1.3502,
    "EUR": 0.9187,
    "GBP": 0.7925,
    "JPY": 150.45,
    "AUD": 1.2708,
    "CAD": 1.3550,
    ...
  }
}
```

### Purpose of structure

- **metadata**: Tracks cache version and last full update for diagnostics
- **timestamp**: Last fetch time; compared against current time for TTL validation
- **base**: Always `"USD"` — all rates are denominated in USD
- **rates**: Currency code → rate mapping for all currencies vs USD
  - Single source of truth; any currency pair can be calculated via `RATES[A] / RATES[B]`
  - Example: SGD to EUR = `RATES["SGD"] / RATES["EUR"]` = `1.3502 / 0.9187` ≈ 1.47

## Caching and TTL strategy

### TTL logic

When a user requests a rate for currency `X`:

1. **Check cache exists**: Look for `rates[X]` in the cache file
2. **Check TTL validity**: 
   - Parse `timestamp` field
   - If `current_time - timestamp < 1 hour`: Use cached rates
   - Otherwise: Fetch fresh rates from API

3. **Update on fetch**: Store new timestamp and refreshed rates
4. **Persist to disk**: Write updated cache file

Note: TTL is per-cache (all currencies share the same timestamp), not per-currency. Once any rate is stale, all rates are refreshed together.

### TTL configuration

Default: 1 hour (`cache_ttl_hours: 1`)

Rationale:

- Balances minimizing API calls with reasonable rate freshness
- Typical daily forex volatility is 0.5-2%, acceptable for budget tracking
- Aligns with common transaction batch workflows (process daily receipts)

Users can override in config:

- Aggressive caching: `cache_ttl_hours: 24`
- Conservative: `cache_ttl_hours: 0` (always fetch, subject to API limits)

### Cache initialization

On first use:

- If cache file doesn't exist, create it with empty structure
- First rate request triggers a fetch from the API

## Fallback mechanism

### Fallback scenarios

| Scenario | Behavior | Log Level |
|----------|----------|-----------|
| No cached rate exists | Attempt to fetch from API; fall back to 1.0 if fetch fails | INFO |
| API unreachable (connection error) | Return 1.0 | WARN |
| API returns HTTP error (5xx) | Return 1.0 | WARN |
| Rate is stale but no API available | Use stale rate | INFO |
| JSON parse error in cache | Clear entry, attempt fresh fetch; fall back to 1.0 if fetch fails | ERROR |
| Malformed API response | Return 1.0 | WARN |

### Rate formula for fallback

The fallback rate `1.0` represents "no conversion" (unit rate), meaning the provided amount is used as-is without adjustment. This is appropriate because:

1. **In offline mode**: User can manually correct the amount or rate later
2. **On first use**: User can verify the amount and rate in the transaction review
3. **Preserves determinism**: Same fallback value across all currency pairs, preventing confusion

### Stale rate fallback

If cache exists but is older than TTL and API fails:

- Use the stale rate instead of 1.0
- Log at INFO level: "Cache expired but using stale rate due to API failure"
- Rationale: A day-old rate is better than no conversion

## Integration points

### Client API

The `HomeBudgetClient` exposes a helper method for other code to fetch rates if needed:

```python
def get_forex_rate(
    self,
    from_currency: str,
    to_currency: str | None = None
) -> float:
    """Fetch current forex rate for a given currency pair.
    
    If to_currency is not specified, uses the account's base currency.
    Returns 1.0 if rate is unavailable (offline or not cached).
    
    Args:
        from_currency: ISO 4217 currency code (e.g., 'SGD')
        to_currency: Target currency code (optional, defaults to base currency)
        
    Returns:
        float: Exchange rate (fallback 1.0 if unavailable)
    """
```

### Shared normalization layer

The forex manager is integrated into shared normalization methods that apply to all transaction types:

- **For single updates**: `_normalize_forex_inputs()` 
- **For batch operations**: `_resolve_batch_forex_add()`
- **For currency inference**: `_infer_currency_for_*()` methods

These methods are called by all transaction operations (add/update/delete) regardless of type (expense/income/transfer).

### Handling amount-only input on non-base accounts

When a user provides only `amount` on a non-base currency account:

**Without forex rate, rate=1.0**:

- User enters: `amount=100` on USD account (base currency is SGD)
- Result: `amount=100, currency=USD, currency_amount=100, exchange_rate=1.0`
- Interpretation: 100 USD = 100 SGD (incorrect 1:1 conversion)

**With forex rate**:

- User enters: `amount=100` on USD account (amount is in USD, the account's currency)
- Fetch rate: 1 USD = 1.35 SGD
- Calculate: `amount = 100 * 1.35 = 135 SGD` (base currency)
- Result: `amount=135, currency=USD, currency_amount=100, exchange_rate=1.35`
- Interpretation: 100 USD ≈ 135 SGD at rate 1.35

### Handling amount-only input on transfers (base to non-base)

When a user provides only `amount` on a **transfer between base and non-base accounts**:

**Scenario**:

- User on base account (SGD) transfers to non-base account (USD)
- User specifies: `amount=135` (base currency, SGD)
- Transfer involves both SGD (base, from_account) and USD (foreign, to_account)

**Enhanced behavior**:

- Infer non-base currency from target account: `currency=USD`
- Fetch rate: 1 USD = 1.35 SGD
- Calculate: `currency_amount = 135 / 1.35 = 100` (WITHOUT rounding)
- Send as foreign currency transaction: `amount=135, currency=USD, currency_amount=100, exchange_rate=1.35`
- Interpretation: 100 USD ≈ 135 SGD at rate 1.35

This applies to the transfer's foreign currency leg (the non-base account side).


## Architecture

**Module structure**

```
src/python/homebudget/
  forex.py               ← New module
  client.py              ← Integrate forex manager initialization
  config.py              ← Handle forex config section (optional)
```

## Error handling

**Normal flow with graceful fallback**:

```python
def get_rate(self, currency: str) -> float:
    """Get rate, falling back to 1.0 on any failure."""
    
    # Check cache validity
    if self._is_cache_valid():
        rate = self._cache.get("rates", {}).get(currency)
        if rate:
            return float(rate)
    
    # Cache miss or stale: try to fetch fresh
    try:
        all_rates = self._fetch_from_api(currency)
        self._cache = {
            "metadata": {"version": 1, "last_update": datetime.isoformat(datetime.utcnow())},
            "timestamp": datetime.isoformat(datetime.utcnow()),
            "base": "USD",
            "rates": all_rates,
        }
        self._save_cache(self._cache)
        rate = all_rates.get(currency)
        if rate:
            return float(rate)
    except Exception as e:
        # Try to use stale rate from cache
        if self._cache and "rates" in self._cache:
            rate = self._cache["rates"].get(currency)
            if rate:
                return float(rate)
    
    # All else failed: fallback
    return 1.0
```

**Cache corruption**: Clear and retry

```python
def _load_cache(self) -> dict:
    """Load cache, clearing on corruption."""
    try:
        with open(self._cache_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        self._cache = {}
        if self._cache_path.exists():
            self._cache_path.unlink()
        return {}
```

### Exception hierarchy

```python
class ForexError(Exception):
    """Base exception for forex operations."""
    pass

class ForexAPIError(ForexError):
    """Raised when API request fails."""
    
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code

class ForexCacheError(ForexError):
    """Raised when cache I/O fails."""
    pass

class InvalidCurrencyError(ForexError):
    """Raised for invalid currency codes."""
    pass
```

## Configuration

### Config schema

Add to `hb-config.json` under `forex` key (all fields optional):

```json
{
  "forex": {
    "cache_ttl_hours": 1
  }
}
```

### Option reference

| Option | Type | Default | Purpose |
|--------|------|---------|---------|
| `cache_ttl_hours` | int | `1` | Cache validity in hours |

### Defaults

All other settings are automatically derived or hardcoded:

- **API provider**: ExchangeRate-API (free, no authentication required)
- **Cache path**: Auto-derived as `{HomeBudgetData}/Forex/forex-rates.json`
- **Fallback rate**: Always `1.0` (unit rate for no conversion)
- **Timeout**: `5` seconds for API requests
- **Offline mode**: Disabled by default

If the `forex` key is omitted entirely from config, the feature uses all defaults with 1-hour TTL. Users only need to configure `cache_ttl_hours` if they want a different caching interval.

## Appendix: Alternative API providers

### exchangerate.host (APILayer)

- **Free tier**: 100 requests/month (very limited)
- **Authentication**: Requires API key signup
- **Data freshness**: Hourly updates (more frequent than ExchangeRate-API)
- **Currencies**: 168 supported
- **Historical data**: 19 years available
- **Uptime**: 99.9%
- **Status**: Not practical for this use case due to 100 req/mo limit with typical usage

### Open Exchange Rates

- **Free tier**: 1,000 requests/month
- **Authentication**: Requires API key signup
- **Currencies**: 200+ (most comprehensive)
- **Data model**: USD-centric
- **Status**: Use as emergency fallback only if ExchangeRate-API becomes unavailable
