import React, { useEffect, useState } from 'react';
import { ScrollView, Text, TextInput, StyleSheet, Alert, View } from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/RootNavigator';
import { briefingAPI } from '../services/api';
import { usePatients } from '../context/PatientContext';
import { storeBriefing } from '../hooks/useBriefingStore';
import { Button, AlertBanner } from '../components/ui';
import { Colors, Spacing, Radius, Typography } from '../utils/design';

type Route = RouteProp<RootStackParamList,'BriefingInput'>; type Nav = NativeStackNavigationProp<RootStackParamList,'BriefingInput'>;
export default function BriefingInputScreen(){
 const {patientId}=useRoute<Route>().params; const nav=useNavigation<Nav>(); const {selectedPatient:p,selectPatient}=usePatients();
 const [trajectory,setTrajectory]=useState('stable'),[map,setMap]=useState(''),[hr,setHr]=useState(''),[spo2,setSpo2]=useState(''),[gcs,setGcs]=useState(''),[notes,setNotes]=useState(''),[loading,setLoading]=useState(false);
 useEffect(()=>{selectPatient(patientId)},[patientId]);
 const generate=async()=>{ if(!p?.ai_consent){Alert.alert('Consent required','Record AI-assistance consent before generating a briefing.');return} setLoading(true); try{const r=await briefingAPI.generate({patient_id:patientId,trajectory,map_value:map?Number(map):undefined,heart_rate:hr?Number(hr):undefined,spo2:spo2?Number(spo2):undefined,gcs:gcs?Number(gcs):undefined,associate_notes:notes,ventilator_status:'not_ventilated'}); storeBriefing(r.briefing_id,r.document,p.full_name);nav.navigate('BriefingPreview',{briefingId:r.briefing_id,patientId});}catch(e:any){Alert.alert('Generation failed',e.message)}finally{setLoading(false)}};
 const field=(label:string,value:string,set:(x:string)=>void,numeric=false)=><View style={styles.field}><Text style={styles.label}>{label}</Text><TextInput style={styles.input} value={value} onChangeText={set} keyboardType={numeric?'decimal-pad':'default'} /></View>;
 return <ScrollView contentContainerStyle={styles.content}><AlertBanner type="info" message="Confirm current bedside data. The AI draft does not replace clinical judgment."/><Text style={styles.label}>Trajectory</Text><TextInput style={styles.input} value={trajectory} onChangeText={setTrajectory} placeholder="improving / stable / guarded / critical / deteriorating"/>{field('MAP (mmHg)',map,setMap,true)}{field('Heart rate',hr,setHr,true)}{field('SpO₂ (%)',spo2,setSpo2,true)}{field('GCS',gcs,setGcs,true)}<Text style={styles.label}>Associate context</Text><TextInput style={[styles.input,styles.area]} value={notes} onChangeText={setNotes} multiline placeholder="Important changes, procedures, specialists and cautions..."/><Button label="Generate briefing draft" onPress={generate} loading={loading}/></ScrollView>
}
const styles=StyleSheet.create({content:{padding:Spacing.base,paddingBottom:48,backgroundColor:Colors.background},field:{marginTop:Spacing.md},label:{fontWeight:'600',color:Colors.textPrimary,marginBottom:6,marginTop:Spacing.md},input:{backgroundColor:Colors.white,borderWidth:1,borderColor:Colors.border,borderRadius:Radius.md,padding:Spacing.md,fontSize:Typography.base},area:{minHeight:120,textAlignVertical:'top',marginBottom:Spacing.xl}});
