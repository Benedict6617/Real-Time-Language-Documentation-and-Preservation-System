import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api.js";

const STATUS_BADGE = {
  uploaded: "",
  queued_for_asr: "warning",
  transcribing: "warning",
  draft_ready: "success",
  under_review: "warning",
  community_approved: "success",
  archived: "success",
};

export default function RecordingsPage() {
  const [recordings, setRecordings] = useState([]);

  useEffect(() => {
    api.listRecordings().then(setRecordings).catch(() => setRecordings([]));
  }, []);

  return (
    <div>
      <h2>Field recordings</h2>
      <p className="muted">
        Recordings captured in the field (including those synced from the offline mobile app).
      </p>

      {recordings.map((rec) => (
        <div className="card" key={rec.id}>
          <h3>
            <Link to={`/recordings/${rec.id}`}>{rec.title}</Link>
          </h3>
          <p className="muted">
            {rec.genre} · {rec.location_description} · {rec.recorded_at_field_date}
            {rec.captured_offline && " · captured offline"}
          </p>
          <span className={`badge ${STATUS_BADGE[rec.status] || ""}`}>{rec.status}</span>{" "}
          <span className="badge">{rec.consent_status}</span>
        </div>
      ))}

      {recordings.length === 0 && (
        <p className="muted">
          No recordings yet. Upload one from the mobile field app, or seed sample data.
        </p>
      )}
    </div>
  );
}
