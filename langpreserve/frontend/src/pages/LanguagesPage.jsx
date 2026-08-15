import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api.js";

export default function LanguagesPage() {
  const [languages, setLanguages] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listLanguages()
      .then(setLanguages)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2>Documented languages</h2>
      <p className="muted">
        Every language your team is documenting, with endangerment status and
        speaker estimates as recorded by the community.
      </p>

      {loading && <p className="muted">Loading…</p>}
      {error && <p style={{ color: "crimson" }}>{error}</p>}

      {languages.map((lang) => (
        <div className="card" key={lang.id}>
          <h3>
            <Link to={`/languages/${lang.id}`}>{lang.name}</Link>
          </h3>
          <p className="muted">{lang.region}</p>
          <span className="badge">{lang.endangerment_status || "Status unknown"}</span>{" "}
          {lang.estimated_speakers != null && (
            <span className="badge">~{lang.estimated_speakers.toLocaleString()} speakers</span>
          )}
          {lang.glottocode && <span className="badge">{lang.glottocode}</span>}
        </div>
      ))}

      {!loading && !error && languages.length === 0 && (
        <p className="muted">
          No languages yet. Run <code>scripts/seed_db.py</code> to load the sample dataset,
          or create one via the API.
        </p>
      )}
    </div>
  );
}
