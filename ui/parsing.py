"""Turn raw crew output (loosely-typed dicts) into clean, typed view models.

Model output is unpredictable: numbers arrive as "35g", "~450 kcal", "400-500",
fields get renamed, lists become dicts. Everything here is deliberately tolerant
and never raises on bad data - missing values just become ``None`` / empty lists.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_NUM = re.compile(r"\d[\d,]*\.?\d*")

KCAL_PER_G = {"protein": 4, "carbs": 4, "fat": 9}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def to_number(value: Any) -> Optional[float]:
    """'35g' -> 35.0, '1,200 kcal' -> 1200.0, '400-500' -> 450.0, None -> None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    nums = _NUM.findall(str(value))
    if not nums:
        return None
    try:
        vals = [float(n.replace(",", "")) for n in nums[:2]]
    except ValueError:
        return None
    # ranges like "400-500" or "400 to 500" -> midpoint
    if len(vals) == 2 and re.search(r"\d\s*(?:-|–|to)\s*\d", str(value)):
        return round(sum(vals) / 2, 1)
    return vals[0]


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _str_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = re.split(r"\n+|(?<=\.)\s+(?=[A-Z])", value)
        return [re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", p).strip() for p in parts if p.strip()]
    if isinstance(value, (list, tuple)):
        return [_text(v) for v in value if _text(v)]
    return [_text(value)]


def clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


# --------------------------------------------------------------------------- #
# Analysis
# --------------------------------------------------------------------------- #
@dataclass
class FoodItemView:
    name: str
    portion: str = ""
    calories: Optional[int] = None


@dataclass
class AnalysisView:
    dish: str = ""
    portion: str = ""
    calories: Optional[int] = None
    calories_derived: bool = False          # True when computed from macros
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    items: List[FoodItemView] = field(default_factory=list)
    vitamins: List[tuple] = field(default_factory=list)   # (name, pct_dv)
    minerals: List[tuple] = field(default_factory=list)   # (name, amount text)
    score: Optional[int] = None
    score_derived: bool = False
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    evaluation: str = ""

    @property
    def has_macros(self) -> bool:
        return any(v is not None for v in (self.protein_g, self.carbs_g, self.fat_g))

    @property
    def is_empty(self) -> bool:
        return not (self.dish or self.calories or self.has_macros or self.items or self.evaluation)

    def macro_kcal(self) -> Dict[str, float]:
        return {
            "protein": (self.protein_g or 0) * KCAL_PER_G["protein"],
            "carbs": (self.carbs_g or 0) * KCAL_PER_G["carbs"],
            "fat": (self.fat_g or 0) * KCAL_PER_G["fat"],
        }

    def macro_shares(self) -> Dict[str, float]:
        k = self.macro_kcal()
        total = sum(k.values())
        return {n: (v / total * 100 if total else 0.0) for n, v in k.items()}


def _closeness(x: float, lo: float, hi: float, falloff: float = 15.0) -> float:
    """1.0 inside [lo, hi], decaying linearly to 0 at ``falloff`` points outside."""
    if lo <= x <= hi:
        return 1.0
    d = lo - x if x < lo else x - hi
    return clamp(1 - d / falloff, 0.0, 1.0)


def derive_balance_score(view: AnalysisView) -> Optional[int]:
    """Fallback only when the model gave no score: how close the macro split is to
    common guidance (protein 15-35%, carbs 40-60%, fat 20-35% of calories)."""
    if not view.has_macros:
        return None
    s = view.macro_shares()
    score = 50 + 20 * _closeness(s["protein"], 15, 35) + 15 * _closeness(s["carbs"], 40, 60) \
        + 15 * _closeness(s["fat"], 20, 35)
    return int(round(score))


def _pick(d: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, "", []):
            return d[k]
    return None


def _parse_vitamins(raw: Any) -> List[tuple]:
    out = []
    if isinstance(raw, dict):
        raw = [{"name": k, "percentage_dv": v} for k, v in raw.items()]
    for v in raw or []:
        if isinstance(v, dict):
            name = _text(_pick(v, "name", "vitamin"))
            pct = to_number(_pick(v, "percentage_dv", "percent_dv", "dv", "amount", "value"))
        else:
            name, pct = _text(v), None
            m = re.match(r"(.+?)[:\-–]\s*(.+)", name)
            if m:
                name, pct = m.group(1).strip(), to_number(m.group(2))
        if name:
            out.append((name, pct))
    return out


def _parse_minerals(raw: Any) -> List[tuple]:
    out = []
    if isinstance(raw, dict):
        raw = [{"name": k, "amount": v} for k, v in raw.items()]
    for m in raw or []:
        if isinstance(m, dict):
            name, amount = _text(_pick(m, "name", "mineral")), _text(_pick(m, "amount", "value"))
        else:
            name, amount = _text(m), ""
            mm = re.match(r"(.+?)[:\-–]\s*(.+)", name)
            if mm:
                name, amount = mm.group(1).strip(), mm.group(2).strip()
        if name:
            out.append((name, amount))
    return out


def parse_analysis(data: Dict[str, Any]) -> AnalysisView:
    data = data or {}
    nutrients = data.get("nutrients") if isinstance(data.get("nutrients"), dict) else data

    v = AnalysisView(
        dish=_text(_pick(data, "dish", "name")),
        portion=_text(_pick(data, "portion_size", "portion")),
    )

    cal = to_number(_pick(data, "estimated_calories", "total_calories", "calories"))
    v.calories = int(round(cal)) if cal else None

    v.protein_g = to_number(_pick(nutrients, "protein", "proteins"))
    v.carbs_g = to_number(_pick(nutrients, "carbohydrates", "carbs", "carbohydrate"))
    v.fat_g = to_number(_pick(nutrients, "fats", "fat"))

    for it in data.get("items") or []:
        if isinstance(it, dict) and _text(it.get("name")):
            c = to_number(it.get("calories"))
            v.items.append(FoodItemView(_text(it["name"]), _text(it.get("portion")),
                                        int(round(c)) if c is not None else None))

    if v.calories is None and v.items and all(i.calories is not None for i in v.items):
        v.calories = sum(i.calories for i in v.items)
    if v.calories is None and v.has_macros:
        v.calories = int(round(sum(v.macro_kcal().values())))
        v.calories_derived = True

    v.vitamins = _parse_vitamins(nutrients.get("vitamins"))
    v.minerals = _parse_minerals(nutrients.get("minerals"))

    score = to_number(data.get("health_score"))
    if score is not None:
        if score <= 10 and "." in str(data.get("health_score")):   # e.g. 7.5 out of 10
            score *= 10
        v.score = int(round(clamp(score, 0, 100)))
    else:
        v.score = derive_balance_score(v)
        v.score_derived = v.score is not None

    v.strengths = _str_list(data.get("health_strengths"))
    v.improvements = _str_list(data.get("health_improvements"))
    v.evaluation = _text(data.get("health_evaluation"))
    return v


# --------------------------------------------------------------------------- #
# Recipes
# --------------------------------------------------------------------------- #
@dataclass
class RecipeView:
    title: str
    ingredients: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    calories: Optional[int] = None
    minutes: Optional[int] = None
    servings: Optional[int] = None


def split_steps(instructions: Any) -> List[str]:
    """Split a blob of instructions into steps ('1. ...', newlines, or sentences)."""
    text = _text(instructions)
    if not text:
        return []
    numbered = re.split(r"(?:^|\s)\d+[.)]\s+", text)
    numbered = [p.strip() for p in numbered if p.strip()]
    if len(numbered) > 1:
        return numbered
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if len(lines) > 1:
        return [re.sub(r"^\s*[-*•]\s*", "", l) for l in lines]
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if s.strip()]


def parse_recipes(data: Dict[str, Any]) -> List[RecipeView]:
    data = data or {}
    raw = data.get("recipes")
    if raw is None:
        nested = data.get("recipe_suggestion_task")
        raw = getattr(nested, "json_dict", {}).get("recipes") if nested is not None and hasattr(nested, "json_dict") \
            and nested.json_dict else None
    recipes: List[RecipeView] = []
    for r in raw or []:
        if not isinstance(r, dict) or not _text(_pick(r, "title", "name")):
            continue
        steps = _str_list(r.get("steps")) if r.get("steps") else split_steps(r.get("instructions"))
        cal = to_number(_pick(r, "calorie_estimate", "calories"))
        mins = to_number(_pick(r, "cook_time_minutes", "time_minutes", "time"))
        serv = to_number(r.get("servings"))
        recipes.append(RecipeView(
            title=_text(_pick(r, "title", "name")),
            ingredients=_str_list(r.get("ingredients")),
            steps=steps,
            calories=int(round(cal)) if cal else None,
            minutes=int(round(mins)) if mins else None,
            servings=int(round(serv)) if serv else None,
        ))
    return recipes
