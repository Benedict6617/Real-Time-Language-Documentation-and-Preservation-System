import { useState } from "react";
import { api } from "../services/api.js";

export default function AnnotationQueuePage() {
  const [transcriptionId, setTranscriptionId] = useState("");
  const [annotations, setAnnotations] = useState([]);
  const [loaded, setLoaded] = useState(false);

  const loadAnnotations = async () => {
    if (!transcriptionId) return;
    const result = await api.listAnnotations(transcriptionId);
    setAnnotations(result);
    setLoaded(true);
  };

  const handleUpvote = async (id) => {
    await api.upvoteAnnotation(id);
    loadAnnotations();
  };

  const handleResolve = async (id) => {
    await api.resolveAnnotation(id);
    loadAnnotations();
  };

  return (
    <div>
      <h2>Community annotation queue</h2>
      <p className="muted">
        Corrections, cultural notes, and review flags submitted by community annotators and
        linguists for a given transcription. Paste a transcription ID to review its queue.
      </p>

      <div className="card">
        <input
          type="text"
          placeholder="transcription UUID"
          value={transcriptionId}
          onChange={(e) => setTranscriptionId(e.target.value)}
          style={{ width: "60%", padding: "0.4rem", marginRight: "0.5rem" }}
        />
        <button onClick={loadAnnotations}>Load</button>
      </div>

      {loaded && annotations.length === 0 && (
        <p className="muted">No annotations found for this transcription.</p>
      )}

      {annotations.map((a) => (
        <div className="card" key={a.id}>
          <span className="badge">{a.annotation_type}</span>{" "}
          {a.resolved && <span className="badge success">resolved</span>}
          <p>{a.body}</p>
          <p className="muted">{a.upvotes} upvotes</p>
          <button className="secondary" onClick={() => handleUpvote(a.id)}>
            Upvote
          </button>{" "}
          {!a.resolved && (
            <button className="secondary" onClick={() => handleResolve(a.id)}>
              Mark resolved
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
