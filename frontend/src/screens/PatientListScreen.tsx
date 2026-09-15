/**
 * AC Agent — Patient List Screen (Home)
 * The Associate's command centre — all active ICU patients at a glance.
 */

import React, { useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  RefreshControl
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { Colors, Typography, Spacing, Radius, Shadow, trajectoryColor } from '../utils/design';
import { TrajectoryBadge, EmptyState, LoadingScreen } from '../components/ui';
import { usePatients } from '../context/PatientContext';
import { PatientListItem } from '../services/api';
import { RootStackParamList } from '../navigation/RootNavigator';

type Nav = NativeStackNavigationProp<RootStackParamList, 'PatientList'>;

export default function PatientListScreen() {
  const navigation = useNavigation<Nav>();
  const { patients, isLoadingList, fetchPatients } = usePatients();

  useEffect(() => { fetchPatients(); }, []);

  const onRefresh = useCallback(() => { fetchPatients(); }, []);

  const openPatient = (patient: PatientListItem) => {
    navigation.navigate('PatientDashboard', { patientId: patient.id });
  };

  const renderPatient = ({ item }: { item: PatientListItem }) => (
    <TouchableOpacity
      onPress={() => openPatient(item)}
      style={styles.card}
      activeOpacity={0.85}
    >
      {/* Left accent bar — trajectory colour */}
      <View style={[styles.accentBar, { backgroundColor: trajectoryColor(item.trajectory) }]} />

      <View style={styles.cardContent}>
        {/* Top row */}
        <View style={styles.cardTop}>
          <View style={{ flex: 1 }}>
            <Text style={styles.patientName}>{item.full_name}</Text>
            <Text style={styles.patientDemo}>{item.age}Y / {item.sex} · {item.ward ?? 'ICU'} · Bed {item.bed_number ?? '—'}</Text>
          </View>
          <View style={styles.cardTopRight}>
            <TrajectoryBadge trajectory={item.trajectory} />
            <Text style={styles.dayBadge}>Day {item.days_admitted}</Text>
          </View>
        </View>

        {/* Diagnosis */}
        <Text style={styles.diagnosis} numberOfLines={2}>
          {item.primary_diagnosis ?? 'Diagnosis pending'}
        </Text>

        {/* Alert row */}
        <View style={styles.alertRow}>
          {item.briefing_overdue && (
            <View style={styles.alertChip}>
              <Text style={styles.alertChipText}>⚠ Briefing Overdue</Text>
            </View>
          )}
          {item.has_pending_results && (
            <View style={[styles.alertChip, styles.alertChipBlue]}>
              <Text style={[styles.alertChipText, { color: Colors.brandMid }]}>🔬 New Results</Text>
            </View>
          )}
          <Text style={styles.uhid}>UHID: {item.uhid}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  if (isLoadingList && patients.length === 0) {
    return <LoadingScreen message="Loading patients..." />;
  }

  return (
    <View style={styles.container}>
      {/* Header bar */}
      <View style={styles.headerBar}>
        <View>
          <Text style={styles.headerGreeting}>Dr. Shivesh</Text>
          <Text style={styles.headerSub}>{patients.length} active patients</Text>
        </View>
        <View style={styles.avatarCircle}>
          <Text style={styles.avatarText}>S</Text>
        </View>
      </View>

      <FlatList
        data={patients}
        keyExtractor={p => p.id}
        renderItem={renderPatient}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={isLoadingList} onRefresh={onRefresh} tintColor={Colors.brandMid} />
        }
        ListEmptyComponent={
          <EmptyState
            icon="🏥"
            title="No active patients"
            subtitle="Active ICU patients will appear here. Pull to refresh."
          />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container:      { flex: 1, backgroundColor: Colors.background },
  headerBar: {
    backgroundColor: Colors.brandDark,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.base,
    paddingVertical: Spacing.md,
    paddingTop: Spacing.lg,
  },
  headerGreeting: { fontSize: Typography.md, fontWeight: '700', color: Colors.white },
  headerSub:      { fontSize: Typography.sm, color: 'rgba(255,255,255,0.7)', marginTop: 2 },
  avatarCircle: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center', justifyContent: 'center',
  },
  avatarText: { color: Colors.white, fontSize: Typography.md, fontWeight: '700' },
  list: { padding: Spacing.base, paddingBottom: Spacing.xxxl },
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    marginBottom: Spacing.md,
    flexDirection: 'row',
    overflow: 'hidden',
    ...Shadow.card,
  },
  accentBar:    { width: 5 },
  cardContent:  { flex: 1, padding: Spacing.md },
  cardTop:      { flexDirection: 'row', justifyContent: 'space-between', marginBottom: Spacing.xs },
  cardTopRight: { alignItems: 'flex-end', gap: 4 },
  patientName:  { fontSize: Typography.md, fontWeight: '700', color: Colors.textPrimary },
  patientDemo:  { fontSize: Typography.sm, color: Colors.textSecondary, marginTop: 2 },
  dayBadge:     { fontSize: Typography.xs, color: Colors.textMuted, marginTop: 2 },
  diagnosis: {
    fontSize: Typography.sm,
    color: Colors.textPrimary,
    lineHeight: 20,
    marginBottom: Spacing.sm,
  },
  alertRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: Spacing.xs,
    marginTop: Spacing.xs,
  },
  alertChip: {
    backgroundColor: '#FFF3E0',
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
  },
  alertChipBlue:  { backgroundColor: Colors.brandAccent },
  alertChipText:  { fontSize: Typography.xs, color: Colors.warning, fontWeight: '600' },
  uhid:           { fontSize: Typography.xs, color: Colors.textMuted, marginLeft: 'auto' },
});
