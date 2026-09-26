"""windows -- cross-plugin registry of Caroline's own currently-open
windows (embedded browser tabs + viewer/editor windows), each with the
reason she opened it. See app/window_registry.py's own docstring for why
this exists and its limits (viewer-window tracking is best-effort;
browser-window tracking is reconciled below against AppBrowserHost's real
live list, the one case where an independent ground truth exists)."""

from __future__ import annotations

import json
from typing import Any

from app.plugins.app_browser_plugin import list_app_browsers
from app.plugins.loader import Plugin, PluginTool
from app.session_context import get_tab_id
from app.window_registry import list_windows
from app.workspace_dir import WORKSPACE_DIR

_TAB_LIST_PATH = "companion-tab-list.json"


def _tab_display_name(tab_id: str | None) -> str:
    """Best-effort tab_id -> the name the user actually gave that tab in the
    desktop UI (companion-tab-list.json, kept fresh by main.py's tab_list_set
    control op -- see companion_api.py's request_tab_list_publish). Falls
    back to a bare "tab <id>" label if the file is missing/stale/doesn't
    have this id -- never fails the whole listing over a cosmetic label."""
    if tab_id is None:
        return "an unknown tab"
    try:
        from pathlib import Path

        raw = json.loads((Path(WORKSPACE_DIR) / _TAB_LIST_PATH).read_text(encoding="utf-8"))
        for row in raw:
            if str(row.get("id")) == str(tab_id):
                name = row.get("name")
                if name:
                    return f'"{name}"'
    except Exception:
        pass
    return f"tab {tab_id}"


async def list_my_windows(_args: dict[str, Any], _rp: Any) -> dict[str, Any]:
    # Bug fix (2026-09-26), per explicit instruction: this used to call
    # list_windows(get_tab_id()), filtering to ONLY the calling tab's own
    # entries -- window_registry.py's own _open_windows dict is already
    # ONE shared, process-wide registry (every tab's opens/closes land in
    # the SAME dict), so the data was never actually siloed; this tool's
    # own filter was what threw every other tab's windows away before the
    # model ever saw them. A tab now sees ALL open windows, its own AND
    # every other tab's, each one clearly marked which tab it belongs to --
    # own windows unmarked (the common case, reads exactly as before),
    # everyone else's flagged "(not yours -- opened by <tab>)" so the model
    # never mistakes another tab's window for something it can act on
    # itself (e.g. close_viewer only makes sense for windows it opened).
    my_tab_id = get_tab_id()
    tracked = list_windows()
    live_labels: set[str] | None
    try:
        raw = json.loads((await list_app_browsers({}, None))["text"])
        live_labels = {row["label"] for row in raw if row.get("label")}
    except Exception:
        # AppBrowserHost unreachable -- can't verify either way, so don't
        # drop entries just because we couldn't confirm them this time.
        live_labels = None

    windows = []
    for entry in tracked:
        if entry["kind"] == "browser" and live_labels is not None and entry["label"] not in live_labels:
            continue  # our own bookkeeping is stale -- the host says this one's actually gone.
        windows.append(entry)

    if not windows:
        return {"text": "No windows are currently open, in your tab or any other."}
    lines = []
    for w in windows:
        line = f"- [{w['kind']}] {w['label']} -- {w['purpose']}"
        if w.get("tab_id") != my_tab_id:
            line += f" (not yours -- opened by {_tab_display_name(w.get('tab_id'))})"
        lines.append(line)
    return {"text": "Currently open windows (yours and every other tab's):\n" + "\n".join(lines)}


PLUGIN = Plugin(
    name="windows",
    tools=[
        PluginTool(
            "list_my_windows",
            "List every window CURRENTLY open across every tab -- embedded browser tabs (open_app_browser) and "
            "viewer/editor windows (open_in_viewer) -- each with who opened it and why. Entries not marked "
            "'(not yours...)' are your own; entries that ARE marked belong to a different tab -- you can see "
            "them for awareness (e.g. before telling the user 'no windows are open' or asking them to close "
            "something), but only close/act on windows that are actually yours. Call this instead of guessing "
            "from what you remember doing earlier in the conversation.",
            {}, list_my_windows,
        ),
    ],
)
