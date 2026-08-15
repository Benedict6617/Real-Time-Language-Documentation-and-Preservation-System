import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../services/api.js";

export default function LanguageDetailPage() {
  const { languageId } = useParams();
  const [language, setLanguage] = useState(null);
  const [phonemes, setPhonemes] = useState([]);
  const [busy, setBusy] = useState(false);

  const loadPhonemes = () => api.listPhonemes(languageId).then(setPhonemes);

  useEffect(() => {
    api.getLanguage(languageId).then(setLanguage);
    loadPhonemes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [languageId]);

  const handleAutoDetect = async () => {
    setBusy(true);
    try {
      await api.autoDetectPhonemes(languageId);
      await loadPhonemes();
    } catch (err) {
      alert(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (!language) return <p className="muted">Loading…</p>;

  return (
    <div>
      <h2>{language.name}</h2>
      <p className="muted">{language.notes}</p>
      <div style={{ marginBottom: "1rem" }}>
        <span className="badge">{language.endangerment_status}</span>{" "}
        <a
          className="button"
          style={{ float: "right", textDecoration: "none" }}
          href={api.lexiconCsvUrl(languageId)}
        >
          Export lexicon (CSV)
        </a>
      </div>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>Phoneme inventory</h3>
          <button onClick={handleAutoDetect} disabled={busy}>
            {busy ? "Detecting…" : "Auto-detect from transcriptions"}
          </button>
        </div>
        <table style={{ marginTop: "1rem" }}>
          <thead>
            <tr>
              <th>IPA</th>
              <th>Type</th>
              <th>Manner / Place</th>
              <th>Example</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {phonemes.map((p) => (
              <tr key={p.id}>
                <td>{p.ipa_symbol}</td>
                <td>{p.phoneme_type}</td>
                <td className="muted">{[p.manner, p.place].filter(Boolean).join(" / ")}</td>
                <td>{p.example_word}</td>
                <td>
                  <span className={`badge ${p.detected_automatically ? "warning" : "success"}`}>
                    {p.detected_automatically ? "auto-detected" : "curated"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {phonemes.length === 0 && (
          <p className="muted">No phoneme entries yet.</p>
        )}
      </div>
    </div>
  );
}
