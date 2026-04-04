/**
 * AC Agent — Shared UI Components
 */

import React, { ReactNode } from 'react';
import {
  View, Text, TouchableOpacity, ActivityIndicator,
  StyleSheet, ViewStyle, TextStyle,
} from 'react-native';
import { Colors, Typography, Spacing, Radius, Shadow, trajectoryColor, trajectoryLabel } from '../utils/design';

// ── Card ──────────────────────────────────────────────────────────────────────

export function Card({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

// ── Section Header ────────────────────────────────────────────────────────────

export function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {subtitle && <Text style={styles.sectionSubtitle}>{subtitle}</Text>}
    </View>
  );
}

// ── Primary Button ────────────────────────────────────────────────────────────

type BtnProps = {
  label: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  style?: ViewStyle;
};

export function Button({ label, onPress, loading, disabled, variant = 'primary', style }: BtnProps) {
  const bgMap = {
    primary:   Colors.brandMid,
    secondary: Colors.brandLight,
    danger:    Colors.critical,
    success:   Colors.success,
  };
  const textMap = {
    primary:   Colors.white,
    secondary: Colors.brandDark,
    danger:    Colors.white,
    success:   Colors.white,
  };
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      style={[styles.button, { backgroundColor: bgMap[variant], opacity: (disabled || loading) ? 0.6 : 1 }, style]}
      activeOpacity={0.8}
    >
      {loading
        ? <ActivityIndicator color={textMap[variant]} size="small" />
        : <Text style={[styles.buttonText, { color: textMap[variant] }]}>{label}</Text>
      }
    </TouchableOpacity>
  );
}

// ── Trajectory Badge ──────────────────────────────────────────────────────────

export function TrajectoryBadge({ trajectory }: { trajectory: string }) {
  return (
    <View style={[styles.badge, { backgroundColor: trajectoryColor(trajectory) }]}>
      <Text style={styles.badgeText}>{trajectoryLabel(trajectory)}</Text>
    </View>
  );
}

// ── Status Dot ────────────────────────────────────────────────────────────────

export function StatusDot({ status }: { status: 'achieved' | 'in_progress' | 'not_yet' }) {
  const colors = {
    achieved:    Colors.success,
    in_progress: Colors.warning,
    not_yet:     Colors.border,
  };
  return <View style={[styles.dot, { backgroundColor: colors[status] }]} />;
}

// ── Key Number Panel Item ─────────────────────────────────────────────────────

export function KeyNumber({ label, value, status }: { label: string; value: string; status: string }) {
  const color = status === 'critical' ? Colors.critical : status === 'abnormal' ? Colors.warning : Colors.brandDark;
  return (
    <View style={styles.keyNumber}>
      <Text style={styles.keyNumberLabel}>{label}</Text>
      <Text style={[styles.keyNumberValue, { color }]}>{value}</Text>
    </View>
  );
}

// ── Info Row ──────────────────────────────────────────────────────────────────

export function InfoRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={[styles.infoValue, highlight && { color: Colors.critical, fontWeight: '600' }]}>{value}</Text>
    </View>
  );
}

// ── Alert Banner ──────────────────────────────────────────────────────────────

export function AlertBanner({ message, type = 'info' }: { message: string; type?: 'info' | 'warning' | 'error' | 'success' }) {
  const colors = {
    info:    { bg: Colors.brandAccent, text: Colors.brandDark, border: Colors.brandMid },
    warning: { bg: '#FFF3E0', text: Colors.warning, border: Colors.warning },
    error:   { bg: '#FFEBEE', text: Colors.critical, border: Colors.critical },
    success: { bg: '#E8F5E9', text: Colors.success, border: Colors.success },
  };
  const c = colors[type];
  return (
    <View style={[styles.alertBanner, { backgroundColor: c.bg, borderLeftColor: c.border }]}>
      <Text style={[styles.alertText, { color: c.text }]}>{message}</Text>
    </View>
  );
}

// ── Do Not Say Card ───────────────────────────────────────────────────────────

export function DoNotSayItem({ text }: { text: string }) {
  return (
    <View style={styles.doNotSay}>
      <Text style={styles.doNotSayIcon}>⛔</Text>
      <Text style={styles.doNotSayText}>{text}</Text>
    </View>
  );
}

// ── Q&A Card ─────────────────────────────────────────────────────────────────

export function QACard({
  question, answer, expanded, onToggle
}: { question: string; answer: string; expanded: boolean; onToggle: () => void }) {
  return (
    <TouchableOpacity onPress={onToggle} style={styles.qaCard} activeOpacity={0.85}>
      <View style={styles.qaHeader}>
        <Text style={styles.qaQuestion}>{question}</Text>
        <Text style={styles.qaChevron}>{expanded ? '▲' : '▼'}</Text>
      </View>
      {expanded && <Text style={styles.qaAnswer}>{answer}</Text>}
    </TouchableOpacity>
  );
}

// ── Checklist Item ────────────────────────────────────────────────────────────

export function ChecklistItem({
  label, checked, onToggle
}: { label: string; checked: boolean; onToggle: () => void }) {
  return (
    <TouchableOpacity onPress={onToggle} style={styles.checklistItem} activeOpacity={0.7}>
      <View style={[styles.checkbox, checked && styles.checkboxChecked]}>
        {checked && <Text style={styles.checkmark}>✓</Text>}
      </View>
      <Text style={[styles.checklistLabel, checked && styles.checklistLabelChecked]}>{label}</Text>
    </TouchableOpacity>
  );
}

// ── Milestone Row ─────────────────────────────────────────────────────────────

export function MilestoneRow({ step, description, status }: { step: number; description: string; status: string }) {
  const colors: Record<string, string> = {
    achieved:    Colors.success,
    in_progress: Colors.warning,
    not_yet:     Colors.border,
  };
  const icons: Record<string, string> = {
    achieved: '✓', in_progress: '◎', not_yet: '○'
  };
  const color = colors[status] ?? Colors.border;
  return (
    <View style={styles.milestoneRow}>
      <View style={[styles.milestoneIcon, { backgroundColor: color }]}>
        <Text style={styles.milestoneIconText}>{icons[status] ?? '○'}</Text>
      </View>
      <View style={styles.milestoneContent}>
        <Text style={styles.milestoneStep}>Step {step}</Text>
        <Text style={[styles.milestoneDesc, { color: status === 'not_yet' ? Colors.textMuted : Colors.textPrimary }]}>
          {description}
        </Text>
      </View>
    </View>
  );
}

// ── Loading Screen ────────────────────────────────────────────────────────────

export function LoadingScreen({ message }: { message?: string }) {
  return (
    <View style={styles.loadingScreen}>
      <ActivityIndicator size="large" color={Colors.brandMid} />
      {message && <Text style={styles.loadingText}>{message}</Text>}
    </View>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────

export function EmptyState({ icon, title, subtitle }: { icon: string; title: string; subtitle?: string }) {
  return (
    <View style={styles.emptyState}>
      <Text style={styles.emptyIcon}>{icon}</Text>
      <Text style={styles.emptyTitle}>{title}</Text>
      {subtitle && <Text style={styles.emptySubtitle}>{subtitle}</Text>}
    </View>
  );
}

// ══════════════════════════════════════════════════════════════════════════════
//  STYLES
// ══════════════════════════════════════════════════════════════════════════════

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    ...Shadow.card,
  },
  sectionHeader: {
    paddingHorizontal: Spacing.base,
    paddingTop: Spacing.base,
    paddingBottom: Spacing.sm,
  },
  sectionTitle: {
    fontSize: Typography.md,
    fontWeight: Typography.bold,
    color: Colors.brandDark,
  },
  sectionSubtitle: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  button: {
    borderRadius: Radius.md,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
  },
  buttonText: {
    fontSize: Typography.base,
    fontWeight: Typography.semibold,
  },
  badge: {
    borderRadius: Radius.full,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 3,
    alignSelf: 'flex-start',
  },
  badgeText: {
    color: Colors.white,
    fontSize: Typography.xs,
    fontWeight: Typography.bold,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  dot: {
    width: 10, height: 10, borderRadius: 5,
  },
  keyNumber: {
    flex: 1,
    backgroundColor: Colors.brandAccent,
    borderRadius: Radius.md,
    padding: Spacing.sm,
    alignItems: 'center',
    marginHorizontal: 3,
  },
  keyNumberLabel: {
    fontSize: Typography.xs,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  keyNumberValue: {
    fontSize: Typography.md,
    fontWeight: Typography.bold,
    textAlign: 'center',
    marginTop: 2,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: Spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: Colors.divider,
  },
  infoLabel: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    flex: 1,
  },
  infoValue: {
    fontSize: Typography.sm,
    color: Colors.textPrimary,
    flex: 2,
    textAlign: 'right',
  },
  alertBanner: {
    borderLeftWidth: 4,
    borderRadius: Radius.sm,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
  },
  alertText: {
    fontSize: Typography.sm,
    lineHeight: 20,
  },
  doNotSay: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFEBEE',
    borderRadius: Radius.sm,
    padding: Spacing.sm,
    marginBottom: Spacing.xs,
  },
  doNotSayIcon: { fontSize: 14, marginRight: Spacing.sm },
  doNotSayText: {
    flex: 1,
    fontSize: Typography.sm,
    color: Colors.critical,
    lineHeight: 20,
  },
  qaCard: {
    backgroundColor: Colors.surface,
    borderRadius: Radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  qaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  qaQuestion: {
    flex: 1,
    fontSize: Typography.base,
    fontWeight: Typography.semibold,
    color: Colors.brandDark,
    lineHeight: 22,
  },
  qaChevron: {
    fontSize: Typography.sm,
    color: Colors.textMuted,
    marginLeft: Spacing.sm,
  },
  qaAnswer: {
    marginTop: Spacing.sm,
    fontSize: Typography.sm,
    color: Colors.textPrimary,
    lineHeight: 22,
    borderTopWidth: 1,
    borderTopColor: Colors.divider,
    paddingTop: Spacing.sm,
  },
  checklistItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.divider,
  },
  checkbox: {
    width: 28, height: 28,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: Colors.brandMid,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  checkboxChecked: {
    backgroundColor: Colors.brandMid,
    borderColor: Colors.brandMid,
  },
  checkmark: { color: Colors.white, fontSize: 16, fontWeight: 'bold' },
  checklistLabel: {
    flex: 1,
    fontSize: Typography.base,
    color: Colors.textPrimary,
    lineHeight: 22,
  },
  checklistLabelChecked: {
    color: Colors.textMuted,
    textDecorationLine: 'line-through',
  },
  milestoneRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
  },
  milestoneIcon: {
    width: 36, height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  milestoneIconText: { color: Colors.white, fontSize: 14, fontWeight: 'bold' },
  milestoneContent: { flex: 1 },
  milestoneStep: {
    fontSize: Typography.xs,
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  milestoneDesc: {
    fontSize: Typography.base,
    lineHeight: 22,
    marginTop: 2,
  },
  loadingScreen: {
    flex: 1, alignItems: 'center', justifyContent: 'center',
    backgroundColor: Colors.background, gap: Spacing.md,
  },
  loadingText: {
    fontSize: Typography.base,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginTop: Spacing.sm,
  },
  emptyState: {
    flex: 1, alignItems: 'center', justifyContent: 'center',
    padding: Spacing.xxxl,
  },
  emptyIcon: { fontSize: 48, marginBottom: Spacing.base },
  emptyTitle: {
    fontSize: Typography.lg,
    fontWeight: Typography.semibold,
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: Typography.sm,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginTop: Spacing.sm,
    lineHeight: 22,
  },
});
