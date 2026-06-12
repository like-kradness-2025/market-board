#!/usr/bin/env python3
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from statistics import median

COINALYZE_DATA_DIR = Path.home() / "coinalyze-receiver" / "data"
DEFAULT_DB_CANDIDATES = (
    COINALYZE_DATA_DIR / "coinalyze_1min.db",
    COINALYZE_DATA_DIR / "coinalyze.db",
    COINALYZE_DATA_DIR / "coinalyze_v2.db",
)

MARKETS = [
    ("BINANCE", "BTCUSDT_PERP.A", "base"),
    ("BINANCE", "BTCUSD_PERP.A", "usd"),
    ("BINANCE", "BTCUSDC_PERP.A", "base"),
    ("BYBIT", "BTCUSDT.6", "base"),
    ("BYBIT", "BTCUSD.6", "usd"),
    ("BYBIT", "BTCPERP.6", "base"),
    ("OKX", "BTCUSDT_PERP.3", "base"),
    ("OKX", "BTCUSD_PERP.3", "usd"),
    ("DERIBIT", "BTC-PERPETUAL.2", "usd"),
    ("HYPERLIQUID", "BTC.H", "base"),
    ("COINBASE", "BTC-PERP.C", "base"),
    ("BITFINEX", "BTCUSDT_PERP.F", "base"),
    ("KRAKEN", "pf_xbtusd.K", "base"),
]


def read_one(connection, query, parameters):
    row = connection.execute(query, parameters).fetchone()
    return row[0] if row else None


def latest_row(connection, table, symbol, cutoff):
    return connection.execute(
        f"""
        SELECT timestamp, close
        FROM {table}
        WHERE symbol = ? AND timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (symbol, cutoff),
    ).fetchone()


def change_percent(current, previous):
    if current is None or previous in (None, 0):
        return None
    return (current / previous - 1) * 100


def normalize_usd(value, price, unit):
    if value is None:
        return None
    return value if unit == "usd" else value * price


def active_oi_3days(connection, symbol, end, unit, fallback_price):
    start = end - 259200
    baseline = latest_row(connection, "open_interest", symbol, start)
    rows = connection.execute(
        """
        SELECT oi.timestamp, oi.close, bars.close AS price
        FROM open_interest AS oi
        LEFT JOIN ohlcv_bars AS bars
          ON bars.symbol = oi.symbol AND bars.timestamp = oi.timestamp
        WHERE oi.symbol = ? AND oi.timestamp > ? AND oi.timestamp <= ?
        ORDER BY oi.timestamp
        """,
        (symbol, start, end),
    ).fetchall()
    if baseline is None or not rows:
        return None

    previous = baseline["close"]
    active_oi = 0.0
    for row in rows:
        movement = abs(row["close"] - previous)
        active_oi += normalize_usd(
            movement,
            row["price"] if row["price"] is not None else fallback_price,
            unit,
        )
        previous = row["close"]
    return active_oi


def window_volume(connection, symbol, start, end):
    return read_one(
        connection,
        """
        SELECT COALESCE(SUM(volume), 0)
        FROM ohlcv_bars
        WHERE symbol = ? AND timestamp BETWEEN ? AND ?
        """,
        (symbol, start, end),
    )


def window_totals(connection, symbol, start, end):
    row = connection.execute(
        """
        SELECT
            COALESCE(SUM(volume), 0),
            COALESCE(SUM(2 * buyvolume - volume), 0)
        FROM ohlcv_bars
        WHERE symbol = ? AND timestamp BETWEEN ? AND ?
        """,
        (symbol, start, end),
    ).fetchone()
    return row[0], row[1]


def liquidation_totals(connection, symbol, start, end):
    return connection.execute(
        """
        SELECT
            COALESCE(SUM(longvolume), 0),
            COALESCE(SUM(shortvolume), 0)
        FROM liquidations
        WHERE symbol = ? AND timestamp BETWEEN ? AND ?
        """,
        (symbol, start, end),
    ).fetchone()


def resolve_db_candidates() -> tuple[Path, ...]:
    env_db = os.environ.get("COINALYZE_DB", "").strip()
    if env_db:
        return (Path(env_db).expanduser(), *DEFAULT_DB_CANDIDATES)
    return DEFAULT_DB_CANDIDATES


def build_snapshot(db_path: Path | None = None):
    candidates = (db_path,) if db_path is not None else resolve_db_candidates()
    last_error: Exception | None = None

    for candidate in candidates:
        if not candidate.exists():
            last_error = FileNotFoundError(f"Coinalyze DB not found: {candidate}")
            continue

        connection = None
        try:
            connection = sqlite3.connect(f"file:{candidate}?mode=ro", uri=True)
            connection.row_factory = sqlite3.Row
            symbols = [symbol for _, symbol, _ in MARKETS]
            placeholders = ",".join("?" for _ in symbols)
            board_timestamp = read_one(
                connection,
                f"SELECT MAX(timestamp) FROM ohlcv_bars WHERE symbol IN ({placeholders})",
                symbols,
            )
            if board_timestamp is None:
                raise RuntimeError("No OHLCV data found for configured markets")

            current_prices = {}
            previous_prices = {}
            for _, symbol, _ in MARKETS:
                current = latest_row(connection, "ohlcv_bars", symbol, board_timestamp)
                previous = latest_row(connection, "ohlcv_bars", symbol, board_timestamp - 300)
                current_prices[symbol] = current["close"] if current else None
                previous_prices[symbol] = previous["close"] if previous else None

            current_index = median(value for value in current_prices.values() if value is not None)
            previous_index = median(value for value in previous_prices.values() if value is not None)
            rows = []
            open_interest_changes = []
            net_cvd_total = 0
            liquidations_total = 0

            for exchange, symbol, unit in MARKETS:
                price_row = latest_row(connection, "ohlcv_bars", symbol, board_timestamp)
                previous_price_row = latest_row(
                    connection, "ohlcv_bars", symbol, board_timestamp - 300
                )
                if not price_row:
                    continue

                price = price_row["close"]
                previous_price = previous_price_row["close"] if previous_price_row else None
                basis = (price / current_index - 1) * 100
                previous_basis = (
                    (previous_price / previous_index - 1) * 100
                    if previous_price is not None
                    else None
                )

                funding_row = latest_row(connection, "funding_rates", symbol, board_timestamp)
                previous_funding_row = latest_row(
                    connection, "funding_rates", symbol, board_timestamp - 300
                )
                oi_row = latest_row(connection, "open_interest", symbol, board_timestamp)
                previous_oi_row = latest_row(
                    connection, "open_interest", symbol, board_timestamp - 300
                )

                current_volume, current_cvd = window_totals(
                    connection, symbol, board_timestamp - 299, board_timestamp
                )
                volume_24h = window_volume(
                    connection, symbol, board_timestamp - 86399, board_timestamp
                )
                previous_volume_24h = window_volume(
                    connection,
                    symbol,
                    board_timestamp - 86399 - 300,
                    board_timestamp - 300,
                )
                long_liq, short_liq = liquidation_totals(
                    connection, symbol, board_timestamp - 299, board_timestamp
                )

                oi = normalize_usd(oi_row["close"], price, unit) if oi_row else None
                previous_oi = (
                    normalize_usd(previous_oi_row["close"], previous_price, unit)
                    if previous_oi_row and previous_price is not None
                    else None
                )
                cvd_5m_usd = normalize_usd(current_cvd, price, unit)
                cvd_ratio = (
                    current_cvd / current_volume * 100
                    if current_volume not in (None, 0)
                    else None
                )
                active_oi = active_oi_3days(
                    connection,
                    symbol,
                    board_timestamp,
                    unit,
                    price,
                )
                previous_active_oi = active_oi_3days(
                    connection,
                    symbol,
                    board_timestamp - 300,
                    unit,
                    previous_price if previous_price is not None else price,
                )
                price_change_5m = change_percent(price, previous_price)
                if oi is not None and previous_oi is not None:
                    open_interest_changes.append(change_percent(oi, previous_oi))
                net_cvd_total += cvd_5m_usd or 0
                liquidations_total += (
                    normalize_usd(long_liq, price, unit) or 0
                ) + (normalize_usd(short_liq, price, unit) or 0)
                volume_24h_usd = normalize_usd(volume_24h, price, unit)
                previous_volume_24h_usd = normalize_usd(
                    previous_volume_24h,
                    previous_price if previous_price is not None else price,
                    unit,
                )

                rows.append(
                    {
                        "exchange": exchange,
                        "symbol": symbol,
                        "sourceTimestamp": price_row["timestamp"],
                        "indexPrice": current_index,
                        "price": price,
                        "priceChange5m": price_change_5m,
                        "basis": basis,
                        "basisChange5mBp": (
                            (basis - previous_basis) * 100
                            if previous_basis is not None
                            else None
                        ),
                        "cvdRatio": cvd_ratio,
                        "funding": funding_row["close"] if funding_row else None,
                        "fundingChange": change_percent(
                            funding_row["close"] if funding_row else None,
                            previous_funding_row["close"] if previous_funding_row else None,
                        ),
                        "openInterestUsd": oi,
                        "openInterestChange5m": change_percent(oi, previous_oi),
                        "activeOpenInterest3DaysUsd": active_oi,
                        "activeOpenInterest3DaysChange5m": change_percent(
                            active_oi,
                            previous_active_oi,
                        ),
                        "volume24hUsd": volume_24h_usd,
                        "volume24hChange5m": change_percent(
                            volume_24h_usd,
                            previous_volume_24h_usd,
                        ),
                    }
                )

            return {
                "timestamp": board_timestamp,
                "indexPrice": current_index,
                "summary": {
                    "openInterestChangeMedian": median(open_interest_changes)
                    if open_interest_changes
                    else None,
                    "netCvd5mUsd": net_cvd_total,
                    "liquidations5mUsd": liquidations_total,
                },
                "markets": rows,
            }
        except sqlite3.DatabaseError as exc:
            last_error = exc
            continue
        finally:
            if connection is not None:
                connection.close()

    if last_error is None:
        raise FileNotFoundError("No Coinalyze DB candidates found")
    raise last_error
