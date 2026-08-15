/**
 * Local-first storage for the field recorder.
 *
 * Everything captured in the field is written to a local SQLite database
 * first — recordings must never be lost because of a bad connection. The
 * `synced` flag on each row tracks whether the record (and its audio file)
 * has been successfully pushed to the backend; `offlineSync.js` is the only
 * module that flips it.
 */
import * as SQLite from "expo-sqlite";

let db = null;

export function initLocalDatabase() {
  db = SQLite.openDatabase("kaimira_field.db");

  db.transaction((tx) => {
    tx.executeSql(`
      CREATE TABLE IF NOT EXISTS recordings (
        local_id TEXT PRIMARY KEY NOT NULL,
        server_id TEXT,
        language_id TEXT NOT NULL,
        speaker_id TEXT,
        title TEXT NOT NULL,
        genre TEXT,
        location_description TEXT,
        recorded_at_field_date TEXT,
        duration_seconds REAL,
        local_file_uri TEXT NOT NULL,
        consent_status TEXT NOT NULL DEFAULT 'pending',
        field_notes TEXT,
        synced INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
      );
    `);
  });

  return db;
}

export function getDatabase() {
  if (!db) {
    throw new Error("Local database not initialized — call initLocalDatabase() first.");
  }
  return db;
}

export function insertLocalRecording(recording) {
  const database = getDatabase();
  return new Promise((resolve, reject) => {
    database.transaction((tx) => {
      tx.executeSql(
        `INSERT INTO recordings
          (local_id, language_id, speaker_id, title, genre, location_description,
           recorded_at_field_date, duration_seconds, local_file_uri, consent_status,
           field_notes, synced, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)`,
        [
          recording.localId,
          recording.languageId,
          recording.speakerId || null,
          recording.title,
          recording.genre || null,
          recording.locationDescription || null,
          recording.recordedAtFieldDate || null,
          recording.durationSeconds || null,
          recording.localFileUri,
          recording.consentStatus || "pending",
          recording.fieldNotes || null,
          new Date().toISOString(),
        ],
        (_, result) => resolve(result),
        (_, error) => {
          reject(error);
          return false;
        }
      );
    });
  });
}

export function getUnsyncedRecordings() {
  const database = getDatabase();
  return new Promise((resolve, reject) => {
    database.transaction((tx) => {
      tx.executeSql(
        "SELECT * FROM recordings WHERE synced = 0 ORDER BY created_at ASC",
        [],
        (_, result) => resolve(result.rows._array),
        (_, error) => {
          reject(error);
          return false;
        }
      );
    });
  });
}

export function markRecordingSynced(localId, serverId) {
  const database = getDatabase();
  return new Promise((resolve, reject) => {
    database.transaction((tx) => {
      tx.executeSql(
        "UPDATE recordings SET synced = 1, server_id = ? WHERE local_id = ?",
        [serverId, localId],
        (_, result) => resolve(result),
        (_, error) => {
          reject(error);
          return false;
        }
      );
    });
  });
}

export function getAllLocalRecordings() {
  const database = getDatabase();
  return new Promise((resolve, reject) => {
    database.transaction((tx) => {
      tx.executeSql(
        "SELECT * FROM recordings ORDER BY created_at DESC",
        [],
        (_, result) => resolve(result.rows._array),
        (_, error) => {
          reject(error);
          return false;
        }
      );
    });
  });
}
