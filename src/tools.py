"""CrewAI tools used by the NutriBot agents.

All model calls go through the OpenAI API. Configure with environment variables
(see ``.env.example``):

* ``OPENAI_API_KEY``          - required
* ``NUTRIBOT_VISION_MODEL``   - multimodal model for image tasks (default ``gpt-4.1-mini``)
* ``NUTRIBOT_TEXT_MODEL``     - text model for filtering (default ``gpt-4o-mini``)
"""
import base64
import logging
import mimetypes
import os
import re
from typing import List, Optional

from langchain.tools import tool
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nutribot.tools")

VISION_MODEL = os.getenv("NUTRIBOT_VISION_MODEL", "gpt-4.1-mini")
TEXT_MODEL = os.getenv("NUTRIBOT_TEXT_MODEL", "gpt-4o-mini")

IMAGE_SEPARATOR = "|"
_IMAGE_PATH_RE = re.compile(r"(?:https?://|/|[A-Za-z]:\\)[^\s|;,'\"\]\[]+\.(?:jpe?g|png|webp|gif)", re.I)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    """Create the OpenAI client lazily so importing this module never needs a key."""
    global _client
    if _client is None:
        _client = OpenAI()  # reads OPENAI_API_KEY from the environment
    return _client


def format_image_inputs(paths: List[str]) -> str:
    """Join several image paths into the single string passed to the agents."""
    return IMAGE_SEPARATOR.join(paths)


def _resolve_images(image_input: str) -> List[str]:
    """Turn the tool input into an ordered list of local file paths / URLs.

    The agent hands us a string. It is normally ``path1|path2|...`` but language
    models sometimes re-format it (quotes, brackets, newlines, prose). Two strategies
    always run and are merged, so a partially-mangled list never loses photos:
    splitting on separators (handles paths containing spaces) and regex extraction.
    """
    text = image_input or ""
    found = {}   # path -> position in the string, to keep the original order

    def usable(candidate: str) -> bool:
        return candidate.startswith("http") or os.path.isfile(candidate)

    for chunk in re.split(r"[|\n;]", text):
        candidate = chunk.strip().strip("'\"[]").strip()
        if candidate and usable(candidate):
            found.setdefault(candidate, text.find(candidate))
    for match in _IMAGE_PATH_RE.finditer(text):
        if usable(match.group(0)):
            found.setdefault(match.group(0), match.start())

    if not found:
        raise FileNotFoundError(f"No readable image found in tool input: {image_input!r}")
    return [path for path, _pos in sorted(found.items(), key=lambda kv: kv[1])]


def _image_part(source: str) -> dict:
    """Build an OpenAI ``image_url`` content part from a URL or local file."""
    if source.startswith("http"):
        return {"type": "image_url", "image_url": {"url": source}}
    mime = mimetypes.guess_type(source)[0] or "image/jpeg"
    with open(source, "rb") as fh:
        encoded = base64.b64encode(fh.read()).decode("utf-8")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}


def _vision_chat(prompt: str, image_input: str, max_tokens: int) -> str:
    sources = _resolve_images(image_input)
    logger.info("Vision request with %d image(s) using %s", len(sources), VISION_MODEL)
    content = [{"type": "text", "text": prompt}] + [_image_part(s) for s in sources]
    response = _get_client().chat.completions.create(
        model=VISION_MODEL,
        messages=[{"role": "user", "content": content}],
        max_tokens=max_tokens,
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


class ExtractIngredientsTool():
    @tool("Extract ingredients")
    def extract_ingredient(image_input: str):
        """
        Extract ingredients from one or more food item images.

        :param image_input: The image file path(s) (local, separated by '|') or URL(s) (remote).
        :return: A comma-separated list of ingredients extracted from the images.
        """
        n = len(_resolve_images(image_input))
        prompt = (
            "You are looking at "
            + ("a photo" if n == 1 else f"{n} photos of the same kitchen, fridge, pantry or meal")
            + ". List every distinct edible ingredient or food item you can identify. "
            "Merge duplicates across photos. Return ONLY a comma-separated list of lowercase "
            "ingredient names - no quantities, no numbering, no commentary."
        )
        return _vision_chat(prompt, image_input, max_tokens=400)


class FilterIngredientsTool:
    @tool("Filter ingredients")
    def filter_ingredients(raw_ingredients: str) -> List[str]:
        """
        Processes the raw ingredient data and filters out non-food items or noise.

        :param raw_ingredients: Raw ingredients as a string.
        :return: A list of cleaned and relevant ingredients.
        """
        ingredients = [ingredient.strip().lower() for ingredient in raw_ingredients.split(',') if ingredient.strip()]
        return ingredients


class DietaryFilterTool:
    @tool("Filter based on dietary restrictions")
    def filter_based_on_restrictions(ingredients: List[str], dietary_restrictions: Optional[str] = None) -> List[str]:
        """
        Uses an LLM to filter ingredients based on dietary restrictions.

        :param ingredients: List of ingredients.
        :param dietary_restrictions: Dietary restrictions (e.g., vegan, gluten-free). Defaults to None.
        :return: Filtered list of ingredients that comply with the dietary restrictions.
        """
        if not dietary_restrictions:
            return ingredients

        prompt = f"""
        You are an AI nutritionist specialized in dietary restrictions.
        Given the following list of ingredients: {', '.join(ingredients)},
        and the dietary restriction(s): {dietary_restrictions},
        remove any ingredient that does not comply with these restrictions.
        Return only the compliant ingredients as a comma-separated list with no additional commentary.
        """
        response = _get_client().chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0,
        )
        filtered = (response.choices[0].message.content or "").strip().lower()
        return [item.strip() for item in filtered.split(',') if item.strip()]


NUTRIENT_PROMPT = """
You are an expert nutritionist. Analyze the food shown in the image(s) and answer using EXACTLY this format.
If several photos are provided, treat them as one meal (different angles or courses) and do not double count items.

1. **Identification**: List each identified food item, one per line.
2. **Portion Size & Calorie Estimation**: One bullet per item:
   - **[Food Item]**: [Portion Size], [Number of Calories] calories
3. **Total Calories**: Total Calories: [number]
4. **Nutrient Breakdown**:
   - **Protein**: [total grams]
   - **Carbohydrates**: [total grams]
   - **Fats**: [total grams]
   - **Vitamins**: list the 3-6 most significant, each with its approximate % Daily Value
   - **Minerals**: list the 3-6 most significant, each with its approximate amount
5. **Health Score**: a single integer from 0 (poor) to 100 (excellent) for overall healthiness.
6. **What's working**: 2-4 short bullet points.
7. **How to improve**: 2-4 short, actionable bullet points.
8. **Health Evaluation**: one paragraph.
9. **Disclaimer**: Include this exact text:
The nutritional information and calorie estimates provided are approximate and are based on general food data.
Actual values may vary depending on factors such as portion size, specific ingredients, preparation methods, and individual variations.
For precise dietary advice or medical guidance, consult a qualified nutritionist or healthcare provider.
"""


class NutrientAnalysisTool():
    @tool("Analyze nutritional values and calories of the dish from uploaded image")
    def analyze_image(image_input: str):
        """
        Provide a detailed nutrient breakdown and estimate the total calories of all food shown in the uploaded image(s).

        :param image_input: The image file path(s) (local, separated by '|') or URL(s) (remote).
        :return: A string with nutrient breakdown (protein, carbs, fat, etc.), health score and estimated calorie information.
        """
        return _vision_chat(NUTRIENT_PROMPT, image_input, max_tokens=1400)
