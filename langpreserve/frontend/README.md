# Kaimira Web Dashboard

React + Vite web dashboard for linguists and community annotators: browse
documented languages, review/correct transcriptions, run ASR and draft
grammatical analysis, manage the community annotation queue, and generate
revitalization learning materials.

## Setup

```bash
npm install
cp .env.example .env   # point VITE_API_BASE_URL at your backend
npm run dev
```

Runs at `http://localhost:5173` by default, talking to the backend API at
`VITE_API_BASE_URL` (defaults to `http://localhost:8000`).

## Structure

```
src/
  pages/       One component per route (Languages, Recordings, Annotation Queue, ...)
  services/    api.js — thin fetch wrapper around the backend REST API
  App.jsx      Routing + sidebar layout
```
