"""Tiny dependency-free chart generators that return HTML / inline SVG strings.

Animations are pure CSS (see styles.css) so they work inside ``gr.HTML`` without
JavaScript. Every dynamic string is escaped.
"""
from __future__ import annotations

from html import escape as esc
from typing import List, Optional, Sequence

ORANGE = "#ff7a1a"
AMBER = "#ffc15e"
SAND = "#e6d3b3"
GREEN = "#8fbf7f"
RED = "#e5654b"


def score_color(score: float) -> str:
    return GREEN if score >= 75 else AMBER if score >= 55 else RED


def donut(segments: Sequence[dict], *, center_value: str, center_label: str, aria: str) -> str:
    """Animated donut. ``segments``: [{label, value, color}]. Gap between arcs is automatic."""
    total = sum(max(s["value"], 0) for s in segments)
    r, width = 40, 11
    track = f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="{width}"/>'
    arcs, offset = [], 0.0
    live = [s for s in segments if s["value"] > 0]
    gap = 1.2 if len(live) > 1 else 0.0
    for i, s in enumerate(live):
        pct = s["value"] / total * 100 if total else 0
        length = max(pct - gap, 0.01)
        arcs.append(
            f'<circle class="nb-arc" cx="50" cy="50" r="{r}" pathLength="100" fill="none" '
            f'stroke="{s["color"]}" stroke-width="{width}" '
            f'style="stroke-dasharray:{length:.2f} {100 - length:.2f};stroke-dashoffset:{-offset:.2f};--d:{i * 0.12:.2f}s"/>'
        )
        offset += pct
    return (
        f'<div class="nb-donut" role="img" aria-label="{esc(aria)}">'
        f'<svg viewBox="0 0 100 100" aria-hidden="true"><g transform="rotate(-90 50 50)">{track}{"".join(arcs)}</g></svg>'
        f'<div class="nb-donut-center"><span class="nb-donut-value">{esc(center_value)}</span>'
        f'<span class="nb-donut-label">{esc(center_label)}</span></div></div>'
    )


def gauge(score: float, *, label: str) -> str:
    """Semicircle score gauge, 0-100."""
    score = max(0.0, min(100.0, float(score)))
    color = score_color(score)
    return (
        f'<div class="nb-gauge" role="img" aria-label="{esc(label)}: {int(score)} out of 100">'
        f'<svg viewBox="0 0 100 58" aria-hidden="true">'
        f'<path d="M 10 52 A 40 40 0 0 1 90 52" pathLength="100" fill="none" stroke="rgba(255,255,255,.07)" '
        f'stroke-width="9" stroke-linecap="round"/>'
        f'<path class="nb-arc" d="M 10 52 A 40 40 0 0 1 90 52" pathLength="100" fill="none" stroke="{color}" '
        f'stroke-width="9" stroke-linecap="round" style="stroke-dasharray:{score:.1f} 100"/></svg>'
        f'<div class="nb-gauge-center"><span class="nb-gauge-value">{int(round(score))}</span>'
        f'<span class="nb-gauge-max">/100</span></div></div>'
    )


def dv_bar(name: str, pct: Optional[float], scale_max: float, delay: float = 0.0) -> str:
    """Daily-value bar with a tick marking 100 %."""
    if pct is None:
        return (f'<div class="nb-dv"><div class="nb-dv-top"><span>{esc(name)}</span>'
                f'<span class="nb-dv-pct nb-muted">n/a</span></div><div class="nb-dv-track"></div></div>')
    width = max(0.0, min(pct / scale_max * 100, 100))
    tick = 100 / scale_max * 100
    return (
        f'<div class="nb-dv"><div class="nb-dv-top"><span>{esc(name)}</span>'
        f'<span class="nb-dv-pct">{pct:g}<small>% DV</small></span></div>'
        f'<div class="nb-dv-track"><div class="nb-dv-fill" style="width:{width:.1f}%;--d:{delay:.2f}s"></div>'
        f'<i class="nb-dv-tick" style="left:{tick:.1f}%" title="100% Daily Value"></i></div></div>'
    )


def share_bars(rows: Sequence[dict], *, unit: str = "kcal") -> str:
    """Horizontal comparison bars. rows: [{label, value, sub?, color?}]. Scaled to the largest value."""
    vals = [r["value"] for r in rows if r.get("value") is not None]
    if not vals:
        return ""
    top = max(vals) or 1
    out = []
    for i, r in enumerate(rows):
        v = r.get("value")
        w = 0 if v is None else max(v / top * 100, 2)
        val = "—" if v is None else f"{v:,.0f}<small> {esc(unit)}</small>"
        sub = f'<em>{esc(r["sub"])}</em>' if r.get("sub") else ""
        color = r.get("color") or ORANGE
        out.append(
            f'<div class="nb-bar"><div class="nb-bar-top"><span class="nb-bar-label">{esc(r["label"])}{sub}</span>'
            f'<span class="nb-bar-val">{val}</span></div>'
            f'<div class="nb-dv-track"><div class="nb-dv-fill" style="width:{w:.1f}%;background:{color};--d:{i * 0.08:.2f}s"></div></div></div>'
        )
    return "".join(out)
