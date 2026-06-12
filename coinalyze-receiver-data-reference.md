# Coinalyze Receiver — 収集データリファレンス

## 収集元

**Coinalyze API** (https://api.coinalyze.net/v1)
制限: 40 calls / 60秒 (sliding window)

---

## 収集 Symbol（全21銘柄）

### Perpetual（13銘柄）

| Symbol | 取引所 | 市場 | クオート |
|--------|--------|------|----------|
| `BTC-PERP.C` | Coinbase | BTC-PERP | USDC |
| `BTC-PERPETUAL.2` | Deribit | BTC-PERPETUAL | USD |
| `BTC.H` | Hyperliquid | BTC | USD |
| `BTCPERP.6` | Bybit | BTCPERP | USDC |
| `BTCUSD.6` | Bybit | BTCUSD | USD |
| `BTCUSDC_PERP.A` | Binance | BTCUSDC | USDC |
| `BTCUSDT.6` | Bybit | BTCUSDT | USDT |
| `BTCUSDT_PERP.3` | OKX | BTC-USDT-SWAP | USDT |
| `BTCUSDT_PERP.A` | Binance | BTCUSDT | USDT |
| `BTCUSDT_PERP.F` | Bitfinex | BTCF0:USTF0 | USDT |
| `BTCUSD_PERP.3` | OKX | BTC-USD-SWAP | USD |
| `BTCUSD_PERP.A` | Binance | BTCUSD_PERP | USD |
| `pf_xbtusd.K` | Kraken | pf_xbtusd | USD |

### Spot（8銘柄）

| Symbol | 取引所 | 市場 | クオート |
|--------|--------|------|----------|
| `BTCUSD.A` | Binance | BTCUSDT | USDT |
| `BTCUSD.B` | Bitstamp | BTCUSD | USD |
| `BTCUSD.C` | Coinbase | BTC-USD | USD |
| `BTCUSD.F` | Bitfinex | BTCUSD | USD |
| `BTCUSD.K` | Kraken | XBT/USD | USD |
| `BTCUSDC.A` | Binance | BTCUSDC | USDC |
| `BTCUSDT.F` | Bitfinex | BTCUST | USDT |
| `sBTCUSDT.6` | Bybit | BTCUSDT | USDT |

---

## 収集データ種別

### 1. OHLCV Bars（`ohlcv_bars`）— 全Symbol
**間隔:** 1min | **カラム:**

| カラム | 型 | 説明 |
|--------|-----|------|
| `symbol` | TEXT | Coinalyze Symbol |
| `timestamp` | INT | Unix秒 |
| `open` | REAL | 始値 |
| `high` | REAL | 高値 |
| `low` | REAL | 安値 |
| `close` | REAL | 終値 |
| `volume` | REAL | 出来高（BTC） |
| `buyvolume` | REAL | 買い出来高（BTC） |
| `trades` | INT | 約定回数 |
| `buytrades` | INT | 買い約定回数 |

**サンプル:**
```
BTC-PERP.C | 1780287540 | 73429.6 | 73437.4 | 73403.3 | 73411.0 | 36.48 | 18.23 | 695 | 352
BTC-PERP.C | 1780287600 | 73410.9 | 73410.9 | 73371.4 | 73403.4 | 49.72 | 25.60 | 802 | 424
```

---

### 2. Open Interest（`open_interest`）— Perpのみ
**間隔:** 1min | **カラム:**

| カラム | 型 | 説明 |
|--------|-----|------|
| `symbol` | TEXT | Coinalyze Symbol |
| `timestamp` | INT | Unix秒 |
| `open` | REAL | 期首OI |
| `high` | REAL | 高値OI |
| `low` | REAL | 安値OI |
| `close` | REAL | 期末OI |

**サンプル:**
```
BTC-PERP.C | 1780287540 | 2841.60 | 2841.70 | 2839.47 | 2840.10
BTC-PERP.C | 1780287600 | 2840.10 | 2843.27 | 2839.79 | 2840.27
```

---

### 3. Funding Rate（`funding_rates`）— Perpのみ
**間隔:** 1min | **カラム:**

| カラム | 型 | 説明 |
|--------|-----|------|
| `symbol` | TEXT | Coinalyze Symbol |
| `timestamp` | INT | Unix秒 |
| `open` | REAL | 期首FR |
| `high` | REAL | 高値FR |
| `low` | REAL | 安値FR |
| `close` | REAL | 期末FR |

**サンプル:**
```
BTC-PERP.C | 1780287540 | 0.0005 | 0.0005 | 0.0005 | 0.0005
BTC-PERP.C | 1780287600 | 0.0005 | 0.0005 | 0.0005 | 0.0005
```

---

### 4. Liquidation（`liquidations`）— Perpのみ
**間隔:** 1min | **カラム:**

| カラム | 型 | 説明 |
|--------|-----|------|
| `symbol` | TEXT | Coinalyze Symbol |
| `timestamp` | INT | Unix秒 |
| `longvolume` | REAL | ロング清算量（USD） |
| `shortvolume` | REAL | ショート清算量（USD） |

**サンプル:**
```
BTCPERP.6 | 1780294860 | 0.01 | 0.0
BTCPERP.6 | 1780294980 | 0.021 | 0.0
```

---

### 5. Long-Short Ratio（`ls_ratios`）— Perpのみ
**間隔:** 15min | **カラム:**

| カラム | 型 | 説明 |
|--------|-----|------|
| `symbol` | TEXT | Coinalyze Symbol |
| `timestamp` | INT | Unix秒 |
| `ratio` | REAL | Long/Short比率 |
| `longpct` | REAL | ロング割合(%) |
| `shortpct` | REAL | ショート割合(%) |

**サンプル:**
```
BTCUSD.6 | 1780288200 | 1.266 | NULL | NULL
BTCUSD.6 | 1780289100 | 1.268 | NULL | NULL
```

---

## データフロー概要

```
Coinalyze API
  ├─ OHLCV 1min          → ohlcv_bars       (全21銘柄)
  ├─ Open Interest 1min   → open_interest    (perp 13銘柄)
  ├─ Funding Rate 1min    → funding_rates    (perp 13銘柄)
  ├─ Liquidation 1min     → liquidations     (perp 13銘柄)
  └─ Long-Short Ratio 15min → ls_ratios      (perp 13銘柄)
```

**DB:** `coinalyze_receiver/data/coinalyze_v2.db` (SQLite)
**取り込み間隔:** 1分ごとに最終1分間を増分fetch
**保持期間:** 365日（自動プルーニング）
