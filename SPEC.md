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
- `CVD24H`
- `FR`
- `OI`
- `OI3Days`
- `VOL24H`

## 6. 列の意味
- `Symbol`: `取引所-Symbol` 形式
- `Price`: 最新の約定終値または直近 close。5分前比を併記する
- `Index`: 13市場の最新価格中央値。表のヘッダー右上に表示する
- `Basis`: 現在価格のIndexに対する乖離率。`(現在Price / 現在Index - 1) × 100`
- `Basischg`: 5分間でBasisがどれだけ拡大・縮小したか。`現在Basis - 5分前Basis` をbpで表示する
- `CVD24H`: 直近24時間Rollingの成行買い出来高と成行売り出来高の差額。5分前のRolling値との差額を併記する
- `FR`: 最新 funding rate。表示時は `値（5分変化率）` の形式にする
- `OI`: 最新 OI のUSD換算値
- `OI3Days`: 直近3日間の Active OI
- `VOL24H`: 直近24時間の出来高のUSD換算値

数量単位がBTCの市場は最新価格を掛けてUSD換算する。USD建てインバース市場は取得値をUSDとして扱う。

### CVD24H

```text
Sell Volume = Total Volume - Buy Volume
CVD24H = Σ((Buy Volume - Sell Volume) × Price)
CVD24H 5M Delta = CVD24H(now) - CVD24H(5min ago)
```

- 正値は直近24時間で成行買い優勢、負値は成行売り優勢
- 括弧内は前回配信からの変化率ではなく、5分間の実額差を表示する
- 背景色は5分実額差の正負と列内強度を反映する
- BTC数量市場は各足の価格でUSD換算し、USD数量市場は取得値をそのまま使う

### Active OI
`OI3Days` は、現在の総OIのうち直近3日間に新規で積み上がり、現在も残っていると推定されるOIとして算出する。

```text
Active OI 3Days = Current OI - Minimum OI in last 3 days
```

- 現在OIに残っている直近3日間の積み上がり分を表す
- Active OI は現在OIを上回らない
- 集計OIから建玉ごとの作成時刻は追えないため、3日間の最小OIを基準に推定する
- BTC数量市場は算出したOI数量を現在価格でUSD換算する
- USD建て市場は算出値をそのままUSDとして扱う

## 7. 表示ルール
- ダークテーマを基本とする
- `Basis`、`Basischg` は表示値ベースでセル全体をヒートマップ表示する
- `CVD24H` は5分前のRolling値からの実額差でセル全体をヒートマップ表示する
- `Basis` は現在の乖離方向、`Basischg` は5分間の乖離変化方向に応じて正値を緑、負値を赤で表示する
- `FR` 以降の表示値は `値（5分変化率）` の形式にする
- `FR` 以降の列は、表示値そのものではなく前回比の変化率を使ってセル全体をヒートマップ表示する
- `FR` は正値を緑、負値を赤で表示する
- `OI`、`OI3Days`、`VOL24H` は前回比が大きいほど濃い緑、減少が大きいほど濃い赤で表示する
- 変化率表記は小数1桁で統一する
- 色の強度は列内の絶対値順位で決め、下位約35%は無色とする
- 中程度の値は薄く、上位の強い値だけが濃くなる非線形カーブを使う
- 重要度の低い列は薄く、重要な列は見やすくする
- 1 行ごとの情報密度は高く保つ
- モバイルでも横スクロールで崩れないことを意識する

## 8. データ更新ルール
- 最新の 1 分足を基本単位にし、表示は1分ごとに更新する
- 画像生成は Python で直接描画し、HTML / Chrome 依存は持たない
- `Price` は5分前比を併記する
- `Basischg` は相対変化率ではなく、5分間のBasis差をbpで表示する
- `FR` 以降のセルは `値（変化率）` の表記にする
- `FR` 以降のセル背景は前回比の変化率を色に反映する
- `OI3Days` は現在OIから直近72時間の最小OIを引いて算出する
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
