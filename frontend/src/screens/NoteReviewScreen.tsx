/**
 * AC Agent — Note Review Screen
 * Associate reviews AI-generated SOAP note section by section.
 * Inline editing. One-tap approval. Full HITL compliance.
 */

import React, { useState } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TextInput,
  TouchableOpacity, Alert, ActivityIndicator
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/RootNavigator';
import { Colors, Typography, Spacing, Radius, Shadow } from '../utils/design';
import { Button, AlertBanner, Card, SectionHeader } from '../components/ui';
import { noteAPI } from '../services/api';
import { useNoteStore } from '../hooks/useBriefingStore';
import { usePatients } from '../context/PatientContext';

type Route = RouteProp<RootStackParamList, 'NoteReview'>;
type Nav   = NativeStackNavigationProp<RootStackParamList, 'NoteReview'>;

type SectionKey = 'subjective' | 'objective' | 'assessment' | 'plan' | 'discussion';

const SECTIONS: { key: SectionKey; label: string; icon: string }[] = [
  { key: 'subjective',  label: 'Subjective',  icon: '💬' },
  { key: 'objective',   label: 'Objective',   icon: '📊' },
  { key: 'assessment',  label: 'Assessment',  icon: '🔍' },
  { key: 'plan',        label: 'Plan',        icon: '📋' },
  { key: 'discussion',  label: 'Discussion',  icon: '🤝' },
];

export default function NoteReviewScreen() {
  const navigation = useNavigation<Nav>();
  const route      = useRoute<Route>();
  const { noteId, patientId } = route.params;

  const { soapNote } = useNoteStore(noteId);
  const { refreshPatient } = usePatients();

  // Editable copies of each section
  const [edits, setEdits] = useState<Partial<Record<SectionKey, string>>>({});
  const [editingSection, setEditingSection] = useState<SectionKey | null>(null);
  const [approving, setApproving] = useState(false);
  const [scrolledAll, setScrolledAll] = useState(false);
  const [sectionsViewed, setSectionsViewed] = useState<Set<string>>(new Set());

  if (!soapNote) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <Text style={{ color: Colors.textSecondary }}>Note not found. Go back.</Text>
      </View>
    );
  }

  const getValue = (key: SectionKey): string => {
    if (edits[key] !== undefined) return edits[key]!;
    if (key === 'objective') {
      return [soapNote.objective_vitals, soapNote.objective_investigations, soapNote.objective_examination]
        .filter(Boolean).join('\n\n');
    }
    return (soapNote as any)[key] ?? '';
  };

  const markViewed = (key: string) => {
    setSectionsViewed(prev => {
      const next = new Set(prev);
      next.add(key);
      if (next.size >= SECTIONS.filter(s => getValue(s.key as SectionKey)).length) {
        setScrolledAll(true);
      }
      return next;
    });
  };

  const handleApprove = async () => {
    if (!scrolledAll) {
      Alert.alert('Review Required', 'Please review all sections before approving.');
      return;
    }
    setApproving(true);
    try {
      await noteAPI.approve({
        note_id: noteId,
        subjective_override:  edits.subjective,
        objective_override:   edits.objective,
        assessment_override:  edits.assessment,
        plan_override:        edits.plan,
        discussion_override:  edits.discussion,
      });
      await refreshPatient(patientId);
      Alert.alert('✓ Note Filed', 'The clinical note has been approved and filed to the patient record.', [
        { text: 'Done', onPress: () => navigation.navigate('PatientDashboard', { patientId }) }
      ]);
    } catch (err: any) {
      Alert.alert('Error', err.message ?? 'Failed to approve note. Please try again.');
    } finally {
      setApproving(false);
    }
  };

  const hasEdits = Object.keys(edits).length > 0;
  const noteTypeLabel = (soapNote.note_type ?? 'note').replace('_', ' ').toUpperCase();

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>

        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>{noteTypeLabel}</Text>
          <Text style={styles.headerSub}>Review each section. Tap Edit to modify. Approve when ready.</Text>
          {soapNote.quality_flags?.length > 0 && (
            <AlertBanner
              message={`Quality flags: ${soapNote.quality_flags.join(' · ')}`}
              type="warning"
            />
          )}
          {hasEdits && (
            <AlertBanner
              message="You have made edits. These will be recorded in the audit trail."
              type="info"
            />
          )}
        </View>

        {/* SOAP Sections */}
        {SECTIONS.map(section => {
          const value = getValue(section.key);
          if (!value && section.key === 'discussion') return null;
          const isEditing = editingSection === section.key;
          const wasEdited = edits[section.key] !== undefined;
          const isViewed  = sectionsViewed.has(section.key);

          return (
            <View key={section.key} style={styles.section}>
              <View style={styles.sectionHeaderRow}>
                <Text style={styles.sectionIcon}>{section.icon}</Text>
                <Text style={styles.sectionLabel}>{section.label}</Text>
                {wasEdited && <View style={styles.editedChip}><Text style={styles.editedChipText}>Edited</Text></View>}
                {isViewed && !isEditing && <Text style={styles.viewedCheck}>✓</Text>}
              </View>

              {isEditing ? (
                <View>
                  <TextInput
                    style={styles.editInput}
                    value={edits[section.key] ?? value}
                    onChangeText={text => setEdits(prev => ({ ...prev, [section.key]: text }))}
                    multiline
                    autoFocus
                    textAlignVertical="top"
                  />
                  <View style={styles.editActions}>
                    <TouchableOpacity
                      onPress={() => {
                        const { [section.key]: _, ...rest } = edits;
                        setEdits(rest);
                        setEditingSection(null);
                      }}
                      style={styles.editBtn}
                    >
                      <Text style={styles.editBtnText}>Discard</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      onPress={() => setEditingSection(null)}
                      style={[styles.editBtn, styles.editBtnSave]}
                    >
                      <Text style={[styles.editBtnText, { color: Colors.white }]}>Save Edit</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ) : (
                <View>
                  <Text
                    style={styles.sectionContent}
                    onLayout={() => markViewed(section.key)}
                  >
                    {value || '—'}
                  </Text>
                  <TouchableOpacity
                    onPress={() => setEditingSection(section.key)}
                    style={styles.editTrigger}
                  >
                    <Text style={styles.editTriggerText}>✏ Edit this section</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
          );
        })}

        {/* Next review trigger */}
        {soapNote.next_review_trigger && (
          <View style={styles.reviewTrigger}>
            <Text style={styles.reviewTriggerLabel}>NEXT REVIEW</Text>
            <Text style={styles.reviewTriggerValue}>{soapNote.next_review_trigger}</Text>
          </View>
        )}

        {/* AI Notice */}
        <Text style={styles.aiNotice}>
          Note generated with AI assistance (claude-sonnet-4-6).{'\n'}
          Your approval makes you the accountable clinician for this entry.
        </Text>

      </ScrollView>

      {/* Sticky Approve Button */}
      <View style={styles.footer}>
        {!scrolledAll && (
          <Text style={styles.scrollHint}>⬆ Scroll through all sections to enable approval</Text>
        )}
        <Button
          label={approving ? 'Filing...' : '✓  Approve & File Note'}
          onPress={handleApprove}
          loading={approving}
          disabled={!scrolledAll}
          variant="success"
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container:    { flex: 1, backgroundColor: Colors.background },
  scroll:       { padding: Spacing.base, paddingBottom: 120 },
  header: {
    backgroundColor: Colors.brandDark,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    marginBottom: Spacing.base,
  },
  headerTitle:  { fontSize: Typography.lg, fontWeight: '800', color: Colors.white },
  headerSub:    { fontSize: Typography.sm, color: 'rgba(255,255,255,0.7)', marginTop: 4, marginBottom: Spacing.sm },
  section: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.lg,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    ...Shadow.card,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.sm,
    gap: Spacing.xs,
  },
  sectionIcon:  { fontSize: 18 },
  sectionLabel: { fontSize: Typography.base, fontWeight: '700', color: Colors.brandDark, flex: 1 },
  editedChip: {
    backgroundColor: Colors.brandAccent,
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
  },
  editedChipText: { fontSize: Typography.xs, color: Colors.brandMid, fontWeight: '600' },
  viewedCheck:    { fontSize: Typography.base, color: Colors.success },
  sectionContent: {
    fontSize: Typography.sm,
    color: Colors.textPrimary,
    lineHeight: 22,
  },
  editTrigger: {
    marginTop: Spacing.sm,
    alignSelf: 'flex-end',
  },
  editTriggerText: { fontSize: Typography.xs, color: Colors.brandMid, fontWeight: '600' },
  editInput: {
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.brandMid,
    borderRadius: Radius.md,
    padding: Spacing.md,
    fontSize: Typography.sm,
    color: Colors.textPrimary,
    lineHeight: 22,
    minHeight: 120,
  },
  editActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: Spacing.sm,
    marginTop: Spacing.sm,
  },
  editBtn: {
    borderRadius: Radius.md,
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  editBtnSave: { backgroundColor: Colors.brandMid, borderColor: Colors.brandMid },
  editBtnText: { fontSize: Typography.sm, color: Colors.textPrimary, fontWeight: '600' },
  reviewTrigger: {
    backgroundColor: Colors.brandAccent,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.base,
  },
  reviewTriggerLabel: { fontSize: Typography.xs, color: Colors.textMuted, fontWeight: '700', letterSpacing: 0.5 },
  reviewTriggerValue: { fontSize: Typography.sm, color: Colors.brandDark, marginTop: 4, lineHeight: 20 },
  aiNotice: {
    fontSize: Typography.xs,
    color: Colors.textMuted,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: Spacing.base,
  },
  footer: {
    position: 'absolute',
    bottom: 0, left: 0, right: 0,
    backgroundColor: Colors.surface,
    padding: Spacing.base,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
    ...Shadow.modal,
  },
  scrollHint: {
    fontSize: Typography.xs,
    color: Colors.textMuted,
    textAlign: 'center',
    marginBottom: Spacing.sm,
  },
});
