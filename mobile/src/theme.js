import { StyleSheet } from 'react-native';

export const colors = {
  bg: '#110d24',
  panel: 'rgba(29,22,58,0.86)',
  card: 'rgba(50,39,91,0.56)',
  surface: 'rgba(63,49,111,0.48)',
  surfaceAlt: 'rgba(83,65,145,0.42)',
  input: 'rgba(24,18,48,0.72)',
  border: 'rgba(221,211,255,0.16)',
  borderStrong: 'rgba(221,211,255,0.28)',
  text: '#f7f2ff',
  muted: '#b8acd8',
  mutedStrong: '#8d80b8',
  accent: '#9b7cff',
  accentLight: '#d9ccff',
  accentDark: '#6e4fed',
  accentSoft: 'rgba(155,124,255,0.18)',
  secondary: '#4fd1ff',
  secondarySoft: 'rgba(79,209,255,0.14)',
  userBubble: 'rgba(126,87,255,0.62)',
  userBubbleBorder: 'rgba(211,194,255,0.30)',
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#4fd1ff',
  white: '#ffffff',
  black: '#110d24',
  dangerSoft: 'rgba(239,68,68,0.12)',
  dangerBorder: 'rgba(239,68,68,0.3)',
  dangerText: '#fecaca',
  whiteMuted: 'rgba(255,255,255,0.65)',
  whiteSoft: 'rgba(255,255,255,0.7)',
  glow: 'rgba(155,124,255,0.36)',
};

export const statusColors = {
  pendiente: colors.warning,
  confirmado: colors.success,
  rechazado: colors.danger,
  en_proceso: colors.info,
  borrador: colors.accent,
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
};

export const radius = {
  sm: 8,
  md: 10,
  lg: 12,
  xl: 16,
  pill: 999,
};

export const globalStyles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.bg,
  },
  card: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.lg,
  },
  glassCard: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.xl,
  },
  input: {
    backgroundColor: colors.input,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    color: colors.text,
  },
});

export default {
  colors,
  statusColors,
  spacing,
  radius,
  globalStyles,
};
