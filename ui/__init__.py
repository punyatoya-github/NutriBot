"""NutriBot UI package: theme, styles and HTML components."""
import os
from urllib.parse import quote

from ui.theme import build_theme  # noqa: F401

_HERE = os.path.dirname(__file__)

# Google Fonts: Fraunces (serif display) + DM Sans (UI). Each has a system fallback in the CSS.
HEAD = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Fraunces:opsz,wght@9..144,400..700&family=Fraunces:ital,opsz,wght@1,9..144,400..600'
    '&family=DM+Sans:wght@400;500;600;700&display=swap">'
    '<meta name="theme-color" content="#141414">'
)

# Forces Gradio's dark class so any un-themed internals also render dark.
FORCE_DARK_JS = "() => { document.documentElement.classList.add('dark'); document.body.classList.add('dark'); }"

_GRAIN_SVG = (
    "<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'>"
    "<filter id='n' x='0' y='0' width='100%' height='100%'>"
    "<feTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/>"
    "<feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.85 0'/></filter>"
    "<rect width='100%' height='100%' filter='url(#n)'/></svg>"
)


def _svg_uri(svg: str) -> str:
    return "url(\"data:image/svg+xml," + quote(svg, safe="/:=' ") + "\")"


def _icon(paths: str) -> str:
    return _svg_uri(
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
        "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>" + paths + "</svg>"
    )


_ICONS = {
    "__ICON_PLUS__": _icon("<path d='M12 5v14M5 12h14'/>"),
    "__ICON_REPLACE__": _icon("<path d='M21 12a9 9 0 1 1-3-6.7'/><path d='M21 4v5h-5'/>"),
    "__ICON_TRASH__": _icon("<path d='M4 7h16M10 11v6M14 11v6M6 7l1 12h10l1-12M9 7V4h6v3'/>"),
    "__ICON_SPARK__": _icon("<path d='M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z'/><path d='M19 16l.7 1.8L21.5 18.5l-1.8.7L19 21l-.7-1.8-1.8-.7 1.8-.7z'/>"),
    "__ICON_UPLOAD__": _icon("<path d='M12 16V4M7 9l5-5 5 5'/><path d='M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3'/>"),
    "__ICON_CHEVRON__": _icon("<path d='M6 9l6 6 6-6'/>"),
    "__GRAIN__": _svg_uri(_GRAIN_SVG),
}


def load_css() -> str:
    """Read styles.css and inject the generated data-URIs (grain texture + icons)."""
    with open(os.path.join(_HERE, "styles.css"), "r", encoding="utf-8") as fh:
        css = fh.read()
    for token, uri in _ICONS.items():
        css = css.replace(token, uri)
    return css
