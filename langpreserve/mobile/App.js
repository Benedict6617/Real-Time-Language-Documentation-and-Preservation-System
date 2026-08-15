import React, { useEffect } from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import RecordScreen from "./src/screens/RecordScreen";
import FieldSessionListScreen from "./src/screens/FieldSessionListScreen";
import SyncStatusScreen from "./src/screens/SyncStatusScreen";
import ConsentScreen from "./src/screens/ConsentScreen";
import { initLocalDatabase } from "./src/services/localDB";
import { startBackgroundSyncListener } from "./src/services/offlineSync";

const Stack = createNativeStackNavigator();

export default function App() {
  useEffect(() => {
    initLocalDatabase();
    const unsubscribe = startBackgroundSyncListener();
    return unsubscribe;
  }, []);

  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Sessions">
        <Stack.Screen
          name="Sessions"
          component={FieldSessionListScreen}
          options={{ title: "Field Sessions" }}
        />
        <Stack.Screen name="Consent" component={ConsentScreen} options={{ title: "Consent" }} />
        <Stack.Screen name="Record" component={RecordScreen} options={{ title: "New Recording" }} />
        <Stack.Screen name="Sync" component={SyncStatusScreen} options={{ title: "Sync Status" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
