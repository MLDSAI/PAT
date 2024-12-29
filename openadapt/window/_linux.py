import xcffib
import xcffib.xproto
import pickle
import time

from openadapt.custom_logger import logger


def get_active_window_meta() -> dict | None:
    """Retrieve metadata of the active window using X server directly.

    Returns:
        dict or None: A dictionary containing metadata of the active window.
    """
    try:
        # Connect to the X server
        conn = xcffib.connect()
        root = conn.get_setup().roots[0].root

        # Get the _NET_ACTIVE_WINDOW atom
        atom = conn.core.InternAtom(
            False, len("_NET_ACTIVE_WINDOW"), "_NET_ACTIVE_WINDOW"
        ).reply().atom

        # Fetch the active window ID
        active_window = conn.core.GetProperty(
            False, root, atom, xcffib.xproto.Atom.WINDOW, 0, 1
        ).reply()
        if not active_window.value_len:
            return None

        window_id = int.from_bytes(active_window.value, byteorder="little")

        # Get window geometry
        geom = conn.core.GetGeometry(window_id).reply()

        return {
            "window_id": window_id,
            "x": geom.x,
            "y": geom.y,
            "width": geom.width,
            "height": geom.height,
            "title": get_window_title(conn, window_id),
        }
    except Exception as exc:
        logger.warning(f"Failed to retrieve active window metadata: {exc}")
        return None


def get_window_title(conn: xcffib.Connection, window_id: int) -> str:
    """Retrieve the title of a given window.

    Args:
        conn (xcffib.Connection): X server connection.
        window_id (int): The ID of the window.

    Returns:
        str: The title of the window, or an empty string if unavailable.
    """
    try:
        atom = conn.core.InternAtom(
            False, len("_NET_WM_NAME"), "_NET_WM_NAME"
        ).reply().atom
        title_property = conn.core.GetProperty(
            False, window_id, atom, xcffib.xproto.Atom.STRING, 0, 1024
        ).reply()
        if title_property.value_len > 0:
            return title_property.value.decode("utf-8")
    except Exception as exc:
        logger.warning(f"Failed to retrieve window title: {exc}")
    return ""


def get_active_window_state(read_window_data: bool) -> dict | None:
    """Get the state of the active window.

    Args:
        read_window_data (bool): Whether to include detailed data about the window.

    Returns:
        dict or None: A dictionary containing the state of the active window.
    """
    meta = get_active_window_meta()
    if not meta:
        return None

    if read_window_data:
        data = get_window_data(meta)
    else:
        data = {}

    state = {
        "title": meta.get("title", ""),
        "left": meta.get("x", 0),
        "top": meta.get("y", 0),
        "width": meta.get("width", 0),
        "height": meta.get("height", 0),
        "window_id": meta.get("window_id", 0),
        "meta": meta,
        "data": data,
    }
    try:
        pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as exc:
        logger.warning(f"{exc=}")
        state.pop("data")
    return state


def get_window_data(meta: dict) -> dict:
    """Retrieve detailed data for the active window.

    Args:
        meta (dict): Metadata of the active window.

    Returns:
        dict: Detailed data of the window.
    """
    # Placeholder for additional detailed data retrieval.
    return {}


def get_active_element_state(x: int, y: int) -> dict | None:
    """Get the state of the active element at the specified coordinates.

    Args:
        x (int): The x-coordinate of the element.
        y (int): The y-coordinate of the element.

    Returns:
        dict or None: A dictionary containing the state of the active element.
    """
    # Placeholder: Implement element-level state retrieval if necessary.
    return {"x": x, "y": y, "state": "placeholder"}


def main() -> None:
    """Test function for retrieving and inspecting the state of the active window."""
    time.sleep(1)

    state = get_active_window_state(read_window_data=True)
    print(state)
    pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)
    import ipdb

    ipdb.set_trace()  # noqa: E702


if __name__ == "__main__":
    main()