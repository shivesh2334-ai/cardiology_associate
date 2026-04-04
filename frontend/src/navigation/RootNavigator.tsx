/**
 * AC Agent — Root Navigator
 */

import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuth } from '../context/AuthContext';
import { Colors } from '../utils/design';

// Screens
import LoginScreen         from '../screens/LoginScreen';
import PatientListScreen   from '../screens/PatientListScreen';
import PatientDashboard    from '../screens/PatientDashboard';
import BriefingInputScreen from '../screens/BriefingInputScreen';
import BriefingPreview     from '../screens/BriefingPreview';
import BriefingCopilot     from '../screens/BriefingCopilot';
import BriefingComplete    from '../screens/BriefingComplete';
import NoteInputScreen     from '../screens/NoteInputScreen';
import NoteReviewScreen    from '../screens/NoteReviewScreen';

export type RootStackParamList = {
  Login: undefined;
  PatientList: undefined;
  PatientDashboard: { patientId: string };
  BriefingInput:    { patientId: string };
  BriefingPreview:  { briefingId: string; patientId: string };
  BriefingCopilot:  { briefingId: string; patientId: string };
  BriefingComplete: { briefingId: string; patientId: string };
  NoteInput:        { patientId: string; noteType?: string };
  NoteReview:       { noteId: string; patientId: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.brandDark }}>
        <ActivityIndicator size="large" color={Colors.white} />
      </View>
    );
  }

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: Colors.brandDark },
        headerTintColor: Colors.white,
        headerTitleStyle: { fontWeight: '600', fontSize: 17 },
        headerBackTitle: '',
        contentStyle: { backgroundColor: Colors.background },
      }}
    >
      {!user ? (
        <Stack.Screen name="Login" component={LoginScreen}
          options={{ headerShown: false }} />
      ) : (
        <>
          <Stack.Screen name="PatientList" component={PatientListScreen}
            options={{ title: 'AC Agent — ICU', headerBackVisible: false }} />
          <Stack.Screen name="PatientDashboard" component={PatientDashboard}
            options={{ title: 'Patient' }} />
          <Stack.Screen name="BriefingInput" component={BriefingInputScreen}
            options={{ title: 'Family Briefing — Input' }} />
          <Stack.Screen name="BriefingPreview" component={BriefingPreview}
            options={{ title: 'Briefing Preview' }} />
          <Stack.Screen name="BriefingCopilot" component={BriefingCopilot}
            options={{ title: '🎯 Live Co-Pilot', headerStyle: { backgroundColor: '#0D2440' } }} />
          <Stack.Screen name="BriefingComplete" component={BriefingComplete}
            options={{ title: 'File Briefing Log' }} />
          <Stack.Screen name="NoteInput" component={NoteInputScreen}
            options={{ title: 'Clinical Note — Input' }} />
          <Stack.Screen name="NoteReview" component={NoteReviewScreen}
            options={{ title: 'Review & Approve Note' }} />
        </>
      )}
    </Stack.Navigator>
  );
}
