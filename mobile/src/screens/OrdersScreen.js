import React, { useState, useCallback } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { getOrders } from '../services/api';
import { colors as C, statusColors } from '../theme';

export default function OrdersScreen({ navigation }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    getOrders().then(setOrders).catch(() => {}).finally(() => setLoading(false));
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <FlatList
        data={orders}
        keyExtractor={(i) => i.id}
        refreshing={loading}
        onRefresh={load}
        contentContainerStyle={{ padding: 16 }}
        ListEmptyComponent={<Text style={s.empty}>No tienes pedidos aun</Text>}
        renderItem={({ item }) => {
          const badgeColor = statusColors[item.status] || C.accent;
          return (
            <TouchableOpacity style={s.card} onPress={() => navigation.navigate('OrderDetail', { orderId: item.id })}>
              <View style={s.headerRow}>
                <Text style={s.orderId}>#{item.id.slice(0, 8)}</Text>
                <View style={[s.badge, { backgroundColor: `${badgeColor}22` }]}>
                  <Text style={{ color: badgeColor, fontSize: 12, fontWeight: '600' }}>{item.status}</Text>
                </View>
              </View>
              <Text style={s.storeName}>{item.store_name || 'Sin sucursal'}</Text>
              <View style={s.metaRow}>
                <Text style={{ color: C.muted, fontSize: 13 }}>{item.items?.length || 0} productos</Text>
                <Text style={{ color: C.text, fontWeight: '700' }}>Bs {Number(item.total).toFixed(2)}</Text>
              </View>
            </TouchableOpacity>
          );
        }}
      />
    </View>
  );
}

const s = StyleSheet.create({
  empty: { textAlign: 'center', color: C.muted, marginTop: 60 },
  card: { backgroundColor: C.card, borderRadius: 12, padding: 16, marginBottom: 10, borderWidth: 1, borderColor: C.border },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, gap: 10 },
  orderId: { fontFamily: 'monospace', color: C.accent, fontSize: 13 },
  badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  storeName: { color: C.text, fontWeight: '600' },
  metaRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
});
