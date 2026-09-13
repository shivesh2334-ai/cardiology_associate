/**
 * AC Agent — Mobile App Entry Point
 * React Native (Expo) — iOS + Android + Web
 */

import React from 'react';
import { Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { AuthProvider } from './src/context/AuthContext';
import { PatientProvider } from './src/context/PatientContext';
import RootNavigator from './src/navigation/RootNavigator';

// Vercel Speed Insights (web only)
let SpeedInsights: any = null;
if (Platform.OS === 'web') {
  try {
    SpeedInsights = require('@vercel/speed-insights/react').SpeedInsights;
  } catch (e) {
    // Package not available on this platform
  }
}

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <AuthProvider>
          <PatientProvider>
            <NavigationContainer>
              <StatusBar style="light" backgroundColor="#1B3A6B" />
              <RootNavigator />
            </NavigationContainer>
          </PatientProvider>
        </AuthProvider>
      </SafeAreaProvider>
      {SpeedInsights && <SpeedInsights />}
    </GestureHandlerRootView>
  );
}
