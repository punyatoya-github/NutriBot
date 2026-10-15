"""HTML builders for every visual block of the app (header, uploader stage, results...).

Rules: every dynamic value goes through ``esc``; no JavaScript; all motion is CSS.
"""
from __future__ import annotations

from html import escape as esc
from typing import List, Optional, Sequence

from ui import charts
from ui.parsing import AnalysisView, RecipeView
from ui.uploader import MAX_IMAGES, stage_data_uri

DISCLAIMER = ("Estimates are generated from photos by an AI model and are approximate. "
              "They are not medical or dietary advice - consult a qualified professional for personal guidance.")

PLATE_SVG = (
    '<svg viewBox="0 0 120 120" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
    'stroke-linejoin="round" aria-hidden="true"><circle cx="60" cy="60" r="38"/><circle cx="60" cy="60" r="26" '
    'opacity=".45"/><path d="M14 30v22a6 6 0 0 0 12 0V30M20 30v62M106 30c-8 4-10 14-10 24 0 6 4 8 10 8V30zM106 62v30"/></svg>'
)
MARK_SVG = (
    '<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="15" fill="#ff7a1a"/>'
    '<path d="M16 7c-1 3-4 4-4 8a4 4 0 0 0 8 0c0-4-3-5-4-8z" fill="#1a1109"/>'
    '<path d="M16 22v4" stroke="#1a1109" stroke-width="2" stroke-linecap="round"/></svg>'
)


def _fmt_int(n: Optional[float]) -> str:
    return "—" if n is None else f"{int(round(n)):,}"


# --------------------------------------------------------------------------- #
# Page chrome
# --------------------------------------------------------------------------- #
def header_html() -> str:
    return (
        '<header class="nb-header">'
        f'<div class="nb-brand"><span class="nb-mark">{MARK_SVG}</span><span class="nb-word">Nutri<em>Bot</em></span></div>'
        '<h1 class="nb-title">Know what is on <em>your plate.</em></h1>'
        '<p class="nb-sub">Snap a photo. Get calories, macros and a health read in seconds - '
        'or turn the contents of your fridge into dinner.</p>'
        '<ol class="nb-steps" aria-label="How it works">'
        '<li><b>01</b><span>Add photos</span></li>'
        '<li><b>02</b><span>Choose a mode</span></li>'
        '<li><b>03</b><span>Get insights</span></li></ol></header>'
    )


def footer_html() -> str:
    return '<p class="nb-footer">NutriBot - a portfolio project built with Gradio, CrewAI and OpenAI.</p>'


def section_label(num: str, title: str, note: str = "") -> str:
    note_html = f'<span class="nb-label-note">{esc(note)}</span>' if note else ""
    return (f'<div class="nb-label"><span class="nb-label-num">{esc(num)}</span>'
            f'<span class="nb-label-text">{esc(title)}</span>{note_html}</div>')


def photos_label(count: int) -> str:
    return section_label("01", "Photos", f"{count} / {MAX_IMAGES}")


def mode_description(mode: str) -> str:
    if mode == "recipe":
        text = "Photograph your fridge or ingredients. Get recipes that respect your dietary needs."
    else:
        text = "Photograph a finished dish. Get calories, macros, vitamins and a health score."
    return f'<p class="nb-hint">{esc(text)}</p>'


# --------------------------------------------------------------------------- #
# Uploader stage (portrait, fixed 3:4)
# --------------------------------------------------------------------------- #
def stage_html(images: Sequence[str], active: int) -> str:
    if not images:
        return ""
    active = max(0, min(active, len(images) - 1))
    src = stage_data_uri(images[active])
    return (
        '<div class="nb-stage">'
        '<div class="nb-frame">'
        f'<img src="{src}" alt="Uploaded photo {active + 1} of {len(images)}">'
        f'<span class="nb-badge">{active + 1} / {len(images)}</span>'
        '<i class="nb-corner tl"></i><i class="nb-corner tr"></i><i class="nb-corner bl"></i><i class="nb-corner br"></i>'
        '</div>'
        '<p class="nb-stage-note">Preview is cropped to 3:4 - the full photo is analysed.</p>'
        '</div>'
    )


# --------------------------------------------------------------------------- #
# Result states
# --------------------------------------------------------------------------- #
def result_empty() -> str:
    return (
        '<section class="nb-card nb-state nb-empty">'
        f'<div class="nb-state-icon">{PLATE_SVG}</div>'
        '<h3>Your results will appear here</h3>'
        '<p>Add a photo, pick a mode and press <b>Analyze</b>. '
        'Nutrition mode shows calories, macros, vitamins and a health score; '
        'Recipe mode suggests dishes from what it sees.</p>'
        '<ul class="nb-chips nb-chips-static"><li>Calories</li><li>Macros</li><li>Vitamins</li>'
        '<li>Health score</li><li>Recipes</li></ul></section>'
    )


_RECIPE_STAGES = ["Detecting ingredients", "Applying dietary filters", "Creating recipes"]


def result_loading(mode: str, done: int = 0) -> str:
    """Skeleton + honest progress. Recipe mode has 3 real tasks; analysis is a single step."""
    if mode == "recipe":
        items = []
        for i, name in enumerate(_RECIPE_STAGES):
            cls = "done" if i < done else "active" if i == done else ""
            items.append(f'<li class="{cls}"><span class="nb-dot"></span>{esc(name)}</li>')
        stages = f'<ol class="nb-stages">{"".join(items)}</ol>'
        title = "Cooking up ideas"
    else:
        stages = ('<ol class="nb-stages"><li class="active"><span class="nb-dot"></span>'
                  'Reading your photo and estimating nutrition</li></ol>')
        title = "Analysing your meal"
    return (
        '<section class="nb-card nb-state nb-loading" aria-live="polite">'
        f'<h3>{esc(title)}</h3>{stages}'
        '<div class="nb-skel nb-skel-lg"></div><div class="nb-skel-row"><div class="nb-skel"></div>'
        '<div class="nb-skel"></div></div><div class="nb-skel nb-skel-md"></div></section>'
    )


def result_error(title: str, message: str, detail: str = "") -> str:
    detail_html = (f'<details class="nb-details"><summary>Technical details</summary>'
                   f'<pre>{esc(detail)}</pre></details>') if detail else ""
    return (
        '<section class="nb-card nb-state nb-error" role="alert">'
        '<div class="nb-state-icon nb-err-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<circle cx="12" cy="12" r="9"/><path d="M12 7v6M12 16.5v.5"/></svg></div>'
        f'<h3>{esc(title)}</h3><p>{esc(message)}</p>{detail_html}</section>'
    )


def result_raw(text: str) -> str:
    return (
        '<section class="nb-card nb-state">'
        '<h3>Here is the raw response</h3>'
        '<p>The model answered in a format the app could not turn into charts, so it is shown as plain text.</p>'
        f'<pre class="nb-raw">{esc(text)}</pre></section>'
    )


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
def _verdict(score: int) -> str:
    return ("Excellent" if score >= 85 else "Very good" if score >= 70
            else "Fair" if score >= 55 else "Needs balance")


def _card(inner: str, i: int, extra: str = "") -> str:
    return f'<article class="nb-card {extra}" style="--i:{i}">{inner}</article>'


def analysis_html(v: AnalysisView) -> str:
    cards: List[str] = []
    n = 0

    # Hero (calories) + score ------------------------------------------------
    pct_day = f"≈ {v.calories / 2000 * 100:.0f}% of a 2,000 kcal day" if v.calories else ""
    derived = '<span class="nb-pill">estimated from macros</span>' if v.calories_derived else ""
    hero = (
        '<div class="nb-eyebrow">Estimated calories</div>'
        f'<div class="nb-big"><span>{_fmt_int(v.calories)}</span><small>kcal</small></div>'
        f'<div class="nb-pills">{f"<span class=nb-pill>{esc(pct_day)}</span>" if pct_day else ""}{derived}</div>'
    )
    top = [_card(hero, n, "nb-hero-card")]
    n += 1
    if v.score is not None:
        label = "Macro balance (estimated)" if v.score_derived else "Health score"
        score_inner = (
            f'<div class="nb-eyebrow">{esc(label)}</div>{charts.gauge(v.score, label=label)}'
            f'<div class="nb-verdict" style="color:{charts.score_color(v.score)}">{esc(_verdict(v.score))}</div>'
        )
        top.append(_card(score_inner, n, "nb-score-card"))
        n += 1
    cards.append(f'<div class="nb-grid nb-grid-{len(top)}">{"".join(top)}</div>')

    # Macros ------------------------------------------------------------------
    if v.has_macros:
        shares = v.macro_shares()
        rows = [("Protein", v.protein_g, shares["protein"], charts.ORANGE),
                ("Carbohydrates", v.carbs_g, shares["carbs"], charts.AMBER),
                ("Fat", v.fat_g, shares["fat"], charts.SAND)]
        segs = [{"label": r[0], "value": r[2], "color": r[3]} for r in rows]
        total_g = sum(g or 0 for _, g, _, _ in rows)
        aria = "Macro split: " + ", ".join(f"{r[0]} {r[2]:.0f} percent" for r in rows)
        legend = "".join(
            f'<li><span class="nb-swatch" style="background:{c}"></span><span class="nb-leg-name">{esc(name)}</span>'
            f'<span class="nb-leg-g">{"—" if g is None else f"{g:g} g"}</span>'
            f'<span class="nb-leg-pct">{pct:.0f}%</span></li>'
            for name, g, pct, c in rows
        )
        inner = (
            '<div class="nb-card-title">Macronutrients<small>share of calories</small></div>'
            '<div class="nb-macro">'
            f'{charts.donut(segs, center_value=f"{total_g:.0f} g", center_label="total", aria=aria)}'
            f'<ul class="nb-legend">{legend}</ul></div>'
        )
        cards.append(_card(inner, n))
        n += 1

    # Per-item breakdown ------------------------------------------------------
    if len(v.items) > 1 and any(i.calories is not None for i in v.items):
        rows = [{"label": i.name, "value": i.calories, "sub": i.portion} for i in v.items]
        cards.append(_card('<div class="nb-card-title">What is on the plate<small>calories per item</small></div>'
                           + charts.share_bars(rows), n))
        n += 1

    # Vitamins + minerals -----------------------------------------------------
    cols = []
    if v.vitamins:
        known = [p for _, p in v.vitamins if p is not None]
        scale = max([100.0] + known)
        bars = "".join(charts.dv_bar(name, pct, scale, i * 0.06) for i, (name, pct) in enumerate(v.vitamins))
        cols.append(f'<div><div class="nb-card-title">Vitamins<small>% daily value</small></div>{bars}</div>')
    if v.minerals:
        chips = "".join(
            f'<li><span>{esc(name)}</span><b>{esc(amount) if amount else "—"}</b></li>' for name, amount in v.minerals
        )
        cols.append(f'<div><div class="nb-card-title">Minerals<small>approx. amount</small></div>'
                    f'<ul class="nb-minerals">{chips}</ul></div>')
    if cols:
        cards.append(_card(f'<div class="nb-split nb-split-{len(cols)}">{"".join(cols)}</div>', n))
        n += 1

    # Health evaluation -------------------------------------------------------
    if v.strengths or v.improvements or v.evaluation:
        parts = ['<div class="nb-card-title">Health evaluation</div>']
        if v.evaluation:
            parts.append(f'<p class="nb-prose">{esc(v.evaluation)}</p>')
        lists = []
        if v.strengths:
            li = "".join(f"<li>{esc(s)}</li>" for s in v.strengths)
            lists.append(f'<div class="nb-points nb-good"><h4>What is working</h4><ul>{li}</ul></div>')
        if v.improvements:
            li = "".join(f"<li>{esc(s)}</li>" for s in v.improvements)
            lists.append(f'<div class="nb-points nb-improve"><h4>How to improve</h4><ul>{li}</ul></div>')
        if lists:
            parts.append(f'<div class="nb-split nb-split-{len(lists)}">{"".join(lists)}</div>')
        cards.append(_card("".join(parts), n))
        n += 1

    head = (
        '<header class="nb-res-head"><div class="nb-eyebrow">Nutrition analysis</div>'
        f'<h2>{esc(v.dish or "Your meal")}</h2>'
        f'{f"<p>{esc(v.portion)}</p>" if v.portion else ""}</header>'
    )
    return f'<section class="nb-result" id="nb-result">{head}{"".join(cards)}<p class="nb-disclaimer">{esc(DISCLAIMER)}</p></section>'


# --------------------------------------------------------------------------- #
# Recipes
# --------------------------------------------------------------------------- #
def recipes_html(recipes: Sequence[RecipeView], diets: Optional[Sequence[str]] = None) -> str:
    diets = [d for d in (diets or []) if d]
    diet_html = "".join(f"<li>{esc(d)}</li>" for d in diets) if diets else "<li>No dietary filter</li>"
    noun = "recipe idea" if len(recipes) == 1 else "recipe ideas"
    head = (
        '<header class="nb-res-head"><div class="nb-eyebrow">Recipe ideas</div>'
        f'<h2>{len(recipes)} {noun} for you</h2>'
        f'<ul class="nb-chips nb-chips-static">{diet_html}</ul></header>'
    )
    cards: List[str] = []
    n = 0

    if len([r for r in recipes if r.calories]) >= 2:
        rows = [{"label": r.title, "value": r.calories} for r in recipes]
        cards.append(_card('<div class="nb-card-title">Calories per serving<small>compare your options</small></div>'
                           + charts.share_bars(rows), n))
        n += 1

    for idx, r in enumerate(recipes, 1):
        meta = []
        if r.calories:
            meta.append(f'<span class="nb-pill nb-pill-hot">{_fmt_int(r.calories)} kcal</span>')
        if r.minutes:
            meta.append(f'<span class="nb-pill">{r.minutes} min</span>')
        if r.servings:
            meta.append(f'<span class="nb-pill">{r.servings} serving{"s" if r.servings != 1 else ""}</span>')
        meta.append(f'<span class="nb-pill">{len(r.ingredients)} ingredients</span>')

        ing = "".join(
            f'<li><label><input type="checkbox"><span class="nb-check"></span><span class="nb-ing">{esc(x)}</span></label></li>'
            for x in r.ingredients
        )
        steps = "".join(f"<li>{esc(s)}</li>" for s in r.steps)
        steps_block = (f'<section><h4>Method</h4><ol class="nb-method">{steps}</ol></section>'
                       if steps else '<section><h4>Method</h4><p class="nb-muted">No steps were returned.</p></section>')
        open_attr = " open" if idx == 1 else ""
        card = (
            f'<details class="nb-recipe"{open_attr}><summary>'
            f'<span class="nb-num">{idx:02d}</span>'
            f'<span class="nb-sum-main"><span class="nb-recipe-title">{esc(r.title)}</span>'
            f'<span class="nb-pills">{"".join(meta)}</span></span>'
            '<span class="nb-chev" aria-hidden="true"></span></summary>'
            f'<div class="nb-recipe-body"><section><h4>Ingredients</h4><ul class="nb-checks">{ing}</ul></section>'
            f'{steps_block}</div></details>'
        )
        cards.append(_card(card, n, "nb-recipe-card"))
        n += 1

    return f'<section class="nb-result" id="nb-result">{head}{"".join(cards)}<p class="nb-disclaimer">{esc(DISCLAIMER)}</p></section>'
