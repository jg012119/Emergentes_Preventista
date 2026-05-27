import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors as C } from '../theme';

export default function HomeScreen({ navigation }) {
  const actions = [
    { label: 'Nuevo Pedido', icon: 'cart-outline', desc: 'Selecciona productos del catalogo', screen: 'Catalog' },
    { label: 'Mis Sucursales', icon: 'storefront-outline', desc: 'Gestiona tus sucursales registradas', screen: 'Sucursales' },
    { label: 'Mis Pedidos', icon: 'clipboard-outline', desc: 'Historial y estado de tus pedidos', screen: 'Pedidos' },
  ];

  return (
    <View style={s.container}>
      <View style={s.heroRow}>
        <Text style={s.heroTitle}>Bienvenido</Text>
        <Ionicons name="hand-left-outline" size={26} color={C.warning} />
      </View>
      <Text style={s.subtitle}>Que deseas hacer hoy?</Text>

      {actions.map((a) => (
        <TouchableOpacity
          key={a.screen}
          style={s.card}
          onPress={() => navigation.navigate(a.screen)}
        >
          <View style={s.cardRow}>
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
  heroRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 12 },
  heroTitle: { fontSize: 26, fontWeight: '800', color: C.text },
  subtitle: { fontSize: 15, color: C.muted, marginBottom: 28, marginTop: 4 },
  card: { backgroundColor: C.card, borderRadius: 14, padding: 16, marginBottom: 14, borderWidth: 1, borderColor: C.border },
  cardRow: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  iconContainer: { width: 44, height: 44, borderRadius: 10, backgroundColor: C.input, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: C.border },
  cardLabel: { fontSize: 16, fontWeight: '700', color: C.text, marginBottom: 2 },
  cardDesc: { fontSize: 13, color: C.muted },
});
