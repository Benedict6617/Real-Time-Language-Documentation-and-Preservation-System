import React, { useCallback, useState } from "react";
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import { getAllLocalRecordings } from "../services/localDB";

export default function FieldSessionListScreen({ navigation }) {
  const [sessions, setSessions] = useState([]);

  useFocusEffect(
    useCallback(() => {
      getAllLocalRecordings().then(setSessions).catch(() => setSessions([]));
    }, [])
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={sessions}
        keyExtractor={(item) => item.local_id}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.meta}>
              {item.genre} · {item.recorded_at_field_date}
            </Text>
            <Text style={item.synced ? styles.synced : styles.pending}>
              {item.synced ? "Synced" : "Waiting to sync"}
            </Text>
          </View>
        )}
        ListEmptyComponent={
          <Text style={styles.empty}>
            No recordings yet on this device. Tap "New recording" to start your first session.
          </Text>
        }
      />
      <TouchableOpacity style={styles.newButton} onPress={() => navigation.navigate("Consent")}>
        <Text style={styles.newButtonText}>+ New recording</Text>
      </TouchableOpacity>
      <TouchableOpacity style={styles.syncLink} onPress={() => navigation.navigate("Sync")}>
        <Text style={styles.syncLinkText}>View sync status</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#faf8f4", padding: 16 },
  row: {
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: "#e4ddd0",
  },
  title: { fontSize: 16, fontWeight: "600" },
  meta: { color: "#766f61", fontSize: 12, marginTop: 2 },
  synced: { color: "#3f7a52", fontSize: 12, marginTop: 4 },
  pending: { color: "#b5822b", fontSize: 12, marginTop: 4 },
  empty: { textAlign: "center", color: "#766f61", marginTop: 40 },
  newButton: {
    backgroundColor: "#8a4b2f",
    padding: 16,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 12,
  },
  newButtonText: { color: "#fff", fontWeight: "600" },
  syncLink: { alignItems: "center", marginTop: 10 },
  syncLinkText: { color: "#8a4b2f" },
});
