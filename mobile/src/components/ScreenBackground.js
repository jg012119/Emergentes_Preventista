import React from 'react';
import { ScrollView, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const BG_COLORS = ['#2a1860', '#160f32', '#0c0a18'];

export function GradientScreen({ children, style }) {
  return (
    <LinearGradient colors={BG_COLORS} locations={[0, 0.48, 1]} style={[s.screen, style]}>
      {children}
    </LinearGradient>
  );
}

export function GradientScrollView({ children, contentContainerStyle, keyboardShouldPersistTaps, style, ...props }) {
  return (
    <LinearGradient colors={BG_COLORS} locations={[0, 0.48, 1]} style={[s.screen, style]}>
      <ScrollView
        style={s.scroll}
        contentContainerStyle={contentContainerStyle}
        keyboardShouldPersistTaps={keyboardShouldPersistTaps}
        {...props}
      >
        {children}
      </ScrollView>
    </LinearGradient>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1 },
  scroll: { flex: 1, backgroundColor: 'transparent' },
});
