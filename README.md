# market-board

BTCデリバティブの一覧ボードを再現するための作業フォルダ。

## 目的
- 添付画像の雰囲気をベースにデフォルメする
- Coinalyze の収集データを元に Perp 一覧を作る

## 対象銘柄
Perp 13銘柄で固定する。

- `BTC-PERP.C` / Coinbase
- `BTC-PERPETUAL.2` / Deribit
- `BTC.H` / Hyperliquid
- `BTCPERP.6` / Bybit
- `BTCUSD.6` / Bybit
- `BTCUSDC_PERP.A` / Binance
- `BTCUSDT.6` / Bybit
- `BTCUSDT_PERP.3` / OKX
- `BTCUSDT_PERP.A` / Binance
- `BTCUSDT_PERP.F` / Bitfinex
- `BTCUSD_PERP.3` / OKX
- `BTCUSD_PERP.A` / Binance
- `pf_xbtusd.K` / Kraken

## 関連資料
- `SPEC.md`
- `coinalyze-receiver-data-reference.md`

## 環境
- Python 3.11+
- `curl`
- Termux の `python-pillow`

## セットアップ

```bash
pkg update
pkg install python python-pillow curl
```

## 実行
Coinalyze receiver の SQLite DB から実データを読み、Python で表を描画して PNG を作り、Discord に送る。

```bash
cd ~/market-board
python send.py
```

Discordへ送らずPNGのみ生成する場合:

```bash
python send.py --no-discord
```

Discord webhook は環境変数またはファイルで指定する。

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/... python send.py
DISCORD_WEBHOOK_FILE=~/webhook/MarketBoard python send.py
```

DB の場所を変更する場合:

```bash
COINALYZE_DB=/path/to/coinalyze_v2.db python send.py
```

優先される DB は `coinalyze_1min.db`、次に `coinalyze.db`、最後に `coinalyze_v2.db`。
