# market-board 仕様書

## 1. 目的
添付画像の `Bitcoin Derivatives Sheet` を、Coinalyze 由来のデータで再現しつつ、見た目はデフォルメした BTC デリバティブ一覧ボードを作る。

## 2. スコープ
- 対象は Perp 13 銘柄に固定する
- Spot は扱わない
- まずは「一覧表示」と「主要指標の可視化」を優先する
- 価格の完全一致より、情報構造と雰囲気の再現を優先する

## 3. 対象銘柄
表示対象は次の 13 銘柄とする。

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

## 4. データソース
参照元は `coinalyze-receiver/data/coinalyze_1min.db` を優先し、`coinalyze.db` と `coinalyze_v2.db` をフォールバックとする。

使用候補データ:
- `ohlcv_bars`
- `open_interest`
- `funding_rates`
- `liquidations`
- `ls_ratios`

## 5. 列構成
画像の構造を踏襲しつつ、Perp 向けに意味が通る列へ寄せる。

採用列:
- `Symbol`
- `Price`
- `Basis`
- `Basischg`
- `CVD Ratio`
- `FR`
- `FRchg`
- `OI`
- `OI3Days`
- `VOL24H`

## 6. 列の意味
- `Symbol`: `取引所-Symbol` 形式
- `Price`: 最新の約定終値または直近 close。5分前比を併記する
- `Index`: 13市場の最新価格中央値。表のヘッダー右上に表示する
- `Basis`: `Price / Index - 1` の乖離率
- `Basischg`: 現在の Basis と5分前の Basis の差（bp）
- `CVD Ratio`: 直近5分の `(Buy Volume - Sell Volume) / Total Volume × 100`
- `FR`: 最新 funding rate
- `FRchg`: 現在の funding rate と5分前の funding rate の変化率
- `OI`: 最新 OI のUSD換算値
- `OI3Days`: 直近3日間の Active OI
- `VOL24H`: 直近24時間の出来高のUSD換算値

数量単位がBTCの市場は最新価格を掛けてUSD換算する。USD建てインバース市場は取得値をUSDとして扱う。

### CVD Ratio

```text
Sell Volume = Total Volume - Buy Volume
CVD Ratio = (Buy Volume - Sell Volume) / Total Volume × 100
          = (2 × Buy Volume - Total Volume) / Total Volume × 100
```

- `+100%` に近いほど成行買い優勢
- `-100%` に近いほど成行売り優勢
- 累積CVD水準の変化率ではなく、直近5分の成行フロー偏りを表す

### Active OI
`OI3Days` は、直近72時間に動いたOIの総量として次の式で算出する。

```text
Active OI 3Days = Σ |OI(t) - OI(t-1)|
```

- OIの増加と減少をともに活動量として加算する
- 同じ建玉規模が複数回入れ替わると、現在OIを上回ることがある
- BTC数量市場は各変化時点の価格でUSD換算する
- USD建て市場はOI変化量をそのままUSDとして扱う

## 7. 表示ルール
- ダークテーマを基本とする
- `Basis` 以降は列ごとの順位でセル全体をヒートマップ表示する
- `Basis`、`Basischg`、`CVD Ratio`、`FR`、`FRchg` は正値を緑、負値を赤で表示する
- `OI`、`OI3Days`、`VOL24H` は値が大きいほど濃い緑で表示する
- 色の強度は列内の絶対値順位で決め、下位約35%は無色とする
- 中程度の値は薄く、上位の強い値だけが濃くなる非線形カーブを使う
- 重要度の低い列は薄く、重要な列は見やすくする
- 1 行ごとの情報密度は高く保つ
- モバイルでも横スクロールで崩れないことを意識する

## 8. データ更新ルール
- 最新の 1 分足を基本単位にし、表示は1分ごとに更新する
- 画像生成は Python で直接描画し、HTML / Chrome 依存は持たない
- `Price` は5分前比を併記する
- `Basischg` は5分間のBasis差をbpで表示する
- `FRchg` は5分前比の変化率を表示する
- `OI3Days` は直近72時間のOI変化を集計する
- `VOL24H` は直近24時間の出来高を集計する
- OI と funding は最新値を優先する
- 欠損値は `-` で表現する

## 9. 表示順
初期は固定順でよい。

優先案:
- Binance
- Bybit
- OKX
- Deribit
- Hyperliquid
- Coinbase
- Bitfinex
- Kraken

## 10. MVP の完了条件
- 13 銘柄が一覧で表示される
- 各列が欠けずに描画される
- 値に応じた色分けが機能する
- 画像の雰囲気に近いダークな表現になっている

## 11. 未確定事項
- 表示順を取引所順で固定するか、指標順にするか
- Coinalyze の市場別契約単位をAPIメタデータから自動判定するか
