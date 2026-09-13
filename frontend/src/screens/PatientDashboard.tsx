import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/RootNavigator';
import { usePatients } from '../context/PatientContext';
import { patientAPI, noteAPI, briefingAPI, BriefingOut, NoteOut } from '../services/api';
import { Colors, Spacing, Radius, Typography, trajectoryColor } from '../utils/design';
import { LoadingScreen } from '../components/ui';

type Route = RouteProp<RootStackParamList, 'PatientDashboard'>;
type Nav = NativeStackNavigationProp<RootStackParamList, 'PatientDashboard'>;

export default function PatientDashboard() {
  const { patientId } = useRoute<Route>().params;
  const navigation = useNavigation<Nav>();
  const { selectedPatient: patient, selectPatient } = usePatients();
  const [notes, setNotes] = useState<NoteOut[]>([]);
  const [briefings, setBriefings] = useState<BriefingOut[]>([]);

  const load = async () => {
    try {
      await selectPatient(patientId);
      const [n, b] = await Promise.all([noteAPI.listForPatient(patientId), briefingAPI.listForPatient(patientId)]);
      setNotes(n); setBriefings(b);
    } catch (e: any) { Alert.alert('Unable to load patient', e.message); }
  };
  useEffect(() => { load(); }, [patientId]);

  if (!patient || patient.id !== patientId) return <LoadingScreen message="Loading clinical record..." />;
  const action = (label: string, subtitle: string, onPress: () => void) => (
    <TouchableOpacity style={styles.action} onPress={onPress}>
      <View><Text style={styles.actionTitle}>{label}</Text><Text style={styles.actionSub}>{subtitle}</Text></View><Text style={styles.chevron}>›</Text>
    </TouchableOpacity>
  );
  return <ScrollView style={styles.container} contentContainerStyle={styles.content}>
    <View style={[styles.hero, { borderLeftColor: trajectoryColor(patient.trajectory) }]}>
      <Text style={styles.name}>{patient.full_name}</Text>
      <Text style={styles.meta}>{patient.age}Y / {patient.sex} · {patient.ward || 'Ward'} · Bed {patient.bed_number || '—'}</Text>
      <Text style={styles.uhid}>UHID {patient.uhid}</Text>
      <Text style={styles.diagnosis}>{patient.primary_diagnosis || 'Diagnosis pending'}</Text>
    </View>
    {!patient.ai_consent && <TouchableOpacity style={styles.consent} onPress={async () => { try { await patientAPI.recordConsent(patientId, 'Patient/family representative'); await selectPatient(patientId); } catch(e:any) { Alert.alert('Consent error', e.message); } }}><Text style={styles.consentTitle}>AI consent required</Text><Text style={styles.consentText}>Tap only after documented patient/family consent has been obtained.</Text></TouchableOpacity>}
    <Text style={styles.heading}>Clinical workflows</Text>
    {action('Family briefing', 'Generate a reviewed, plain-language ICU update', () => navigation.navigate('BriefingInput', { patientId }))}
    {action('Clinical note', 'Generate a SOAP draft for clinician review', () => navigation.navigate('NoteInput', { patientId }))}
    <Text style={styles.heading}>Record</Text>
    <View style={styles.summary}><Text style={styles.count}>{notes.length}</Text><Text style={styles.summaryLabel}>notes</Text><Text style={styles.count}>{briefings.length}</Text><Text style={styles.summaryLabel}>briefings</Text></View>
    {notes.slice(0, 5).map(n => <View key={n.id} style={styles.row}><Text style={styles.rowTitle}>{n.note_type.replace(/_/g, ' ')}</Text><Text style={styles.rowMeta}>{n.status} · {new Date(n.created_at).toLocaleDateString()}</Text></View>)}
  </ScrollView>;
}

const styles = StyleSheet.create({ container:{flex:1,backgroundColor:Colors.background},content:{padding:Spacing.base,paddingBottom:48},hero:{backgroundColor:Colors.white,borderRadius:Radius.lg,padding:Spacing.base,borderLeftWidth:6},name:{fontSize:Typography.xl,fontWeight:'700',color:Colors.brandDark},meta:{color:Colors.textSecondary,marginTop:4},uhid:{fontSize:Typography.xs,color:Colors.textMuted,marginTop:6},diagnosis:{fontSize:Typography.base,color:Colors.textPrimary,marginTop:Spacing.md},heading:{fontSize:Typography.md,fontWeight:'700',color:Colors.brandDark,marginTop:Spacing.xl,marginBottom:Spacing.sm},action:{backgroundColor:Colors.white,borderRadius:Radius.md,padding:Spacing.base,marginBottom:Spacing.sm,flexDirection:'row',alignItems:'center',justifyContent:'space-between'},actionTitle:{fontWeight:'700',fontSize:Typography.base,color:Colors.textPrimary},actionSub:{fontSize:Typography.sm,color:Colors.textSecondary,marginTop:3,maxWidth:290},chevron:{fontSize:28,color:Colors.brandMid},consent:{backgroundColor:'#FFF3E0',borderRadius:Radius.md,padding:Spacing.base,marginTop:Spacing.md},consentTitle:{fontWeight:'700',color:Colors.warning},consentText:{fontSize:Typography.sm,color:Colors.textSecondary,marginTop:4},summary:{flexDirection:'row',alignItems:'baseline',gap:8,backgroundColor:Colors.white,padding:Spacing.base,borderRadius:Radius.md},count:{fontSize:Typography.xl,fontWeight:'700',color:Colors.brandMid},summaryLabel:{color:Colors.textSecondary,marginRight:Spacing.base},row:{backgroundColor:Colors.white,padding:Spacing.md,borderBottomWidth:1,borderBottomColor:Colors.divider},rowTitle:{textTransform:'capitalize',fontWeight:'600'},rowMeta:{fontSize:Typography.xs,color:Colors.textMuted,marginTop:3} });
