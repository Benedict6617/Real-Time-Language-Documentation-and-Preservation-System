import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../services/api.js";

export default function RecordingDetailPage() {
  const { recordingId } = useParams();
  const [recording, setRecording] = useState(null);
  const [transcription, setTranscription] = useState(null);
  const [igtLines, setIgtLines] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.getRecording(recordingId).then(setRecording);
  }, [recordingId]);

  const handleTranscribe = async () => {
    setBusy(true);
    try {
      const result = await api.transcribeRecording(recordingId);
      setTranscription(result);
    } catch (err) {
      alert(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleAnalyzeGrammar = async () => {
    if (!transcription) return;
    setBusy(true);
    try {
      const lines = await api.analyzeGrammar(transcription.id);
      setIgtLines(lines);
    } catch (err) {
      alert(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (!recording) return <p className="muted">Loading…</p>;

  return (
    <div>
      <h2>{recording.title}</h2>
      <p className="muted">
        {recording.genre} · {recording.location_description} · {recording.recorded_at_field_date}
      </p>
      <div style={{ marginBottom: "1rem" }}>
        <span className="badge">{recording.status}</span>{" "}
        <a
          className="button"
          style={{ float: "right", textDecoration: "none" }}
          href={api.eafDownloadUrl(recordingId)}
        >
          Export ELAN (.eaf)
        </a>
      </div>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>Transcription</h3>
          <button onClick={handleTranscribe} disabled={busy}>
            {busy ? "Working…" : "Run ASR transcription"}
          </button>
        </div>
        {transcription ? (
          <>
            <p style={{ marginTop: "1rem" }}>{transcription.text}</p>
            <p className="muted">
              confidence: {transcription.confidence} · source: {transcription.source} · model:{" "}
              {transcription.asr_model_version}
            </p>
          </>
        ) : (
          <p className="muted">No transcription yet — run ASR or add one manually via the API.</p>
        )}
      </div>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>Grammatical analysis (IGT)</h3>
          <button onClick={handleAnalyzeGrammar} disabled={busy || !transcription}>
            Generate draft glosses
          </button>
        </div>
        {igtLines.map((line) => (
          <div className="igt-line" key={line.id}>
            <div className="surface">{line.surface_form}</div>
            <div>{line.morpheme_breakdown}</div>
            <div className="gloss">{line.gloss_line}</div>
            <div>'{line.free_translation}'</div>
          </div>
        ))}
        {igtLines.length === 0 && (
          <p className="muted">No interlinear glosses generated yet.</p>
        )}
      </div>
    </div>
  );
}
