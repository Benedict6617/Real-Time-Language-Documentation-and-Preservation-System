# Kaimira Field Recorder (offline mobile app)

An offline-first React Native / Expo app for capturing field recordings —
built for the reality of documentation fieldwork, where a village or valley
may have no connectivity for days at a time.

## How offline-first works here

1. **Consent checkpoint** — every session starts with a short consent
   confirmation screen (`src/screens/ConsentScreen.js`).
2. **Local capture** — audio is recorded straight to device storage and
   metadata is written to a local SQLite database
   (`src/services/localDB.js`) immediately. Nothing here touches the
   network.
3. **Opportunistic sync** — `src/services/offlineSync.js` listens for
   connectivity changes and pushes any unsynced sessions to the backend's
   `/api/v1/recordings/sync` batch endpoint, uploading audio first and then
   reconciling metadata in one small request to stay fast on weak signal.
   Failures are retried automatically on the next connectivity window — nothing
   is deleted locally until the server confirms receipt.

## Setup

```bash
npm install
cp .env.example .env    # set EXPO_PUBLIC_API_BASE_URL
npx expo start
```

Scan the QR code with Expo Go on a physical device to test real
microphone/recording behavior — the simulator's audio input is unreliable
for this kind of testing.

## Structure

```
App.js                        Navigation shell + local DB / sync bootstrap
src/screens/
  FieldSessionListScreen.js   List of local + synced sessions
  ConsentScreen.js            Pre-recording consent checkpoint
  RecordScreen.js             Audio capture + session metadata form
  SyncStatusScreen.js         Manual "sync now" + pending-count display
src/services/
  localDB.js                  SQLite schema + CRUD for offline sessions
  offlineSync.js               Connectivity listener + batch sync to backend
```
