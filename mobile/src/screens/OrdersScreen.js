import React, { useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { getOrders } from '../services/api';

const C = { bg: '#0f1117', card: '#1a1d29', accent: '#6366f1', text: '#f0f2f5', muted: '#8b92a5', border: '#2a2f45' };
const BADGE = { pendiente: '#f59e0b', confirmado: '#22c55e', rechazado: '#ef4444', en_proceso: '#3b82f6', borrador: '#818cf8' };

export default function OrdersScreen({ navigation }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => { setLoading(true); getOrders().then(setOrders).catch(() => {}).finally(() => setLoading(false)); };
  useFocusEffect(useCallback(() => { load(); }, []));

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <FlatList data={orders} keyExtractor={i => i.id} refreshing={loading} onRefresh={load}
        contentContainerStyle={{ padding: 16 }}
        ListEmptyComponent={<Text style={{ textAlign: 'center', color: C.muted, marginTop: 60 }}>No tienes pedidos aún</Text>}
        renderItem={({ item }) => (
          <TouchableOpacity style={s.card} onPress={() => navigation.navigate('OrderDetail', { orderId: item.id })}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <Text style={{ fontFamily: 'monospace', color: C.accent, fontSize: 13 }}>#{item.id.slice(0, 8)}</Text>
              <View style={[s.badge, { backgroundColor: (BADGE[item.status] || C.accent) + '22' }]}>
                <Text style={{ color: BADGE[item.status] || C.accent, fontSize: 12, fontWeight: '600' }}>{item.status}</Text>
              </View>
            </View>
            <Text style={{ color: C.text, fontWeight: '600' }}>{item.store_name || 'Sin tienda'}</Text>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 }}>
              <Text style={{ color: C.muted, fontSize: 13 }}>{item.items?.length || 0} productos</Text>
              <Text style={{ color: C.text, fontWeight: '700' }}>Bs {Number(item.total).toFixed(2)}</Text>
            </View>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.card, borderRadius: 12, padding: 16, marginBottom: 10, borderWidth: 1, borderColor: C.border },
  badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
});
