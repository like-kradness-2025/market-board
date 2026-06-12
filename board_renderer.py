from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

CANVAS_SIZE = (1680, 820)
BOARD_MARGIN = 18
BOARD_WIDTH = CANVAS_SIZE[0] - BOARD_MARGIN * 2
BOARD_LEFT = BOARD_MARGIN
BOARD_TOP = BOARD_MARGIN

FONT_DIR = Path(__file__).resolve().parent / "assets" / "fonts"
FONT_MONO = FONT_DIR / "DejaVuSansMono.ttf"
FONT_SANS = FONT_DIR / "NotoSans-Regular.ttf"
FONT_SANS_BOLD = FONT_DIR / "NotoSans-Bold.ttf"
FONT_NARROW_BOLD = FONT_DIR / "LiberationSansNarrow-Bold.ttf"


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if not path.exists():
        raise FileNotFoundError(f"Font not found: {path}")
    return ImageFont.truetype(str(path), size=size)


def _fonts() -> dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    return {
        "mono_11": _font(FONT_MONO, 11),
        "mono_12": _font(FONT_MONO, 12),
        "mono_13": _font(FONT_MONO, 13),
        "mono_14": _font(FONT_MONO, 14),
        "mono_15": _font(FONT_MONO, 15),
        "sans_12": _font(FONT_SANS, 12),
        "sans_13": _font(FONT_SANS, 13),
        "sans_14": _font(FONT_SANS, 14),
        "sans_16": _font(FONT_SANS, 16),
        "sans_20_bold": _font(FONT_SANS_BOLD, 20),
        "narrow_14_bold": _font(FONT_NARROW_BOLD, 14),
        "narrow_16_bold": _font(FONT_NARROW_BOLD, 16),
        "narrow_18_bold": _font(FONT_NARROW_BOLD, 18),
        "narrow_24_bold": _font(FONT_NARROW_BOLD, 24),
        "narrow_36_bold": _font(FONT_NARROW_BOLD, 36),
    }


COLORS = {
    "bg": (8, 12, 15, 255),
    "bg_soft": (12, 17, 20, 255),
    "panel": (14, 20, 24, 255),
    "panel_2": (16, 23, 28, 255),
    "line": (35, 49, 55, 255),
    "line_soft": (24, 34, 39, 255),
    "text": (215, 224, 223, 255),
    "muted": (117, 132, 138, 255),
    "cyan": (85, 217, 210, 255),
    "green": (56, 216, 155, 255),
    "red": (255, 102, 115, 255),
    "amber": (230, 189, 100, 255),
    "row_even": (13, 18, 22, 255),
    "row_odd": (15, 22, 26, 255),
    "row_hover": (20, 34, 36, 255),
}


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font,
    fill,
    anchor: str | None = None,
) -> None:
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def _fmt_signed(value: float | None, digits: int = 2, suffix: str = "") -> str:
    if value is None:
        return "-"
    return f"{value:+.{digits}f}{suffix}"


def _fmt_pct(value: float | None, digits: int = 2) -> str:
    return _fmt_signed(value, digits, "%")


def _fmt_bp(value: float | None, digits: int = 2) -> str:
    return _fmt_signed(value, digits, " bp")


def _fmt_price(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value:,.1f}"


def _fmt_compact_usd(value: float | None) -> str:
    if value is None:
        return "-"
    abs_value = abs(value)
    if abs_value >= 1e9:
        return f"${value / 1e9:+.1f}B".replace("+", "")
    if abs_value >= 1e6:
        return f"${value / 1e6:+.1f}M".replace("+", "")
    if abs_value >= 1e3:
        return f"${value / 1e3:+.1f}K".replace("+", "")
    return f"${value:,.0f}"


def _fmt_signed_compact_usd(value: float | None) -> str:
    if value is None:
        return "-"
    sign = "+" if value > 0 else "-" if value < 0 else ""
    abs_value = abs(value)
    if abs_value >= 1e9:
        return f"{sign}${abs_value / 1e9:.1f}B"
    if abs_value >= 1e6:
        return f"{sign}${abs_value / 1e6:.1f}M"
    if abs_value >= 1e3:
        return f"{sign}${abs_value / 1e3:.1f}K"
    return f"{sign}${abs_value:,.0f}"


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
        255,
    )


def _pill_fill(value: float | None, intensity: float = 0.12) -> tuple[int, int, int, int]:
    if value is None:
        return COLORS["panel"]
    color = COLORS["green"] if value >= 0 else COLORS["red"]
    return _blend(COLORS["panel"][:3], color[:3], intensity)


def _pill_text_color(value: float | None) -> tuple[int, int, int, int]:
    if value is None:
        return COLORS["muted"]
    return COLORS["green"] if value >= 0 else COLORS["red"]


def _rank_intensities(
    markets: list[dict],
    key: str,
) -> list[float]:
    values = [market.get(key) for market in markets]
    intensities = [0.0] * len(values)

    indices = [index for index, value in enumerate(values) if value is not None]
    ranked = sorted(indices, key=lambda index: abs(values[index]))
    count = len(ranked)
    for rank, index in enumerate(ranked):
        if values[index] == 0:
            continue

        percentile = (rank + 1) / count
        normalized = max(0.0, (percentile - 0.35) / 0.65)
        intensities[index] = 0.58 * normalized**2

    return intensities


def _heatmap_scales(markets: list[dict]) -> dict[str, list[float]]:
    return {
        "basis": _rank_intensities(markets, "basis"),
        "basisChange5mBp": _rank_intensities(markets, "basisChange5mBp"),
        "cvd24hChange5mUsd": _rank_intensities(
            markets,
            "cvd24hChange5mUsd",
        ),
        "fundingChange": _rank_intensities(markets, "fundingChange"),
        "openInterestChange5m": _rank_intensities(markets, "openInterestChange5m"),
        "activeOpenInterest3DaysChange5m": _rank_intensities(
            markets,
            "activeOpenInterest3DaysChange5m",
        ),
        "volume24hChange5m": _rank_intensities(markets, "volume24hChange5m"),
    }


def _heat_fill(
    row_fill: tuple[int, int, int, int],
    value: float | None,
    intensity: float,
    *,
    signed: bool,
) -> tuple[int, int, int, int]:
    if value is None or intensity <= 0:
        return row_fill
    target = COLORS["green"] if not signed or value >= 0 else COLORS["red"]
    return _blend(row_fill[:3], target[:3], intensity)


def _draw_gradient_background(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    draw.rectangle((0, 0, width, height), fill=COLORS["bg"])
    for y in range(0, height, 28):
        alpha = 9 if (y // 28) % 2 == 0 else 5
        draw.rectangle(
            (BOARD_LEFT, y, BOARD_LEFT + BOARD_WIDTH - 1, min(height, y + 1)),
            fill=(255, 255, 255, alpha),
        )


def _draw_board_frame(draw: ImageDraw.ImageDraw, right: int, bottom: int) -> None:
    draw.rectangle((BOARD_LEFT, BOARD_TOP, right, bottom), fill=COLORS["bg_soft"], outline=COLORS["line"])


def _draw_header(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.ImageFont], snapshot: dict, board_right: int) -> int:
    left = BOARD_LEFT + 20
    top = BOARD_TOP + 22

    _draw_text(draw, (left, top), "5 MINUTE MARKET PULSE", fonts["mono_12"], COLORS["cyan"])
    _draw_text(draw, (left, top + 20), "BTC PERPETUALS", fonts["narrow_36_bold"], COLORS["text"])

    meta_top = top + 22
    ref_x = board_right - 320
    upd_x = board_right - 225

    _draw_text(draw, (ref_x, meta_top), "REFERENCE", fonts["mono_11"], COLORS["muted"])
    _draw_text(draw, (ref_x, meta_top + 18), f"${_fmt_price(snapshot['indexPrice'])}", fonts["mono_14"], COLORS["text"])

    updated = datetime.fromtimestamp(snapshot["timestamp"], tz=timezone.utc).astimezone().strftime("%H:%M:%S JST")
    _draw_text(draw, (upd_x, meta_top), "UPDATED", fonts["mono_11"], COLORS["muted"])
    _draw_text(draw, (upd_x, meta_top + 18), updated, fonts["mono_14"], COLORS["text"])

    badge_w, badge_h = 90, 26
    badge_x = board_right - badge_w - 20
    badge_y = meta_top + 14
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h),
        radius=2,
        outline=COLORS["green"],
        width=1,
        fill=COLORS["bg_soft"],
    )
    draw.ellipse((badge_x + 9, badge_y + 9, badge_x + 15, badge_y + 15), fill=COLORS["green"])
    _draw_centered_text(draw, (badge_x, badge_y, badge_x + badge_w, badge_y + badge_h), "LIVE DB", fonts["mono_12"], COLORS["green"])

    return top + 84


def _draw_summary_strip(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.ImageFont], snapshot: dict, top: int, width: int) -> int:
    items = [
        ("MEDIAN OI 5M", _fmt_pct(snapshot["summary"]["openInterestChangeMedian"], 1), snapshot["summary"]["openInterestChangeMedian"]),
        ("NET CVD 5M", _fmt_compact_usd(snapshot["summary"]["netCvd5mUsd"]), snapshot["summary"]["netCvd5mUsd"]),
        ("LIQUIDATIONS 5M", _fmt_compact_usd(snapshot["summary"]["liquidations5mUsd"]), snapshot["summary"]["liquidations5mUsd"]),
        ("DOMINANT FLOW", "BUY" if snapshot["summary"]["netCvd5mUsd"] >= 0 else "SELL", snapshot["summary"]["netCvd5mUsd"]),
    ]
    strip_h = 42
    col_w = width // len(items)
    for index, (label, value, tone) in enumerate(items):
        x = BOARD_LEFT + index * col_w
        if index:
            draw.line((x, top, x, top + strip_h), fill=COLORS["line"], width=1)
        _draw_text(draw, (x + 16, top + 11), label, fonts["mono_11"], COLORS["muted"])
        fill = COLORS["green"] if (label == "DOMINANT FLOW" and value == "BUY") or (label != "DOMINANT FLOW" and tone is not None and tone >= 0) else COLORS["red"]
        if label == "DOMINANT FLOW":
            fill = COLORS["green"] if value == "BUY" else COLORS["red"]
        _draw_text(draw, (x + col_w - 16, top + 11), value, fonts["mono_14"], fill, anchor="ra")
    draw.line((BOARD_LEFT, top + strip_h, BOARD_LEFT + width, top + strip_h), fill=COLORS["line"], width=1)
    return top + strip_h


def _draw_table_header(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.ImageFont], top: int, col_x: list[int], col_w: list[int]) -> int:
    header_h = 56
    table_right = BOARD_LEFT + sum(col_w) + len(col_w) - 1
    draw.rectangle((BOARD_LEFT, top, table_right, top + header_h), fill=COLORS["bg_soft"])
    titles = [
        ("SYMBOL", None),
        ("PRICE", "5M Δ"),
        ("BASIS", "CURRENT %"),
        ("BASIS CHG", "5M Δ BP"),
        ("CVD24H", "5M Δ"),
        ("FR", None),
        ("OI", None),
        ("OI3DAYS", "ACTIVE OI"),
        ("VOL24H", None),
    ]
    for i, (label, sublabel) in enumerate(titles):
        x = col_x[i]
        w = col_w[i]
        if i:
            draw.line((x, top, x, top + header_h), fill=COLORS["line_soft"], width=1)
        _draw_text(draw, (x + 12, top + 17), label, fonts["mono_12"], COLORS["muted"])
        if sublabel:
            _draw_text(draw, (x + w - 12, top + 36), sublabel, fonts["mono_11"], COLORS["muted"], anchor="ra")
    draw.line((BOARD_LEFT, top + header_h, table_right, top + header_h), fill=COLORS["line"], width=1)
    return top + header_h


def _draw_pill(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font,
    value: float | None,
) -> None:
    draw.rounded_rectangle(box, radius=2, fill=_pill_fill(value), outline=_pill_text_color(value))
    _draw_centered_text(draw, box, text, font, COLORS["text"])


def _draw_centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    text: str,
    font,
    fill,
) -> None:
    text_box = draw.textbbox((0, 0), text, font=font)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    x = box[0] + (box[2] - box[0] - text_w) / 2 - text_box[0]
    y = box[1] + (box[3] - box[1] - text_h) / 2 - text_box[1]
    draw.text((x, y), text, font=font, fill=fill)


def _value_with_change(value: str, change: float | None, digits: int = 1) -> str:
    if change is None:
        return value
    return f"{value} ({_fmt_pct(change, digits)})"


def _value_with_amount_change(value: str, change: float | None) -> str:
    if change is None:
        return value
    return f"{value} ({_fmt_signed_compact_usd(change)})"


def _draw_rows(
    draw: ImageDraw.ImageDraw,
    fonts: dict[str, ImageFont.ImageFont],
    markets: Iterable[dict],
    top: int,
    col_x: list[int],
    col_w: list[int],
) -> int:
    row_h = 44
    table_left = BOARD_LEFT
    table_right = BOARD_LEFT + sum(col_w) + len(col_w) - 1
    market_rows = list(markets)
    heatmap = _heatmap_scales(market_rows)
    heat_columns = (
        (2, "basis", True),
        (3, "basisChange5mBp", True),
        (4, "cvd24hChange5mUsd", True),
        (5, "fundingChange", True),
        (6, "openInterestChange5m", True),
        (7, "activeOpenInterest3DaysChange5m", True),
        (8, "volume24hChange5m", True),
    )

    for row_index, market in enumerate(market_rows):
        y = top + row_index * row_h
        row_fill = COLORS["row_even"] if row_index % 2 == 0 else COLORS["row_odd"]
        draw.rectangle((table_left, y, table_right, y + row_h), fill=row_fill)

        for column_index, key, signed in heat_columns:
            x = col_x[column_index]
            draw.rectangle(
                (x, y, x + col_w[column_index], y + row_h),
                fill=_heat_fill(
                    row_fill,
                    market.get(key),
                    heatmap[key][row_index],
                    signed=signed,
                ),
            )

        for x in col_x[1:]:
            draw.line((x, y, x, y + row_h), fill=COLORS["line_soft"], width=1)
        draw.line((table_left, y, table_right, y), fill=COLORS["line_soft"], width=1)

        _draw_text(draw, (col_x[0] + 12, y + 13), f'{market["exchange"]}-{market["symbol"]}', fonts["narrow_18_bold"], COLORS["text"])

        price_text = _fmt_price(market["price"])
        price_delta = _fmt_pct(market["priceChange5m"], 1)
        delta_w = 64
        delta_h = 26
        delta_x = col_x[1] + col_w[1] - delta_w - 10
        delta_y = y + 9
        _draw_text(draw, (col_x[1] + 10, y + 13), price_text, fonts["mono_15"], COLORS["text"])
        _draw_pill(draw, (delta_x, delta_y, delta_x + delta_w, delta_y + delta_h), price_delta, fonts["mono_11"], market["priceChange5m"])

        _draw_text(
            draw,
            (col_x[2] + col_w[2] - 12, y + 13),
            _fmt_pct(market["basis"], 2),
            fonts["mono_14"],
            COLORS["text"],
            anchor="ra",
        )
        _draw_text(
            draw,
            (col_x[3] + col_w[3] - 12, y + 13),
            _fmt_bp(market["basisChange5mBp"], 1),
            fonts["mono_14"],
            COLORS["text"],
            anchor="ra",
        )

        cvd_text = _value_with_amount_change(
            _fmt_signed_compact_usd(market["cvd24hUsd"]),
            market.get("cvd24hChange5mUsd"),
        )
        _draw_text(draw, (col_x[4] + col_w[4] - 12, y + 13), cvd_text, fonts["mono_13"], COLORS["text"], anchor="ra")
        fr_text = _value_with_change(_fmt_pct(market["funding"], 4), market.get("fundingChange"), 1)
        _draw_text(draw, (col_x[5] + col_w[5] - 12, y + 13), fr_text, fonts["mono_13"], COLORS["text"], anchor="ra")

        oi_text = _value_with_change(
            _fmt_compact_usd(market["openInterestUsd"]),
            market.get("openInterestChange5m"),
            1,
        )
        _draw_text(draw, (col_x[6] + col_w[6] - 12, y + 13), oi_text, fonts["mono_13"], COLORS["text"], anchor="ra")

        aoi_text = _value_with_change(
            _fmt_compact_usd(market["activeOpenInterest3DaysUsd"]),
            market.get("activeOpenInterest3DaysChange5m"),
            1,
        )
        _draw_text(draw, (col_x[7] + col_w[7] - 12, y + 13), aoi_text, fonts["mono_13"], COLORS["text"], anchor="ra")

        vol_text = _value_with_change(
            _fmt_compact_usd(market["volume24hUsd"]),
            market.get("volume24hChange5m"),
            1,
        )
        _draw_text(draw, (col_x[8] + col_w[8] - 12, y + 13), vol_text, fonts["mono_13"], COLORS["text"], anchor="ra")

    bottom = top + len(market_rows) * row_h
    draw.line((table_left, bottom, table_right, bottom), fill=COLORS["line"], width=1)
    return bottom


def _footer(draw: ImageDraw.ImageDraw, fonts: dict[str, ImageFont.ImageFont], top: int, width: int, count: int) -> None:
    left = BOARD_LEFT + 16
    right = BOARD_LEFT + width - 16
    _draw_text(draw, (left, top + 12), f"{count} PERPETUAL MARKETS", fonts["mono_11"], COLORS["muted"])
    _draw_text(draw, (right, top + 12), "Source: Coinalyze receiver SQLite", fonts["mono_11"], COLORS["muted"], anchor="ra")


def render_market_board(snapshot: dict, output_path: Path) -> Path:
    image = Image.new("RGBA", CANVAS_SIZE, COLORS["bg"])
    draw = ImageDraw.Draw(image)
    fonts = _fonts()

    _draw_gradient_background(draw, *CANVAS_SIZE)

    board_right = BOARD_LEFT + BOARD_WIDTH - 1
    header_top = BOARD_TOP + 1
    _draw_board_frame(draw, board_right, CANVAS_SIZE[1] - BOARD_TOP - 1)

    content_top = _draw_header(draw, fonts, snapshot, board_right)
    summary_top = _draw_summary_strip(draw, fonts, snapshot, content_top, BOARD_WIDTH - 2)

    # Fill the board width while reserving space for value-plus-change cells.
    col_w = [260, 200, 125, 135, 195, 180, 175, 180, 186]
    col_x = [BOARD_LEFT]
    for width in col_w[:-1]:
        col_x.append(col_x[-1] + width + 1)

    table_top = _draw_table_header(draw, fonts, summary_top, col_x, col_w)
    table_bottom = _draw_rows(draw, fonts, snapshot["markets"], table_top, col_x, col_w)
    _footer(draw, fonts, table_bottom, BOARD_WIDTH, len(snapshot["markets"]))

    image = image.convert("RGB")
    image.save(output_path)
    return output_path
