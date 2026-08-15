import { Routes, Route, NavLink } from "react-router-dom";
import LanguagesPage from "./pages/LanguagesPage.jsx";
import LanguageDetailPage from "./pages/LanguageDetailPage.jsx";
import RecordingsPage from "./pages/RecordingsPage.jsx";
import RecordingDetailPage from "./pages/RecordingDetailPage.jsx";
import AnnotationQueuePage from "./pages/AnnotationQueuePage.jsx";
import LearningMaterialsPage from "./pages/LearningMaterialsPage.jsx";

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Kaimira</h1>
        <nav>
          <NavLink to="/" end>Languages</NavLink>
          <NavLink to="/recordings">Recordings</NavLink>
          <NavLink to="/annotations">Annotation Queue</NavLink>
          <NavLink to="/learning-materials">Learning Materials</NavLink>
        </nav>
        <p className="muted" style={{ marginTop: "2rem" }}>
          Language documentation &amp; preservation platform
        </p>
      </aside>
      <main className="main-content">
        <Routes>
          <Route path="/" element={<LanguagesPage />} />
          <Route path="/languages/:languageId" element={<LanguageDetailPage />} />
          <Route path="/recordings" element={<RecordingsPage />} />
          <Route path="/recordings/:recordingId" element={<RecordingDetailPage />} />
          <Route path="/annotations" element={<AnnotationQueuePage />} />
          <Route path="/learning-materials" element={<LearningMaterialsPage />} />
        </Routes>
      </main>
    </div>
  );
}
