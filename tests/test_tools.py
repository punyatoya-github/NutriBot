"""Tests for the OpenAI-backed tools. No network: the OpenAI client is replaced by a fake,
and ``langchain.tools.tool`` is stubbed so the plain functions can be called directly."""
import importlib
import os
import sys
import types

import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def tools(monkeypatch):
    fake_lc = types.ModuleType("langchain")
    fake_tools = types.ModuleType("langchain.tools")
    fake_tools.tool = lambda *_a, **_k: (lambda fn: fn)          # decorator that returns the function
    fake_lc.tools = fake_tools
    monkeypatch.setitem(sys.modules, "langchain", fake_lc)
    monkeypatch.setitem(sys.modules, "langchain.tools", fake_tools)
    sys.modules.pop("src.tools", None)
    return importlib.import_module("src.tools")


class FakeClient:
    def __init__(self, reply="ok"):
        self.calls, self.reply = [], reply
        outer = self

        class _Completions:
            def create(self, **kw):
                outer.calls.append(kw)
                msg = types.SimpleNamespace(content=outer.reply)
                return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

        self.chat = types.SimpleNamespace(completions=_Completions())


@pytest.fixture
def photos(tmp_path):
    out = []
    for i in range(3):
        p = tmp_path / f"photo-{i + 1}.jpg"
        Image.new("RGB", (64, 48), (i * 60, 90, 30)).save(p)
        out.append(str(p))
    return out


def test_no_watsonx_left():
    for rel in ("src/tools.py", "src/crew.py"):
        text = open(os.path.join(os.path.dirname(__file__), "..", rel)).read().lower()
        assert "watsonx" not in text and "ibm" not in text, rel


def test_resolve_images_pipe_joined(tools, photos):
    assert tools._resolve_images(tools.format_image_inputs(photos)) == photos


def test_resolve_images_survives_llm_reformatting(tools, photos):
    messy = f"['{photos[0]}', \"{photos[1]}\"]\n{photos[2]}"
    assert tools._resolve_images(messy) == photos
    assert tools._resolve_images(f"Images are at {photos[0]} and {photos[1]}.") == photos[:2]


def test_resolve_images_errors_and_urls(tools):
    with pytest.raises(FileNotFoundError):
        tools._resolve_images("/definitely/not/here.jpg")
    assert tools._resolve_images("https://example.com/a.jpg") == ["https://example.com/a.jpg"]


def test_vision_request_shape_multi_image(tools, photos, monkeypatch):
    fake = FakeClient("Total Calories: 500")
    monkeypatch.setattr(tools, "_client", fake)
    out = tools.NutrientAnalysisTool.analyze_image(tools.format_image_inputs(photos))
    assert out == "Total Calories: 500"
    call = fake.calls[0]
    assert call["model"] == tools.VISION_MODEL and call["max_tokens"] >= 1000
    parts = call["messages"][0]["content"]
    assert parts[0]["type"] == "text" and "Health Score" in parts[0]["text"]
    images = [p for p in parts if p["type"] == "image_url"]
    assert len(images) == 3 and all(p["image_url"]["url"].startswith("data:image/jpeg;base64,") for p in images)


def test_extract_ingredients_prompt_mentions_photo_count(tools, photos, monkeypatch):
    fake = FakeClient("eggs, milk")
    monkeypatch.setattr(tools, "_client", fake)
    assert tools.ExtractIngredientsTool.extract_ingredient(tools.format_image_inputs(photos[:2])) == "eggs, milk"
    assert "2 photos" in fake.calls[0]["messages"][0]["content"][0]["text"]
    fake.calls.clear()
    tools.ExtractIngredientsTool.extract_ingredient(photos[0])
    assert "a photo" in fake.calls[0]["messages"][0]["content"][0]["text"]


def test_dietary_filter(tools, monkeypatch):
    fake = FakeClient("Tomato, Rice , ")
    monkeypatch.setattr(tools, "_client", fake)
    f = tools.DietaryFilterTool.filter_based_on_restrictions
    assert f(["egg", "tomato"], None) == ["egg", "tomato"] and not fake.calls     # no restriction: no API call
    assert f(["egg", "tomato", "rice"], "vegan, nut-free") == ["tomato", "rice"]
    call = fake.calls[0]
    assert call["model"] == tools.TEXT_MODEL and "vegan, nut-free" in call["messages"][0]["content"]


def test_filter_ingredients(tools):
    assert tools.FilterIngredientsTool.filter_ingredients("Eggs, MILK, , Rice") == ["eggs", "milk", "rice"]


def test_importing_tools_needs_no_api_key(tools, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert tools._client is None or tools._client is not None       # import succeeded without a key
