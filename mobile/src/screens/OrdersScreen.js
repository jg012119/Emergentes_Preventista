import React, { useState, useCallback, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { getOrders } from '../services/api';
import { colors as C, statusColors } from '../theme';
import { GradientScreen } from '../components/ScreenBackground';

const ORDER_FILTERS = [
  { label: 'Todos', value: null },
  { label: 'Pendientes', value: 'pendiente' },
  { label: 'Confirmados', value: 'confirmado' },
  { label: 'En proceso', value: 'en_proceso' },
  { label: 'Rechazados', value: 'rechazado' },
  { label: 'Borradores', value: 'borrador' },
];

const FILTER_EMPTY_LABELS = {
  pendiente: 'pendientes',
  confirmado: 'confirmados',
  en_proceso: 'en proceso',
  rechazado: 'rechazados',
  borrador: 'borradores',
};

export default function OrdersScreen({ route, navigation }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState(route?.params?.statusFilter || null);

  useEffect(() => {
    setStatusFilter(route?.params?.statusFilter || null);
  }, [route?.params?.statusFilter]);

  const load = useCallback(() => {
    setLoading(true);
    getOrders(statusFilter).then(setOrders).catch(() => {}).finally(() => setLoading(false));
  }, [statusFilter]);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const selectFilter = (value) => {
    setStatusFilter(value);
    navigation.setParams?.({ statusFilter: value });
  };

  const emptyLabel = statusFilter ? `No tienes pedidos ${FILTER_EMPTY_LABELS[statusFilter] || statusFilter}` : 'No tienes pedidos aun';

  return (
    <GradientScreen>
      <View style={s.filterWrap}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.filterContent}>
          {ORDER_FILTERS.map((filter) => {
            const active = statusFilter === filter.value;
            return (
              <TouchableOpacity
                key={filter.value || 'all'}
                style={[s.filterChip, active && s.filterChipActive]}
                onPress={() => selectFilter(filter.value)}
              >
                <Text style={[s.filterText, active && s.filterTextActive]}>{filter.label}</Text>
              </TouchableOpacity>
            );
          })}
        </ScrollView>
      </View>

      <FlatList
        data={orders}
        keyExtractor={(i) => i.id}
        refreshing={loading}
        onRefresh={load}
        contentContainerStyle={{ padding: 16 }}
        ListEmptyComponent={<Text style={s.empty}>{emptyLabel}</Text>}
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
    </GradientScreen>
  );
}

const s = StyleSheet.create({
  filterWrap: { borderBottomWidth: 1, borderBottomColor: C.border, backgroundColor: 'transparent' },
  filterContent: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 10, gap: 8 },
  filterChip: {
    minHeight: 34,
    borderRadius: 17,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surfaceAlt,
    paddingHorizontal: 13,
    alignItems: 'center',
    justifyContent: 'center',
  },
  filterChipActive: { borderColor: C.accentLight, backgroundColor: C.accentSoft },
  filterText: { color: C.muted, fontSize: 12, fontWeight: '700' },
  filterTextActive: { color: C.accent },
  empty: { textAlign: 'center', color: C.muted, marginTop: 60 },
  card: { backgroundColor: C.card, borderRadius: 24, padding: 16, marginBottom: 10, borderWidth: 1, borderColor: C.borderStrong },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, gap: 10 },
  orderId: { fontFamily: 'monospace', color: C.accent, fontSize: 13 },
  badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
  storeName: { color: C.text, fontWeight: '600' },
  metaRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
});
