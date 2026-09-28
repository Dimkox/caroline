namespace Caroline.Native;

/// <summary>
/// Per explicit instruction (2026-09-27): this class used to spawn and
/// supervise the Python backend sidecar directly (Process.Start/Kill,
/// crash detection). That whole responsibility moved to backend-py/
/// supervisor.py, a standalone Python process now spawned by
/// SupervisorClient.cs instead -- see that file's own doc comment, and
/// supervisor.py's module docstring, for the full reasoning (decoupling
/// process supervision from this WPF-specific, Windows-only shell).
///
/// What's left here is just the Port constant: the backend's own app port
/// (chat.js's WebSocket, App.xaml.cs's splash-dismiss poll, MainWindow's
/// /api/control calls) is unchanged by that move and still referenced by
/// its old name at every one of those call sites -- kept as a plain
/// constant holder rather than touching all of them for a rename.
/// </summary>
public static class BackendProcess
{
    // Moved off 8765 (2026-09-13, per explicit instruction) to 48765 -- a
    // dedicated, unlikely-to-collide port, rather than the low/common 8765
    // several other unrelated apps also default to.
    public const int Port = 48765;
}
