/**
 * AC Agent — Briefing Co-Pilot Screen
 * The live AI assistant during the family meeting.
 * Eyes-up design. Large touch targets. Dark mode for ICU lighting.
 */

import React, { useState, useCallback } from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  SafeAreaView, Alert
} from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../navigation/RootNavigator';
import { Colors, Typography, Spacing, Radius } from '../utils/design';
import { ChecklistItem, QACard, KeyNumber, DoNotSayItem, AlertBanner, MilestoneRow } from '../components/ui';
import { useBriefingStore } from '../hooks/useBriefingStore';

type Route = RouteProp<RootStackParamList, 'BriefingCopilot'>;
type Nav   = NativeStackNavigationProp<RootStackParamList, 'BriefingCopilot'>;

const QUESTIONS = [
  { key: 'q1', label: 'Current condition explained' },
  { key: 'q2', label: 'Treatment explained' },
  { key: 'q3', label: 'Ventilator / breathing discussed' },
  { key: 'q4', label: 'Ward transfer milestones shown' },
  { key: 'q5', label: 'Cause of illness explained' },
];

type Tab = 'checklist' | 'answers' | 'milestones' | 'donotsay';

export default function BriefingCopilot() {
  const navigation = useNavigation<Nav>();
  const route      = useRoute<Route>();
  const { briefingId, patientId } = route.params;

  const { document, patientName } = useBriefingStore(briefingId);

  const [checkedTopics, setCheckedTopics]   = useState<Record<string, boolean>>({});
  const [expandedQA, setExpandedQA]         = useState<number | null>(null);
  const [activeTab, setActiveTab]           = useState<Tab>('checklist');

  const toggleTopic = useCallback((key: string) => {
    setCheckedTopics(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const toggleQA = useCallback((i: number) => {
    setExpandedQA(prev => prev === i ? null : i);
  }, []);

  const checkedCount = Object.values(checkedTopics).filter(Boolean).length;

  const handleEndBriefing = () => {
    const covered = QUESTIONS.filter(q => checkedTopics[q.key]).map(q => q.key);
    if (covered.length < 3) {
      Alert.alert(
        'Briefing Incomplete',
        `Only ${covered.length} of 5 topics covered. Are you sure you want to end?`,
        [
          { text: 'Continue Briefing', style: 'cancel' },
          { text: 'End Anyway', onPress: () => navigation.navigate('BriefingComplete', { briefingId, patientId }) }
        ]
      );
    } else {
      navigation.navigate('BriefingComplete', { briefingId, patientId });
    }
  };

  if (!document) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Briefing document not found. Go back and regenerate.</Text>
      </View>
    );
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: 'checklist', label: '✓ Topics' },
    { key: 'answers',   label: '💬 Q&A' },
    { key: 'milestones',label: '📊 Steps' },
    { key: 'donotsay',  label: '⛔ Avoid' },
  ];

  return (
    <SafeAreaView style={styles.container}>

      {/* ── Persistent Key Numbers Panel ────────────────────────────────── */}
      <View style={styles.keyPanel}>
        <Text style={styles.keyPanelLabel}>KEY VALUES — {patientName}</Text>
        <View style={styles.keyRow}>
          {(document.key_numbers_panel ?? []).slice(0, 3).map((kn, i) => (
            <KeyNumber key={i} label={kn.label} value={kn.value} status={kn.status} />
          ))}
        </View>
      </View>

      {/* ── Progress indicator ───────────────────────────────────────────── */}
      <View style={styles.progressBar}>
        <View style={[styles.progressFill, { width: `${(checkedCount / 5) * 100}%` as any }]} />
      </View>
      <Text style={styles.progressText}>{checkedCount} of 5 topics covered</Text>

      {/* ── Tab Bar ─────────────────────────────────────────────────────── */}
      <View style={styles.tabBar}>
        {TABS.map(tab => (
          <TouchableOpacity
            key={tab.key}
            onPress={() => setActiveTab(tab.key)}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
          >
            <Text style={[styles.tabText, activeTab === tab.key && styles.tabTextActive]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* ── Tab Content ──────────────────────────────────────────────────── */}
      <ScrollView style={styles.content} contentContainerStyle={{ padding: Spacing.base }}>

        {/* CHECKLIST */}
        {activeTab === 'checklist' && (
          <View>
            <AlertBanner
              message="Tap each topic as you cover it in the family meeting."
              type="info"
            />
            {QUESTIONS.map(q => (
              <ChecklistItem
                key={q.key}
                label={q.label}
                checked={!!checkedTopics[q.key]}
                onToggle={() => toggleTopic(q.key)}
              />
            ))}

            {/* Q content previews */}
            <View style={{ marginTop: Spacing.base }}>
              {[
                { key: 'q1', title: 'Q1 — Condition', content: document.q1_plain_language },
                { key: 'q2', title: 'Q2 — Treatment', content: document.q2_plain_language },
                { key: 'q3', title: 'Q3 — Ventilator', content: document.q3_plain_language },
                { key: 'q4', title: 'Q4 — Ward Transfer', content: document.q4_plain_language },
                { key: 'q5', title: 'Q5 — Cause', content: document.q5_cause_plain },
              ].map(item => (
                <View key={item.key} style={[styles.qBlock, checkedTopics[item.key] && styles.qBlockDone]}>
                  <Text style={styles.qTitle}>{item.title}</Text>
                  <Text style={styles.qContent}>{item.content}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Q&A PANEL */}
        {activeTab === 'answers' && (
          <View>
            <AlertBanner
              message="Pre-generated answers to likely family questions. Tap to expand."
              type="info"
            />
            {(document.predicted_questions ?? []).map((qa, i) => (
              <QACard
                key={i}
                question={qa.question}
                answer={qa.answer_full}
                expanded={expandedQA === i}
                onToggle={() => toggleQA(i)}
              />
            ))}
          </View>
        )}

        {/* MILESTONES */}
        {activeTab === 'milestones' && (
          <View>
            <AlertBanner
              message="Show this to the family on screen — it explains the recovery journey clearly."
              type="info"
            />
            <Text style={styles.milestoneTitle}>Steps to Ward Transfer</Text>
            {(document.q4_milestones ?? []).map((m, i) => (
              <MilestoneRow key={i} step={m.step} description={m.description} status={m.status} />
            ))}

            {document.q3_conditional_phrases && (
              <View style={[styles.qBlock, { marginTop: Spacing.base }]}>
                <Text style={styles.qTitle}>If family asks for a specific date...</Text>
                <Text style={styles.qContent}>{document.q3_conditional_phrases.if_family_pushes_for_date}</Text>
              </View>
            )}
          </View>
        )}

        {/* DO NOT SAY */}
        {activeTab === 'donotsay' && (
          <View>
            <AlertBanner
              message="These are case-specific things to avoid saying in this briefing."
              type="warning"
            />
            {(document.q1_do_not_say ?? []).map((text, i) => (
              <DoNotSayItem key={i} text={text} />
            ))}
            {document.q5_escalation_prompt && (
              <View style={styles.escalationBox}>
                <Text style={styles.escalationTitle}>↑ Escalation Prompt</Text>
                <Text style={styles.escalationText}>{document.q5_escalation_prompt}</Text>
              </View>
            )}
          </View>
        )}

      </ScrollView>

      {/* ── End Briefing Button ──────────────────────────────────────────── */}
      <View style={styles.footer}>
        <TouchableOpacity onPress={handleEndBriefing} style={styles.endButton}>
          <Text style={styles.endButtonText}>End Briefing & File Log →</Text>
        </TouchableOpacity>
      </View>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container:      { flex: 1, backgroundColor: '#0D2440' },   // Dark for ICU lighting
  keyPanel: {
    backgroundColor: '#162D50',
    padding: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  keyPanelLabel:  { fontSize: Typography.xs, color: 'rgba(255,255,255,0.5)', marginBottom: Spacing.sm, letterSpacing: 0.5 },
  keyRow:         { flexDirection: 'row', gap: Spacing.sm },
  progressBar:    { height: 3, backgroundColor: 'rgba(255,255,255,0.1)' },
  progressFill:   { height: 3, backgroundColor: Colors.brandMid },
  progressText:   { fontSize: Typography.xs, color: 'rgba(255,255,255,0.5)', textAlign: 'center', paddingVertical: 4 },
  tabBar: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  tab: {
    flex: 1, paddingVertical: Spacing.sm,
    alignItems: 'center',
  },
  tabActive:      { borderBottomWidth: 2, borderBottomColor: Colors.brandMid },
  tabText:        { fontSize: Typography.xs, color: 'rgba(255,255,255,0.5)' },
  tabTextActive:  { color: Colors.white, fontWeight: '600' },
  content:        { flex: 1 },
  qBlock: {
    backgroundColor: 'rgba(255,255,255,0.07)',
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderLeftWidth: 3,
    borderLeftColor: Colors.brandMid,
  },
  qBlockDone: {
    opacity: 0.5,
    borderLeftColor: Colors.success,
  },
  qTitle:    { fontSize: Typography.sm, fontWeight: '700', color: Colors.brandLight, marginBottom: 6 },
  qContent:  { fontSize: Typography.sm, color: 'rgba(255,255,255,0.85)', lineHeight: 22 },
  milestoneTitle: {
    fontSize: Typography.base,
    fontWeight: '700',
    color: Colors.white,
    marginBottom: Spacing.sm,
  },
  escalationBox: {
    backgroundColor: 'rgba(46,117,182,0.2)',
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginTop: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.brandMid,
  },
  escalationTitle: { fontSize: Typography.sm, fontWeight: '700', color: Colors.brandLight, marginBottom: 4 },
  escalationText:  { fontSize: Typography.sm, color: 'rgba(255,255,255,0.85)', lineHeight: 20 },
  footer: {
    padding: Spacing.base,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  endButton: {
    backgroundColor: Colors.success,
    borderRadius: Radius.md,
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  endButtonText: { color: Colors.white, fontSize: Typography.base, fontWeight: '700' },
  errorText: { color: Colors.white, textAlign: 'center', padding: Spacing.xxl },
});
