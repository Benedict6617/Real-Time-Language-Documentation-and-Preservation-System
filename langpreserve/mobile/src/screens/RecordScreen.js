import React, { useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from "react-native";
import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system";
import { insertLocalRecording } from "../services/localDB";

/**
 * Core field-recording screen. Works fully offline: audio is captured to
 * local device storage and metadata is written to the local SQLite DB
 * immediately — nothing here depends on network connectivity. Sync happens
 * separately and opportunistically (see services/offlineSync.js).
 */
export default function RecordScreen({ route, navigation }) {
  const { languageId, speakerId } = route.params || {};
  const [recording, setRecording] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [title, setTitle] = useState("");
  const [genre, setGenre] = useState("narrative");
  const [locationDescription, setLocationDescription] = useState("");
  const [fieldNotes, setFieldNotes] = useState("");

  async function startRecording() {
    try {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording: newRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      setRecording(newRecording);
      setIsRecording(true);
    } catch (err) {
      Alert.alert("Could not start recording", err.message);
    }
  }

  async function stopRecording() {
    if (!recording) return;
    setIsRecording(false);
    await recording.stopAndUnloadAsync();
    const uri = recording.getURI();
    const status = await recording.getStatusAsync();

    const persistentDir = `${FileSystem.documentDirectory}kaimira_recordings/`;
    await FileSystem.makeDirectoryAsync(persistentDir, { intermediates: true }).catch(() => {});
    const localId = `local-${Date.now()}`;
    const persistentUri = `${persistentDir}${localId}.m4a`;
    await FileSystem.moveAsync({ from: uri, to: persistentUri });

    await insertLocalRecording({
      localId,
      languageId,
      speakerId,
      title: title || `Untitled session ${new Date().toLocaleString()}`,
      genre,
      locationDescription,
      recordedAtFieldDate: new Date().toISOString().slice(0, 10),
      durationSeconds: (status.durationMillis || 0) / 1000,
      localFileUri: persistentUri,
      consentStatus: "pending",
      fieldNotes,
    });

    setRecording(null);
    Alert.alert(
      "Saved locally",
      "This recording is saved on your device and will sync automatically next time you're online.",
      [{ text: "OK", onPress: () => navigation.navigate("Sessions") }]
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Session title</Text>
      <TextInput style={styles.input} value={title} onChangeText={setTitle} placeholder="e.g. Coyote and Raven, part 2" />

      <Text style={styles.label}>Genre</Text>
      <TextInput style={styles.input} value={genre} onChangeText={setGenre} placeholder="narrative / elicitation / conversation / song" />

      <Text style={styles.label}>Location</Text>
      <TextInput style={styles.input} value={locationDescription} onChangeText={setLocationDescription} placeholder="e.g. speaker's home" />

      <Text style={styles.label}>Field notes</Text>
      <TextInput
        style={[styles.input, styles.notes]}
        value={fieldNotes}
        onChangeText={setFieldNotes}
        placeholder="Anything worth remembering about this session"
        multiline
      />

      <TouchableOpacity
        style={[styles.recordButton, isRecording && styles.recordButtonActive]}
        onPress={isRecording ? stopRecording : startRecording}
      >
        <Text style={styles.recordButtonText}>{isRecording ? "Stop recording" : "Start recording"}</Text>
      </TouchableOpacity>

      <Text style={styles.hint}>
        Recordings are saved to this device immediately and sync automatically once you're back
        online — you never need signal in the field.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "#faf8f4" },
  label: { fontSize: 14, color: "#766f61", marginTop: 12, marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: "#e4ddd0",
    borderRadius: 8,
    padding: 10,
    backgroundColor: "#fff",
  },
  notes: { height: 80, textAlignVertical: "top" },
  recordButton: {
    marginTop: 28,
    backgroundColor: "#8a4b2f",
    padding: 16,
    borderRadius: 10,
    alignItems: "center",
  },
  recordButtonActive: { backgroundColor: "#b5482f" },
  recordButtonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  hint: { marginTop: 16, color: "#766f61", fontSize: 12, textAlign: "center" },
});
