import { useEffect, useState } from "react";
import { api } from "../services/api.js";

const MATERIAL_TYPES = [
  { value: "flashcard_deck", label: "Flashcard deck" },
  { value: "minimal_pairs", label: "Minimal pairs drill" },
  { value: "phrasebook", label: "Phrasebook" },
];

export default function LearningMaterialsPage() {
  const [languages, setLanguages] = useState([]);
  const [languageId, setLanguageId] = useState("");
  const [materialType, setMaterialType] = useState(MATERIAL_TYPES[0].value);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.listLanguages().then((langs) => {
      setLanguages(langs);
      if (langs.length > 0) setLanguageId(langs[0].id);
    });
  }, []);

  const handleGenerate = async () => {
    setBusy(true);
    setResult(null);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"}/api/v1/learning-materials/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ language_id: languageId, material_type: materialType }),
        }
      );
      const data = await response.json();
      setResult(data);
    } catch (err) {
      alert(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h2>Revitalization learning materials</h2>
      <p className="muted">
        Auto-generate flashcards, minimal-pair drills, or phrasebooks from a language's
        documented phoneme inventory and transcribed recordings.
      </p>

      <div className="card">
        <label className="muted">Language</label>
        <select
          value={languageId}
          onChange={(e) => setLanguageId(e.target.value)}
          style={{ display: "block", width: "100%", padding: "0.4rem", margin: "0.5rem 0" }}
        >
          {languages.map((l) => (
            <option key={l.id} value={l.id}>
              {l.name}
            </option>
          ))}
        </select>

        <label className="muted">Material type</label>
        <select
          value={materialType}
          onChange={(e) => setMaterialType(e.target.value)}
          style={{ display: "block", width: "100%", padding: "0.4rem", margin: "0.5rem 0" }}
        >
          {MATERIAL_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>

        <button onClick={handleGenerate} disabled={busy || !languageId}>
          {busy ? "Generating…" : "Generate"}
        </button>
      </div>

      {result && (
        <div className="card">
          <h3>{result.title}</h3>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.85rem" }}>
            {JSON.stringify(JSON.parse(result.content_json), null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
