"""Production entry point -- invoked directly by BackendProcess.cs (pythonw.exe
run_server.py) instead of `python -m app.main`, because the embeddable Python
distribution's own python3XX._pth file fully overrides sys.path (per its own
documented contract: when a ._pth file exists, ALL registry/env vars are
ignored and sys.path is built solely from that file's own entries) -- this
means `-m`'s usual cwd-prepend behavior can't be relied on to make the `app`
package importable. A plain script invocation doesn't have that problem: the
script's own directory is always sys.path[0], confirmed empirically against
the actual embeddable runtime this ships with (see PythonInstaller.cs).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.main import PORT, app  # noqa: E402
from app.logging_setup import log_event  # noqa: E402
from app.skills_seed import seed_skills  # noqa: E402
from app.workspace_dir import WORKSPACE_DIR  # noqa: E402

if __name__ == "__main__":
    import uvicorn

    log_event("engine", "starting", port=PORT, workspace_dir=WORKSPACE_DIR)
    seed_skills(WORKSPACE_DIR)
    # Bug fix (2026-09-27), per explicit instruction, found live (backend
    # crash-looping on startup, "ModuleNotFoundError: No module named
    # 'app.local_tts_launcher'"): main.py's OWN __main__ block (dead code
    # when run_server.py is the real entry point, which it always is --
    # see this file's own docstring) had already been fixed the same day to
    # drop the local_tts_launcher/launch_local_tts_server() call (see its
    # comment: "no longer launches local_tts_server.py as a separate
    # subprocess ... in-process app.local_edge_tts now, this file/launcher
    # was leftover from the old Node.js backend") -- but THIS copy, the one
    # actually invoked by SupervisorClient.cs/BackendProcess.cs, was missed,
    # importing a module (app/local_tts_launcher.py) that no longer exists
    # in the repo at all. Nothing replaces this call: local_edge_tts is
    # called in-process, on demand, from voice_api.py's own TTS path, not
    # launched once at startup.
    uvicorn.run(app, host="127.0.0.1", port=PORT)
