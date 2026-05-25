import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const C = { bg: '#0f1117', card: '#1a1d29', accent: '#6366f1', accentLight: '#818cf8', text: '#f0f2f5', muted: '#8b92a5', border: '#2a2f45' };

export default function HomeScreen({ navigation }) {
  const actions = [
    { label: 'Nuevo Pedido', icon: 'cart-outline', desc: 'Selecciona productos del catálogo', screen: 'Catalog' },
    { label: 'Mis Tiendas', icon: 'storefront-outline', desc: 'Gestiona tus tiendas registradas', screen: 'Tiendas' },
    { label: 'Mis Pedidos', icon: 'clipboard-outline', desc: 'Historial y estado de tus pedidos', screen: 'Pedidos' },
  ];

  return (
    <View style={s.container}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 12 }}>
        <Text style={{ fontSize: 26, fontWeight: '800', color: C.text }}>¡Bienvenido!</Text>
        <Ionicons name="hand-left-outline" size={26} color="#fbbf24" />
      </View>
      <Text style={s.subtitle}>¿Qué deseas hacer hoy?</Text>

      {actions.map((a, i) => (
        <TouchableOpacity
          key={i}
          style={s.card}
          onPress={() => navigation.navigate(a.screen)}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 14 }}>
            <View style={s.iconContainer}>
              <Ionicons name={a.icon} size={24} color={C.accent} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={s.cardLabel}>{a.label}</Text>
              <Text style={s.cardDesc}>{a.desc}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={C.muted} />
          </View>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg, padding: 20 },
  subtitle: { fontSize: 15, color: C.muted, marginBottom: 28, marginTop: 4 },
  card: { backgroundColor: C.card, borderRadius: 14, padding: 16, marginBottom: 14, borderWidth: 1, borderColor: C.border },
  iconContainer: { width: 44, height: 44, borderRadius: 10, backgroundColor: '#181b27', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: C.border },
  cardLabel: { fontSize: 16, fontWeight: '700', color: C.text, marginBottom: 2 },
  cardDesc: { fontSize: 13, color: C.muted },
});
