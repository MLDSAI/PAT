from pprint import pformat

from loguru import logger
from nicegui import ui
from tqdm import tqdm

from openadapt import config
from openadapt.crud import get_latest_recording
from openadapt.events import get_events
from openadapt.utils import (
    EMPTY,
    configure_logging,
    display_event,
    image2utf8,
    row2dict,
    rows2dicts,
)

SCRUB = config.SCRUB_ENABLED
if SCRUB:
    # too many warnings from scrubbing
    __import__("warnings").filterwarnings("ignore", category=DeprecationWarning)
    from openadapt import scrub


LOG_LEVEL = "INFO"
MAX_EVENTS = None
MAX_TABLE_CHILDREN = 5
PROCESS_EVENTS = True


def create_tree(tree_dict, max_children=MAX_TABLE_CHILDREN):
    tree_data = []
    for key, value in tree_dict.items():
        if value in EMPTY:
            continue
        node = {
            "id": str(key)
            + f"{(': '  + str(value)) if not isinstance(value, (dict, list)) else ''}"
        }
        if isinstance(value, dict):
            node["children"] = create_tree(value)
        elif isinstance(value, list):
            if max_children is not None and len(value) > max_children:
                node["children"] = create_tree(
                    {i: v for i, v in enumerate(value[:max_children])}
                )
                node["children"].append({"id": "..."})
            else:
                node["children"] = create_tree({i: v for i, v in enumerate(value)})
        tree_data.append(node)
    return tree_data


def set_tree_props(tree):
    tree._props["dense"] = True
    tree._props["no-transition"] = True
    # tree._props["default-expand-all"] = True


@logger.catch
def main(recording=get_latest_recording()):
    configure_logging(logger, LOG_LEVEL)

    ui.switch(
        text="Dark Mode", value=ui.dark_mode().value, on_change=ui.dark_mode().toggle
    )

    if SCRUB:
        scrub.scrub_text(recording.task_description)
    logger.debug(f"{recording=}")

    meta = {}
    action_events = get_events(recording, process=PROCESS_EVENTS, meta=meta)
    event_dicts = rows2dicts(action_events)

    if SCRUB:
        event_dicts = scrub.scrub_list_dicts(event_dicts)
    logger.info(f"event_dicts=\n{pformat(event_dicts)}")

    recording_dict = row2dict(recording)
    if SCRUB:
        recording_dict = scrub.scrub_dict(recording_dict)

    rcolumns = []
    for key in recording_dict.keys():
        rcolumns.append(
            {
                "name": key,
                "field": key,
                "label": key,
                "sortable": False,
                "required": False,
                "align": "left",
            }
        )

    meta_col = [
        {
            "name": key,
            "field": key,
            "label": key,
            "sortable": False,
            "required": False,
            "align": "left",
        }
        for key in meta.keys()
    ]

    ui.table(rows=[meta], columns=meta_col)
    ui.table(rows=[recording_dict], columns=rcolumns)

    interactive_images = []
    action_event_trees = []
    window_event_trees = []

    logger.info(f"{len(action_events)=}")

    num_events = (
        min(MAX_EVENTS, len(action_events))
        if MAX_EVENTS is not None
        else len(action_events)
    )

    with tqdm(
        total=num_events,
        desc="Preparing HTML",
        unit="event",
        colour="green",
        dynamic_ncols=True,
    ) as progress:
        for idx, action_event in enumerate(action_events):
            if idx == MAX_EVENTS:
                break
            image = display_event(action_event)
            diff = display_event(action_event, diff=True)
            mask = action_event.screenshot.diff_mask

            if SCRUB:
                image = scrub.scrub_image(image)
                diff = scrub.scrub_image(diff)
                mask = scrub.scrub_image(mask)

            image_utf8 = image2utf8(image)
            diff_utf8 = image2utf8(diff)
            mask_utf8 = image2utf8(mask)
            width, height = image.size

            action_event_dict = row2dict(action_event)
            window_event_dict = row2dict(action_event.window_event)

            if SCRUB:
                action_event_dict = scrub.scrub_dict(action_event_dict)
                window_event_dict = scrub.scrub_dict(window_event_dict)

            with ui.column():
                with ui.row():
                    interactive_images.append(
                        ui.interactive_image(
                            source=image_utf8,
                        ).classes("drop-shadow-md rounded")
                    )
            with ui.splitter(value=60) as splitter:
                splitter.classes("w-full h-full")
                with splitter.after:
                    action_event_tree = create_tree(action_event_dict)
                    action_event_trees.append(
                        ui.tree(
                            action_event_tree,
                            label_key="id",
                            on_select=lambda e: ui.notify(e.value),
                        )
                    )
                    set_tree_props(action_event_trees[idx])
                with splitter.before:
                    ui.label("window_event_dict | action_event_dict:").style("font-weight: bold;")
                    ui.html("<br/>")
                    window_event_tree = create_tree(window_event_dict, None)

                    window_event_trees.append(
                        ui.tree(
                            window_event_tree,
                            label_key="id",
                            on_select=lambda e: ui.notify(e.value),
                        )
                    )

                    set_tree_props(window_event_trees[idx])

            progress.update()

        progress.close()

    ui.run(
        reload=False,
        title=f"OpenAdapt: recording-{recording.id}",
        favicon="📊",
        native=True,
        fullscreen=False,
    )


if __name__ == "__main__":
    main()
