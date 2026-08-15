import React, { useState } from "react";
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from "react-native";

/**
 * A lightweight consent checkpoint shown before every recording session.
 * Field teams should adapt the wording here to match their own IRB/ethics
 * board language and the specific agreement in place with the community
 * (see docs/CONTRIBUTING.md for guidance on data sovereignty).
 */
export default function ConsentScreen({ navigation, route }) {
  const [acknowledged, setAcknowledged] = useState(false);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.heading}>Before you record</Text>
      <Text style={styles.body}>
        Confirm with the speaker(s) that they understand:
      </Text>
      <Text style={styles.bullet}>• This recording will be stored and may be shared with the documentation project and, if they agree, an academic archive.</Text>
      <Text style={styles.bullet}>• They can ask for a recording to be deleted or restricted at any time.</Text>
      <Text style={styles.bullet}>• They decide whether their name is attached to the recording or it stays anonymous.</Text>

      <TouchableOpacity
        style={styles.checkboxRow}
        onPress={() => setAcknowledged((prev) => !prev)}
      >
        <View style={[styles.checkbox, acknowledged && styles.checkboxChecked]} />
        <Text style={styles.checkboxLabel}>
          I've confirmed consent with the speaker(s) for this session.
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.continueButton, !acknowledged && styles.continueButtonDisabled]}
        disabled={!acknowledged}
        onPress={() => navigation.navigate("Record", route.params)}
      >
        <Text style={styles.continueButtonText}>Continue to recording</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 20, backgroundColor: "#faf8f4", flexGrow: 1 },
  heading: { fontSize: 20, fontWeight: "700", marginBottom: 12 },
  body: { fontSize: 14, color: "#2b2620", marginBottom: 8 },
  bullet: { fontSize: 14, color: "#2b2620", marginBottom: 6, paddingLeft: 8 },
  checkboxRow: { flexDirection: "row", alignItems: "center", marginTop: 24 },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#8a4b2f",
    marginRight: 10,
  },
  checkboxChecked: { backgroundColor: "#8a4b2f" },
  checkboxLabel: { flex: 1, fontSize: 14 },
  continueButton: {
    marginTop: 28,
    backgroundColor: "#8a4b2f",
    padding: 16,
    borderRadius: 10,
    alignItems: "center",
  },
  continueButtonDisabled: { opacity: 0.4 },
  continueButtonText: { color: "#fff", fontWeight: "600" },
});
