/**
 * AC Agent — Mobile App Entry Point
 * React Native (Expo) — iOS + Android
 */

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { AuthProvider } from './src/context/AuthContext';
import { PatientProvider } from './src/context/PatientContext';
import RootNavigator from './src/navigation/RootNavigator';

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
    </GestureHandlerRootView>
  );
}
