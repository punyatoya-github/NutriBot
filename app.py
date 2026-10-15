"""NutriBot - Gradio app.

Run:            python app.py
UI-only demo:   NUTRIBOT_DEMO=1 python app.py      (no API key, no calls to OpenAI)

The layout and event wiring live here; HTML rendering is in ``ui/components.py``,
the uploader logic in ``ui/uploader.py`` and the model-output parsing in ``ui/parsing.py``.
"""
import logging
import os
import queue
import shutil
import tempfile
import threading
import time
import traceback

import gradio as gr

try:  # optional: load OPENAI_API_KEY etc. from a local .env file
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # pragma: no cover
    pass

from ui import FORCE_DARK_JS, HEAD, build_theme, load_css
from ui import components as C
from ui import uploader as U
from ui.demo_data import DEMO_ANALYSIS, DEMO_RECIPES
from ui.parsing import parse_analysis, parse_recipes

logger = logging.getLogger("nutribot.app")

DEMO = os.getenv("NUTRIBOT_DEMO", "").strip().lower() in {"1", "true", "yes", "on"}
TIMEOUT_SECONDS = int(os.getenv("NUTRIBOT_TIMEOUT", "300"))

DIET_CHOICES = ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "Keto", "Low-carb", "Nut-free", "Halal"]
MODE_CHOICES = [("Nutrition analysis", "analysis"), ("Recipe ideas", "recipe")]


# --------------------------------------------------------------------------- #
# Uploader events
# --------------------------------------------------------------------------- #
def _warn(messages):
    for m in messages:
        try:
            gr.Warning(m)
        except Exception:  # outside of an event context (tests)
            logger.warning(m)


def _view(images, active, notices=()):
    """Render every uploader-related component from the (images, active) state."""
    _warn(notices)
    images = [p for p in images if os.path.exists(p)]   # cache may have been cleaned
    active = max(0, min(active, len(images) - 1)) if images else 0
    n = len(images)
    return (
        images,                                                   # images_state
        active,                                                   # active_state
        C.photos_label(n),                                        # section label
        gr.update(visible=(n == 0)),                              # empty drop zone
        gr.update(visible=(n > 0)),                               # stage + thumbs + buttons
        C.stage_html(images, active),                             # portrait stage
        gr.update(value=U.thumbnails(images, active) if n else [],
                  selected_index=active if n else None),          # thumbnails
        gr.update(interactive=n < U.MAX_IMAGES),                  # Add
        gr.update(interactive=n > 0),                             # Replace
        gr.update(interactive=n > 0),                             # Delete
        gr.update(interactive=n > 0),                             # Analyze
    )


def on_drop(files, images, active):
    images, active, notes = U.add_images(U.to_paths(files), images, active)
    return (*_view(images, active, notes), None)                  # None clears the drop zone


def on_add(files, images, active):
    images, active, notes = U.add_images(U.to_paths(files), images, active)
    return _view(images, active, notes)


def on_replace(file, images, active):
    paths = U.to_paths(file)
    images, active, notes = U.replace_image(paths[0] if paths else None, images, active)
    return _view(images, active, notes)


def on_delete(images, active):
    images, active, notes = U.delete_image(images, active)
    return _view(images, active, notes)


def on_select(evt: gr.SelectData, images, active):
    if evt.index == active:                    # echo of our own programmatic selection
        return tuple(gr.skip() for _ in range(11))
    images, active, notes = U.select_image(evt.index, images)
    return _view(images, active, notes)


# --------------------------------------------------------------------------- #
# Mode toggle
# --------------------------------------------------------------------------- #
def on_mode_change(mode):
    return C.mode_description(mode), gr.update(visible=(mode == "recipe"))


# --------------------------------------------------------------------------- #
# Run the workflow
# --------------------------------------------------------------------------- #
def _diet_list(diets, other):
    parts = list(diets or [])
    if other and other.strip():
        parts.append(other.strip())
    return parts


def _render_result(mode, data, raw, diets):
    if mode == "recipe":
        recipes = parse_recipes(data)
        if recipes:
            return C.recipes_html(recipes, diets)
    else:
        view = parse_analysis(data)
        if not view.is_empty:
            return C.analysis_html(view)
    if raw:
        return C.result_raw(raw)
    return C.result_error("Nothing to show", "The model returned an empty response. Please try again.")


def _friendly_error(exc):
    low = str(exc).lower()
    if "api key" in low or "authentication" in low or "401" in low:
        return ("OpenAI authentication failed",
                "Check that OPENAI_API_KEY is set correctly in your environment or .env file.")
    if "rate limit" in low or "429" in low or "quota" in low:
        return ("OpenAI rate limit reached", "Wait a moment and try again, or check your plan and usage limits.")
    if "model" in low and ("not found" in low or "does not exist" in low or "access" in low):
        return ("Model not available",
                "Your key cannot use the configured model. Set NUTRIBOT_VISION_MODEL / NUTRIBOT_TEXT_MODEL.")
    return ("Something went wrong", "The analysis could not be completed. Please try again in a moment.")


def run_nutribot(images, mode, diets, other_diet):
    """Generator: yields (results_html, analyze_button_update)."""
    busy, ready = gr.update(interactive=False), gr.update(interactive=True)
    if not images:
        _warn(["Add at least one photo first."])
        yield C.result_empty(), ready
        return

    diet_list = _diet_list(diets, other_diet) if mode == "recipe" else []
    dietary = ", ".join(diet_list)

    yield C.result_loading(mode, 0), busy

    # ---- demo mode: canned output, simulated stage changes -------------------
    if DEMO:
        stages = 3 if mode == "recipe" else 1
        for i in range(stages):
            time.sleep(0.9)
            yield C.result_loading(mode, i + 1), busy
        data = DEMO_RECIPES if mode == "recipe" else DEMO_ANALYSIS
        yield _render_result(mode, data, "", diet_list), ready
        return

    # ---- real run -------------------------------------------------------------
    if not os.getenv("OPENAI_API_KEY"):
        yield C.result_error(
            "OpenAI API key missing",
            "Set OPENAI_API_KEY in your environment or in a .env file, then restart the app.",
        ), ready
        return

    workdir = tempfile.mkdtemp(prefix="nutribot_")        # unique per request: no shared files
    events = queue.Queue()
    try:
        prepared = U.prepare_for_model(images, workdir)

        def worker():
            try:
                from src.crew import NutriBotAnalysisCrew, NutriBotRecipeCrew
                from src.tools import format_image_inputs

                image_arg = format_image_inputs(prepared)
                inputs = {"uploaded_image": image_arg, "dietary_restrictions": dietary, "workflow_type": mode}

                def on_done(_output):
                    events.put(("task", None))

                if mode == "recipe":
                    crew = NutriBotRecipeCrew(image_data=image_arg, dietary_restrictions=dietary, on_task_done=on_done)
                else:
                    crew = NutriBotAnalysisCrew(image_data=image_arg, on_task_done=on_done)
                output = crew.crew().kickoff(inputs=inputs)
                events.put(("done", output))
            except Exception as exc:  # noqa: BLE001 - surfaced to the UI below
                logger.error("Crew failed:\n%s", traceback.format_exc())
                events.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()

        done_tasks, started = 0, time.time()
        while True:
            try:
                kind, payload = events.get(timeout=0.5)
            except queue.Empty:
                if time.time() - started > TIMEOUT_SECONDS:
                    yield C.result_error("This is taking too long",
                                         f"No result after {TIMEOUT_SECONDS} seconds. Please try again."), ready
                    return
                continue
            if kind == "task":
                done_tasks += 1
                if mode == "recipe":
                    yield C.result_loading(mode, done_tasks), busy
            elif kind == "error":
                title, message = _friendly_error(payload)
                yield C.result_error(title, message, f"{type(payload).__name__}: {payload}"), ready
                return
            elif kind == "done":
                data = payload.to_dict() if hasattr(payload, "to_dict") else {}
                raw = getattr(payload, "raw", "") or ""
                yield _render_result(mode, data, raw, diet_list), ready
                return
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Layout
# --------------------------------------------------------------------------- #
SCROLL_TO_RESULTS_JS = """() => {
  const el = document.getElementById('nb-results');
  if (el && window.matchMedia('(max-width: 900px)').matches) {
    el.scrollIntoView({behavior: 'smooth', block: 'start'});
  }
}"""

with gr.Blocks(
    theme=build_theme(),
    css=load_css(),
    js=FORCE_DARK_JS,
    head=HEAD,
    title="NutriBot - AI nutrition assistant",
    delete_cache=(3600, 6 * 3600),     # purge uploaded photos from Gradio's cache after 6 h
) as demo:
    images_state = gr.State([])
    active_state = gr.State(0)

    gr.HTML(C.header_html(), container=False, padding=False, elem_classes=["nb-html"])

    with gr.Row(elem_classes=["nb-layout"], equal_height=False):
        # ------------------------------ inputs --------------------------------
        with gr.Column(scale=5, min_width=340, elem_classes=["nb-panel"]):
            photos_lbl = gr.HTML(C.photos_label(0), container=False, padding=False, elem_classes=["nb-html"])

            with gr.Column(visible=True, elem_classes=["nb-drop-wrap"]) as empty_col:
                dropzone = gr.File(
                    file_count="multiple", file_types=["image"], type="filepath",
                    show_label=False, container=False, elem_classes=["nb-drop"],
                )

            with gr.Column(visible=False, elem_classes=["nb-stage-wrap"]) as stage_col:
                stage = gr.HTML("", container=False, padding=False, elem_classes=["nb-html"])
                thumbs = gr.Gallery(
                    value=None, show_label=False, container=False, columns=5, rows=1, height="auto",
                    object_fit="cover", allow_preview=False, preview=False, interactive=False,
                    show_download_button=False, show_share_button=False, show_fullscreen_button=False,
                    elem_classes=["nb-thumbs"],
                )
                with gr.Row(elem_classes=["nb-actions"]):
                    add_btn = gr.UploadButton("Add", file_types=["image"], file_count="multiple",
                                              variant="secondary", elem_classes=["nb-btn", "nb-add"])
                    replace_btn = gr.UploadButton("Replace", file_types=["image"], file_count="single",
                                                  variant="secondary", elem_classes=["nb-btn", "nb-replace"])
                    delete_btn = gr.Button("Delete", variant="stop", elem_classes=["nb-btn", "nb-delete"])

            gr.HTML(C.section_label("02", "Mode"), container=False, padding=False, elem_classes=["nb-html"])
            mode = gr.Radio(MODE_CHOICES, value="analysis", show_label=False, container=False,
                            elem_classes=["nb-segmented"])
            mode_desc = gr.HTML(C.mode_description("analysis"), container=False, padding=False,
                                elem_classes=["nb-html"])

            with gr.Column(visible=False, elem_classes=["nb-diet"]) as diet_col:
                gr.HTML(C.section_label("03", "Dietary needs", "optional"), container=False, padding=False,
                        elem_classes=["nb-html"])
                diets = gr.CheckboxGroup(DIET_CHOICES, show_label=False, container=False,
                                         elem_classes=["nb-chipgroup"])
                other_diet = gr.Textbox(label="Anything else?", placeholder="e.g. no shellfish, low sodium",
                                        max_lines=1, elem_classes=["nb-field"])

            analyze_btn = gr.Button("Analyze", variant="primary", interactive=False, elem_classes=["nb-go"])

        # ------------------------------ results -------------------------------
        with gr.Column(scale=7, min_width=360):
            results = gr.HTML(C.result_empty(), container=False, padding=False,
                              elem_id="nb-results", elem_classes=["nb-html"])

    gr.HTML(C.footer_html(), container=False, padding=False, elem_classes=["nb-html"])

    # ------------------------------ wiring ---------------------------------------
    view_outputs = [images_state, active_state, photos_lbl, empty_col, stage_col, stage, thumbs,
                    add_btn, replace_btn, delete_btn, analyze_btn]

    dropzone.upload(on_drop, [dropzone, images_state, active_state], view_outputs + [dropzone],
                    show_progress="hidden")
    add_btn.upload(on_add, [add_btn, images_state, active_state], view_outputs, show_progress="hidden")
    replace_btn.upload(on_replace, [replace_btn, images_state, active_state], view_outputs, show_progress="hidden")
    delete_btn.click(on_delete, [images_state, active_state], view_outputs, show_progress="hidden")
    thumbs.select(on_select, [images_state, active_state], view_outputs, show_progress="hidden")

    mode.change(on_mode_change, mode, [mode_desc, diet_col], show_progress="hidden")

    analyze_btn.click(run_nutribot, [images_state, mode, diets, other_diet], [results, analyze_btn],
                      show_progress="hidden")
    analyze_btn.click(None, None, None, js=SCROLL_TO_RESULTS_JS)

demo.queue(default_concurrency_limit=2)

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=int(os.getenv("PORT", "5000")), show_api=False)
