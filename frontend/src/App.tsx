import { useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { ScanConfig, SessionDetail, SessionSummary } from "./types";

const initialConfig: ScanConfig = {
  folder_path: "",
  overall_similarity: 0.85,
  face_similarity: 0.8,
  strict_mode: false,
};

function App() {
  const [config, setConfig] = useState<ScanConfig>(initialConfig);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string>("");

  const markedCount = useMemo(
    () =>
      activeSession?.groups
        .flatMap((group) => group.images)
        .filter((image) => image.user_marked_delete).length ?? 0,
    [activeSession],
  );

  async function refreshSessions() {
    const history = await api.listSessions();
    setSessions(history);
  }

  useEffect(() => {
    refreshSessions().catch((err: Error) => setMessage(err.message));
  }, []);

  async function startScan() {
    if (!config.folder_path.trim()) {
      setMessage("Please enter a folder path.");
      return;
    }
    setBusy(true);
    setMessage("Scanning images...");
    try {
      const result = await api.startScan(config);
      setActiveSession(result);
      await refreshSessions();
      setMessage(`Scan completed: ${result.groups.length} similarity groups found.`);
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function loadSession(sessionId: number) {
    setBusy(true);
    try {
      const detail = await api.getSession(sessionId);
      setActiveSession(detail);
      setMessage(`Loaded report #${detail.id}`);
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function toggleImage(imageId: number, checked: boolean) {
    if (!activeSession) return;
    const updated = await api.updateDecisions(activeSession.id, [
      { image_id: imageId, marked_for_delete: checked },
    ]);
    setActiveSession(updated);
  }

  async function deleteMarked() {
    if (!activeSession) return;
    const confirmed = window.confirm(`Move ${markedCount} marked image(s) to trash staging folder?`);
    if (!confirmed) return;

    setBusy(true);
    try {
      const result = await api.deleteMarked(activeSession.id);
      setMessage(`Moved ${result.moved.length} file(s) to ${result.trash_folder}`);
      await loadSession(activeSession.id);
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="mx-auto max-w-6xl space-y-6 p-6">
        <h1 className="text-3xl font-bold">PhotoMorph Deduplicator</h1>

        <section className="rounded bg-white p-4 shadow">
          <h2 className="mb-3 text-xl font-semibold">Folder Selection & Configuration</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2">
              <span className="text-sm font-medium">Folder path</span>
              <input
                className="w-full rounded border border-slate-300 p-2"
                value={config.folder_path}
                onChange={(e) => setConfig((prev) => ({ ...prev, folder_path: e.target.value }))}
                placeholder="/absolute/path/to/images"
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium">Overall similarity: {config.overall_similarity.toFixed(2)}</span>
              <input
                type="range"
                min={0.5}
                max={1}
                step={0.01}
                value={config.overall_similarity}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, overall_similarity: Number(e.target.value) }))
                }
              />
            </label>

            <label className="space-y-2">
              <span className="text-sm font-medium">Face match threshold: {config.face_similarity.toFixed(2)}</span>
              <input
                type="range"
                min={0.5}
                max={1}
                step={0.01}
                value={config.face_similarity}
                onChange={(e) =>
                  setConfig((prev) => ({ ...prev, face_similarity: Number(e.target.value) }))
                }
              />
            </label>

            <label className="flex items-center gap-2 pt-7">
              <input
                type="checkbox"
                checked={config.strict_mode}
                onChange={(e) => setConfig((prev) => ({ ...prev, strict_mode: e.target.checked }))}
              />
              Strict duplicate mode
            </label>
          </div>

          <button
            className="mt-4 rounded bg-slate-900 px-4 py-2 font-medium text-white disabled:opacity-50"
            onClick={startScan}
            disabled={busy}
          >
            Start Scan
          </button>
        </section>

        <section className="rounded bg-white p-4 shadow">
          <h2 className="mb-3 text-xl font-semibold">Report History</h2>
          <div className="space-y-2">
            {sessions.map((session) => (
              <button
                key={session.id}
                className="flex w-full items-center justify-between rounded border border-slate-200 p-2 text-left hover:bg-slate-50"
                onClick={() => loadSession(session.id)}
              >
                <span>#{session.id} — {session.folder_path}</span>
                <span className="text-sm text-slate-500">
                  {session.total_images} images · {session.group_count} groups
                </span>
              </button>
            ))}
            {sessions.length === 0 && <p className="text-sm text-slate-500">No previous reports yet.</p>}
          </div>
        </section>

        {activeSession && (
          <section className="rounded bg-white p-4 shadow">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Grouped Results (Session #{activeSession.id})</h2>
              <button
                onClick={deleteMarked}
                disabled={busy || markedCount === 0}
                className="rounded bg-rose-700 px-4 py-2 font-medium text-white disabled:opacity-50"
              >
                Delete All Marked Images ({markedCount})
              </button>
            </div>

            <div className="space-y-4">
              {activeSession.groups.map((group) => (
                <details key={group.group_id} open className="rounded border border-slate-200 p-3">
                  <summary className="cursor-pointer font-medium">
                    Group {group.group_id} — {group.images.length} image(s)
                  </summary>

                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    {group.images.map((image) => (
                      <label key={image.id} className="rounded border border-slate-200 p-3">
                        <div className="flex items-center justify-between gap-3">
                          <span className="break-all text-sm">{image.file_path}</span>
                          <input
                            type="checkbox"
                            checked={image.user_marked_delete}
                            onChange={(e) => toggleImage(image.id, e.target.checked)}
                          />
                        </div>
                        <div className="mt-2 text-xs text-slate-500">
                          {image.width}×{image.height} · sharpness {image.sharpness.toFixed(2)} · exposure {image.exposure.toFixed(2)}
                          {group.keep_image_id === image.id && " · recommended keep"}
                          {image.recommended_delete && " · recommended delete"}
                        </div>
                      </label>
                    ))}
                  </div>
                </details>
              ))}
              {activeSession.groups.length === 0 && (
                <p className="text-sm text-slate-500">No similarity groups found for this session.</p>
              )}
            </div>
          </section>
        )}

        {message && <p className="rounded bg-slate-900 p-3 text-sm text-white">{message}</p>}
      </div>
    </div>
  );
}

export default App;
