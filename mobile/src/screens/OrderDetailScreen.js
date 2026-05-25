import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { getOrder } from '../services/api';
import { Ionicons } from '@expo/vector-icons';

const C = { bg: '#0f1117', card: '#1a1d29', accent: '#6366f1', text: '#f0f2f5', muted: '#8b92a5', border: '#2a2f45' };
const BADGE = { pendiente: '#f59e0b', confirmado: '#22c55e', rechazado: '#ef4444', en_proceso: '#3b82f6', borrador: '#818cf8' };

export default function OrderDetailScreen({ route, navigation }) {
  const { orderId } = route.params;
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { getOrder(orderId).then(setOrder).catch(() => navigation.goBack()).finally(() => setLoading(false)); }, [orderId]);

  if (loading || !order) return <View style={{ flex: 1, backgroundColor: C.bg, justifyContent: 'center' }}><Text style={{ color: C.muted, textAlign: 'center' }}>Cargando...</Text></View>;

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ padding: 20 }}>
      <View style={s.card}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Text style={s.title}>Pedido #{order.id.slice(0, 8)}</Text>
          <View style={[s.badge, { backgroundColor: (BADGE[order.status] || C.accent) + '22' }]}>
            <Text style={{ color: BADGE[order.status], fontWeight: '600' }}>{order.status}</Text>
          </View>
        </View>

        <View style={s.row}><Text style={s.lbl}>Tienda</Text><Text style={s.val}>{order.store_name}</Text></View>
        <View style={s.row}><Text style={s.lbl}>Entrega</Text><Text style={s.val}>{order.delivery_date || '—'}</Text></View>
        <View style={s.row}><Text style={s.lbl}>Creado</Text><Text style={s.val}>{order.created_at ? new Date(order.created_at).toLocaleString('es-BO') : '—'}</Text></View>
        {order.notes && <View style={s.row}><Text style={s.lbl}>Notas</Text><Text style={s.val}>{order.notes}</Text></View>}
      </View>

      <View style={[s.card, { marginTop: 16 }]}>
        <Text style={{ color: C.muted, fontSize: 12, fontWeight: '600', textTransform: 'uppercase', marginBottom: 12 }}>Productos</Text>
        {order.items?.map((item, i) => (
          <View key={item.id} style={s.item}>
            <Text style={{ color: C.text, flex: 1 }}>{i + 1}. {item.product_name}</Text>
            <Text style={{ color: C.muted, fontSize: 13 }}>x{item.quantity}</Text>
            <Text style={{ color: C.text, fontWeight: '700', width: 70, textAlign: 'right' }}>Bs {Number(item.subtotal).toFixed(2)}</Text>
          </View>
        ))}
        <View style={{ borderTopWidth: 1, borderTopColor: C.border, marginTop: 8, paddingTop: 12, flexDirection: 'row', justifyContent: 'space-between' }}>
          <Text style={{ color: C.text, fontWeight: '800', fontSize: 16 }}>TOTAL</Text>
          <Text style={{ color: C.accent, fontWeight: '800', fontSize: 18 }}>Bs {Number(order.total).toFixed(2)}</Text>
        </View>
      </View>

      <TouchableOpacity style={s.chatBtn} onPress={() => navigation.navigate('OrderChat', { orderId: order.id })}>
        <View style={{ flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 }}>
          <Ionicons name="chatbubble-ellipses-outline" size={20} color="#fff" />
          <Text style={{ color: '#fff', fontWeight: '700', textAlign: 'center' }}>Ver Chat del Pedido</Text>
        </View>
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.card, borderRadius: 14, padding: 20, borderWidth: 1, borderColor: C.border },
  title: { fontSize: 18, fontWeight: '700', color: C.text },
  badge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  lbl: { color: C.muted },
  val: { color: C.text, fontWeight: '500' },
  item: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: C.border },
  chatBtn: { backgroundColor: C.accent, borderRadius: 12, padding: 16, marginTop: 20, marginBottom: 40 },
});
