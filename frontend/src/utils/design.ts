/**
 * AC Agent — Design System
 * All visual tokens in one place.
 */

export const Colors = {
  // Brand
  brandDark:   '#1B3A6B',   // Deep navy — primary
  brandMid:    '#2E75B6',   // Mid blue — secondary
  brandLight:  '#D6E4F0',   // Pale blue — fills
  brandAccent: '#E8F4FD',   // Lightest blue — backgrounds

  // Trajectory / Status
  improving:   '#1E7B4B',   // Green
  stable:      '#2E75B6',   // Blue
  guarded:     '#C05911',   // Amber
  critical:    '#B31B1B',   // Red
  deteriorating:'#8B0000',  // Dark red

  // UI
  white:       '#FFFFFF',
  background:  '#F4F6F9',
  surface:     '#FFFFFF',
  border:      '#DDE3ED',
  divider:     '#EEEEEE',

  // Text
  textPrimary:   '#1A1A1A',
  textSecondary: '#555555',
  textMuted:     '#888888',
  textOnDark:    '#FFFFFF',

  // Semantic
  success:  '#1E7B4B',
  warning:  '#C05911',
  error:    '#B31B1B',
  info:     '#2E75B6',

  // ICU specific
  critical_value: '#B31B1B',
  pending:        '#C05911',
  completed:      '#1E7B4B',
};

export const Typography = {
  // Sizes (sp)
  xs:   11,
  sm:   13,
  base: 15,
  md:   17,
  lg:   19,
  xl:   22,
  xxl:  26,
  xxxl: 32,

  // Weights
  regular: '400' as const,
  medium:  '500' as const,
  semibold:'600' as const,
  bold:    '700' as const,
};

export const Spacing = {
  xs:   4,
  sm:   8,
  md:   12,
  base: 16,
  lg:   20,
  xl:   24,
  xxl:  32,
  xxxl: 48,
};

export const Radius = {
  sm:   6,
  md:   10,
  lg:   14,
  xl:   20,
  full: 999,
};

export const Shadow = {
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
  modal: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.15,
    shadowRadius: 16,
    elevation: 8,
  },
};

export const trajectoryColor = (trajectory: string): string => {
  const map: Record<string, string> = {
    improving:    Colors.improving,
    stable:       Colors.stable,
    guarded:      Colors.guarded,
    critical:     Colors.critical,
    deteriorating: Colors.deteriorating,
  };
  return map[trajectory] ?? Colors.stable;
};

export const trajectoryLabel = (trajectory: string): string => {
  const map: Record<string, string> = {
    improving:    '↑ Improving',
    stable:       '→ Stable',
    guarded:      '⚠ Guarded',
    critical:     '🔴 Critical',
    deteriorating:'↓ Deteriorating',
  };
  return map[trajectory] ?? trajectory;
};

export const milestoneColor = (status: string): string => {
  if (status === 'achieved')    return Colors.completed;
  if (status === 'in_progress') return Colors.guarded;
  return Colors.border;
};
