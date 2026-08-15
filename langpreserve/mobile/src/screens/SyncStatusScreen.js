import React, { useCallback, useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { getUnsyncedRecordings } from "../services/localDB";
import { syncPendingRecordings } from "../services/offlineSync";

export default function SyncStatusScreen() {
  const [pendingCount, setPendingCount] = useState(0);
  const [syncing, setSyncing] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  const refresh = useCallback(() => {
    getUnsyncedRecordings().then((rows) => setPendingCount(rows.length));
  }, []);

  useFocusEffect(refresh);

  async function handleSyncNow() {
    setSyncing(true);
    try {
      const result = await syncPendingRecordings();
      setLastResult(result);
      refresh();
    } finally {
      setSyncing(false);
    }
  }

  return (
    <View style={styles.container}>
      <Text style={styles.count}>{pendingCount}</Text>
      <Text style={styles.label}>recording(s) waiting to sync</Text>

      {syncing ? (
        <ActivityIndicator style={{ marginTop: 24 }} color="#8a4b2f" />
      ) : (
        <TouchableOpacity style={styles.button} onPress={handleSyncNow}>
          <Text style={styles.buttonText}>Sync now</Text>
        </TouchableOpacity>
      )}

      {lastResult && (
        <Text style={styles.result}>
          Last attempt: {lastResult.synced} synced, {lastResult.failed} failed (will retry
          automatically).
        </Text>
      )}

      <Text style={styles.hint}>
        Sync also runs automatically in the background whenever the device regains a network
        connection — you don't need to open this screen for it to work.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#faf8f4", alignItems: "center", paddingTop: 60, padding: 20 },
  count: { fontSize: 48, fontWeight: "700", color: "#8a4b2f" },
  label: { color: "#766f61", marginBottom: 20 },
  button: { backgroundColor: "#8a4b2f", padding: 14, borderRadius: 10, paddingHorizontal: 30 },
  buttonText: { color: "#fff", fontWeight: "600" },
  result: { marginTop: 20, color: "#2b2620", textAlign: "center" },
  hint: { marginTop: 40, color: "#766f61", fontSize: 12, textAlign: "center" },
});
