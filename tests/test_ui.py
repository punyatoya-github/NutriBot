import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ui import components as C
from ui import uploader as U
from ui.demo_data import DEMO_ANALYSIS, DEMO_RECIPES, MESSY_ANALYSIS
from ui.parsing import parse_analysis, parse_recipes, split_steps, to_number


@pytest.fixture
def imgs(tmp_path):
    paths = []
    for i, size in enumerate([(800, 600), (600, 900), (1000, 1000), (300, 400), (500, 200), (640, 480), (320, 240)]):
        p = tmp_path / f"p{i}.jpg"
        Image.new("RGB", size, (40 * i % 255, 120, 60)).save(p)
        paths.append(str(p))
    return paths


# ---------------- uploader ----------------
def test_max_five_images(imgs):
    images, active, notes = U.add_images(imgs[:3], [], 0)
    assert len(images) == 3 and active == 0
    images, active, notes = U.add_images(imgs[3:7], images, active)   # 4 more -> only 2 fit
    assert len(images) == U.MAX_IMAGES == 5
    assert any("up to 5" in n for n in notes)
    assert active == 3                                                # first newly added photo


def test_cannot_add_when_full(imgs):
    images, _, _ = U.add_images(imgs[:5], [], 0)
    images2, _, notes = U.add_images(imgs[5:], images, 0)
    assert images2 == images and notes


def test_replace_keeps_count_and_position(imgs):
    images, _, _ = U.add_images(imgs[:3], [], 0)
    new, active, _ = U.replace_image(imgs[5], images, 1)
    assert len(new) == 3 and new[1] == imgs[5] and active == 1


def test_delete_adjusts_active(imgs):
    images, _, _ = U.add_images(imgs[:3], [], 0)
    images, active, _ = U.delete_image(images, 2)          # delete last -> select new last
    assert len(images) == 2 and active == 1
    images, active, _ = U.delete_image(images, 0)
    images, active, _ = U.delete_image(images, 0)
    assert images == [] and active == 0
    assert U.delete_image([], 0)[0] == []                   # deleting from empty is safe


def test_invalid_files_skipped(tmp_path, imgs):
    bad = tmp_path / "x.jpg"
    bad.write_text("not an image")
    images, _, notes = U.add_images([str(bad), imgs[0]], [], 0)
    assert images == [imgs[0]] and any("not a supported" in n for n in notes)


def test_to_paths_variants():
    class F:
        name = "/a.jpg"
    assert U.to_paths(None) == [] and U.to_paths("/x.jpg") == ["/x.jpg"]
    assert U.to_paths([F(), {"path": "/b.jpg"}, None]) == ["/a.jpg", "/b.jpg"]


def test_portrait_ratio_for_every_orientation(imgs):
    for p in imgs:
        im = U.cover_crop(p, U.STAGE_SIZE)
        assert im.size == U.STAGE_SIZE and abs(im.size[0] / im.size[1] - 0.75) < 1e-6
    thumbs = U.thumbnails(imgs[:3], 1)
    assert len(thumbs) == 3 and all(t.size == U.THUMB_SIZE for t in thumbs)


def test_prepare_for_model_caps_size_and_keeps_originals(tmp_path):
    big = tmp_path / "big.png"
    Image.new("RGBA", (4000, 3000)).save(big)
    out = U.prepare_for_model([str(big)], str(tmp_path))
    with Image.open(out[0]) as im:
        assert max(im.size) == U.MODEL_MAX_SIDE and im.mode == "RGB"
    with Image.open(big) as im:
        assert im.size == (4000, 3000)


# ---------------- parsing ----------------
def test_to_number():
    assert to_number("35g") == 35 and to_number("1,200 kcal") == 1200
    assert to_number("400-500") == 450 and to_number(None) is None and to_number("n/a") is None


def test_parse_demo_analysis():
    v = parse_analysis(DEMO_ANALYSIS)
    assert v.calories == 640 and v.protein_g == 38 and v.score == 82 and not v.score_derived
    assert len(v.items) == 4 and len(v.vitamins) == 5


def test_parse_messy_analysis_is_tolerant():
    v = parse_analysis(MESSY_ANALYSIS)
    assert v.calories == 285 and v.fat_g is None
    assert dict(v.vitamins)["Calcium"] == 20 and ("Sodium", "640 mg") in v.minerals
    assert v.score is not None and v.score_derived


def test_parse_empty_and_garbage():
    assert parse_analysis({}).is_empty and parse_analysis(None).is_empty
    assert parse_recipes({}) == [] and parse_recipes({"recipes": ["x", 3, {}]}) == []


def test_parse_recipes_both_step_formats():
    rs = parse_recipes(DEMO_RECIPES)
    assert len(rs) == 3 and len(rs[0].steps) == 4 and len(rs[1].steps) == 4   # steps list + instructions blob
    assert split_steps("1. A. 2. B. 3. C.") == ["A.", "B.", "C."]


# ---------------- html safety + rendering ----------------
def test_model_text_is_escaped():
    v = parse_analysis({"dish": "<script>alert(1)</script>", "estimated_calories": 100,
                        "health_strengths": ["<img src=x onerror=1>"]})
    html = C.analysis_html(v)
    assert "<script>" not in html and "<img src=x" not in html and "&lt;script&gt;" in html
    r = C.recipes_html(parse_recipes({"recipes": [{"title": "<b>x</b>", "ingredients": ["<i>"], "steps": ["<u>"],
                                                    "calorie_estimate": 1}]}), ["<s>"])
    assert "<b>x</b>" not in r and "<i>" not in r and "<s>" not in r


def test_renderers_produce_expected_blocks():
    a = C.analysis_html(parse_analysis(DEMO_ANALYSIS))
    for token in ["nb-donut", "nb-gauge", "nb-dv-fill", "Vitamins", "Minerals", "What is on the plate", "How to improve"]:
        assert token in a
    r = C.recipes_html(parse_recipes(DEMO_RECIPES), ["Vegan"])
    assert r.count("nb-recipe-card") == 3 and "Calories per serving" in r and "Vegan" in r
    assert r.count("<details") == 3 and r.count(" open>") == 1


def test_partial_data_does_not_crash():
    C.analysis_html(parse_analysis({"dish": "Toast"}))
    C.analysis_html(parse_analysis({"estimated_calories": 0}))
    C.recipes_html(parse_recipes({"recipes": [{"title": "Only title"}]}))
    C.result_loading("recipe", 2); C.result_loading("analysis"); C.result_error("t", "m", "d"); C.result_raw("x")
