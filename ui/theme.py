"""Gradio theme: grainy charcoal + orange. Light and dark variants are identical
so the app always looks the same regardless of the viewer's system setting."""
import gradio as gr
from gradio.themes import Color

ORANGE = Color(
    name="nb_orange",
    c50="#fff4ea", c100="#ffe4cc", c200="#ffc79a", c300="#ffa763", c400="#ff8d3a",
    c500="#ff7a1a", c600="#e8620a", c700="#bf4b07", c800="#963b0a", c900="#7a320c", c950="#451a05",
)
CHARCOAL = Color(
    name="nb_charcoal",
    c50="#f3f1ee", c100="#e3dfda", c200="#c9c4bd", c300="#a7a198", c400="#857f76",
    c500="#625d56", c600="#4a4640", c700="#35322e", c800="#242220", c900="#1a1918", c950="#121110",
)

BG = "#141414"
SURFACE = "#1b1b1b"
SURFACE_2 = "#232323"
LINE = "rgba(255,255,255,0.09)"
TEXT = "#f3ede6"
MUTED = "#a39b91"
ACCENT = "#ff7a1a"

FONT_SANS = ["DM Sans", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"]
FONT_MONO = ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"]


def build_theme() -> gr.themes.Base:
    theme = gr.themes.Base(
        primary_hue=ORANGE,
        secondary_hue=ORANGE,
        neutral_hue=CHARCOAL,
        font=FONT_SANS,
        font_mono=FONT_MONO,
        radius_size=gr.themes.sizes.radius_lg,
        text_size=gr.themes.sizes.text_md,
    )

    both = {
        # page + surfaces
        "body_background_fill": BG,
        "body_text_color": TEXT,
        "body_text_color_subdued": MUTED,
        "background_fill_primary": SURFACE,
        "background_fill_secondary": SURFACE_2,
        "block_background_fill": "transparent",
        "block_border_color": "transparent",
        "block_label_background_fill": "transparent",
        "block_label_text_color": MUTED,
        "block_title_text_color": MUTED,
        "block_info_text_color": MUTED,
        "panel_background_fill": SURFACE,
        "panel_border_color": LINE,
        "border_color_primary": LINE,
        "border_color_accent": ACCENT,
        "color_accent_soft": "rgba(255,122,26,0.14)",
        # inputs
        "input_background_fill": "#101010",
        "input_background_fill_focus": "#101010",
        "input_background_fill_hover": "#141414",
        "input_border_color": LINE,
        "input_border_color_focus": ACCENT,
        "input_border_color_hover": "rgba(255,255,255,0.18)",
        "input_placeholder_color": "#6f685f",
        "input_shadow_focus": "0 0 0 3px rgba(255,122,26,0.18)",
        # chips (checkbox group) + segmented (radio) share these variables
        "checkbox_label_background_fill": "#1f1f1f",
        "checkbox_label_background_fill_hover": "#262626",
        "checkbox_label_background_fill_selected": "rgba(255,122,26,0.16)",
        "checkbox_label_border_color": LINE,
        "checkbox_label_border_color_hover": "rgba(255,255,255,0.2)",
        "checkbox_label_border_color_selected": ACCENT,
        "checkbox_label_text_color": "#d8d0c6",
        "checkbox_label_text_color_selected": "#ffb37a",
        "checkbox_background_color_selected": ACCENT,
        "checkbox_border_color_selected": ACCENT,
        # buttons
        "button_primary_background_fill": "linear-gradient(180deg, #ff8a35 0%, #ff7a1a 55%, #f06a0a 100%)",
        "button_primary_background_fill_hover": "linear-gradient(180deg, #ff9a4d 0%, #ff8426 55%, #f87414 100%)",
        "button_primary_border_color": "#ff9a4d",
        "button_primary_text_color": "#1a0d02",
        "button_primary_text_color_hover": "#1a0d02",
        "button_primary_shadow": "0 8px 24px -8px rgba(255,122,26,0.55), inset 0 1px 0 rgba(255,255,255,0.35)",
        "button_secondary_background_fill": "#202020",
        "button_secondary_background_fill_hover": "#292929",
        "button_secondary_border_color": "rgba(255,255,255,0.12)",
        "button_secondary_border_color_hover": "rgba(255,122,26,0.55)",
        "button_secondary_text_color": TEXT,
        "button_secondary_text_color_hover": "#ffb37a",
        "button_cancel_background_fill": "#202020",
        "button_cancel_background_fill_hover": "rgba(229,101,75,0.16)",
        "button_cancel_border_color": "rgba(255,255,255,0.12)",
        "button_cancel_border_color_hover": "rgba(229,101,75,0.6)",
        "button_cancel_text_color": TEXT,
        "button_cancel_text_color_hover": "#f19a88",
        "loader_color": ACCENT,
    }
    kwargs = {}
    for key, val in both.items():
        kwargs[key] = val
        kwargs[key + "_dark"] = val
    # Only keys that exist on Theme.set() are valid; drop the rest rather than crash across versions.
    import inspect
    valid = set(inspect.signature(theme.set).parameters)
    kwargs = {k: v for k, v in kwargs.items() if k in valid}
    return theme.set(**kwargs)
