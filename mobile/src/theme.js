import { StyleSheet } from 'react-native';

export const colors = {
  bg: '#0b141a',
  panel: '#111b21',
  card: '#17232b',
  surface: '#17232b',
  surfaceAlt: '#202c33',
  input: '#202c33',
  border: '#2a3942',
  text: '#eef6f7',
  muted: '#8fa4ad',
  mutedStrong: '#6f858e',
  accent: '#25d366',
  accentLight: '#4ade80',
  accentDark: '#128c7e',
  accentSoft: '#10261d',
  userBubble: '#005c4b',
  userBubbleBorder: '#0b6b59',
  success: '#22c55e',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#3b82f6',
  white: '#ffffff',
  black: '#0b141a',
  dangerSoft: 'rgba(239,68,68,0.12)',
  dangerBorder: 'rgba(239,68,68,0.3)',
  dangerText: '#fecaca',
  whiteMuted: 'rgba(255,255,255,0.65)',
  whiteSoft: 'rgba(255,255,255,0.7)',
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
