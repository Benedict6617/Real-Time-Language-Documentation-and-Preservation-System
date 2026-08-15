/**
 * Background sync: watches for connectivity and pushes any locally-recorded,
 * unsynced sessions to the backend's `/api/v1/recordings/sync` batch
 * endpoint. Designed around the reality of fieldwork — connectivity may not
 * return for days, so every operation here must be safe to retry and safe
 * to interrupt mid-batch.
 */
import NetInfo from "@react-native-community/netinfo";
import * as FileSystem from "expo-file-system";
import {
  getUnsyncedRecordings,
  markRecordingSynced,
} from "./localDB";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000";
const DEVICE_ID_KEY = "kaimira-device-id";

let deviceId = null;

async function getDeviceId() {
  if (deviceId) return deviceId;
  // In a full implementation this would be persisted via SecureStore /
  // AsyncStorage on first launch. Kept inline here to keep this reference
  // module dependency-light.
  deviceId = `field-device-${Math.random().toString(36).slice(2, 10)}`;
  return deviceId;
}

async function uploadAudioFile(localFileUri) {
  // Uploads the raw audio bytes to a staging storage key; the backend links
  // this to the metadata record during `/recordings/sync` reconciliation.
  const uploadResult = await FileSystem.uploadAsync(
    `${API_BASE_URL}/api/v1/recordings/staging-upload`,
    localFileUri,
    {
      httpMethod: "POST",
      uploadType: FileSystem.FileSystemUploadType.MULTIPART,
      fieldName: "audio_file",
    }
  );
  if (uploadResult.status >= 400) {
    throw new Error(`Audio upload failed: HTTP ${uploadResult.status}`);
  }
  return uploadResult;
}

export async function syncPendingRecordings() {
  const pending = await getUnsyncedRecordings();
  if (pending.length === 0) {
    return { synced: 0, failed: 0 };
  }

  const device = await getDeviceId();
  let syncedCount = 0;
  let failedCount = 0;

  // Upload audio bytes first (can partially succeed and retry next time),
  // then reconcile metadata in one batch call so the trip is fast even on a
  // slow connection.
  for (const record of pending) {
    try {
      await uploadAudioFile(record.local_file_uri);
    } catch (err) {
      failedCount += 1;
      // Leave this record unsynced; next connectivity window will retry.
      continue;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/recordings/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: device,
          recordings: [
            {
              language_id: record.language_id,
              speaker_id: record.speaker_id,
              title: record.title,
              genre: record.genre,
              location_description: record.location_description,
              recorded_at_field_date: record.recorded_at_field_date,
              duration_seconds: record.duration_seconds,
              field_notes: record.field_notes,
              captured_offline: true,
              consent_status: record.consent_status,
            },
          ],
          client_recorded_local_ids: [record.local_id],
        }),
      });

      if (!response.ok) throw new Error(`Sync failed: HTTP ${response.status}`);
      const [created] = await response.json();
      await markRecordingSynced(record.local_id, created.id);
      syncedCount += 1;
    } catch (err) {
      failedCount += 1;
    }
  }

  return { synced: syncedCount, failed: failedCount };
}

export function startBackgroundSyncListener() {
  const unsubscribe = NetInfo.addEventListener((state) => {
    if (state.isConnected && state.isInternetReachable !== false) {
      syncPendingRecordings().catch(() => {
        // Swallow errors here — the UI's SyncStatusScreen surfaces failures
        // and the unsynced rows simply remain queued for the next attempt.
      });
    }
  });
  return unsubscribe;
}
