const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("kaimira_access_token");
}

async function request(path, options = {}) {
  const token = getToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }
  if (response.status === 204) return null;
  return response.json();
}

export const api = {
  // Languages
  listLanguages: () => request("/api/v1/languages"),
  getLanguage: (id) => request(`/api/v1/languages/${id}`),
  listPhonemes: (languageId) => request(`/api/v1/languages/${languageId}/phonemes`),
  autoDetectPhonemes: (languageId) =>
    request(`/api/v1/languages/${languageId}/phonemes/auto-detect`, { method: "POST" }),

  // Recordings
  listRecordings: (languageId) =>
    request(`/api/v1/recordings${languageId ? `?language_id=${languageId}` : ""}`),
  getRecording: (id) => request(`/api/v1/recordings/${id}`),
  transcribeRecording: (id, payload = {}) =>
    request(`/api/v1/recordings/${id}/transcribe`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  // Transcriptions & grammar
  getTranscription: (id) => request(`/api/v1/transcriptions/${id}`),
  updateTranscription: (id, payload) =>
    request(`/api/v1/transcriptions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  analyzeGrammar: (transcriptionId) =>
    request("/api/v1/grammar/analyze", {
      method: "POST",
      body: JSON.stringify({ transcription_id: transcriptionId }),
    }),
  listIgtLines: (transcriptionId) =>
    request(`/api/v1/transcriptions/${transcriptionId}/igt`),

  // Annotations
  listAnnotations: (transcriptionId) =>
    request(`/api/v1/annotations?transcription_id=${transcriptionId}`),
  createAnnotation: (payload) =>
    request("/api/v1/annotations", { method: "POST", body: JSON.stringify(payload) }),
  upvoteAnnotation: (id) => request(`/api/v1/annotations/${id}/upvote`, { method: "POST" }),
  resolveAnnotation: (id) => request(`/api/v1/annotations/${id}/resolve`, { method: "POST" }),

  // Export
  createExportJob: (payload) =>
    request("/api/v1/export/jobs", { method: "POST", body: JSON.stringify(payload) }),
  eafDownloadUrl: (recordingId) =>
    `${API_BASE_URL}/api/v1/export/recordings/${recordingId}/eaf`,
  lexiconCsvUrl: (languageId) =>
    `${API_BASE_URL}/api/v1/export/languages/${languageId}/lexicon.csv`,

  // Auth
  login: async (email, password) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    if (!response.ok) throw new Error("Login failed");
    const data = await response.json();
    localStorage.setItem("kaimira_access_token", data.access_token);
    return data;
  },
  logout: () => localStorage.removeItem("kaimira_access_token"),
  isAuthenticated: () => Boolean(getToken()),
};
