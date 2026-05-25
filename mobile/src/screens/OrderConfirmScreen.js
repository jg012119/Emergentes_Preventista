import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { confirmOrder } from '../services/api';
import { Ionicons } from '@expo/vector-icons';

const C = { bg: '#0f1117', card: '#1a1d29', accent: '#6366f1', text: '#f0f2f5', muted: '#8b92a5', border: '#2a2f45', success: '#22c55e' };

export default function OrderConfirmScreen({ route, navigation }) {
  const { order } = route.params;
  const [loading, setLoading] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await confirmOrder(order.id);
      Alert.alert('Pedido confirmado', 'Tu pedido fue enviado a AJE. Te notificaremos cuando lo revisen.', [
        { text: 'OK', onPress: () => navigation.navigate('Main') },
      ]);
    } catch (e) { Alert.alert('Error', e.message); }
    finally { setLoading(false); }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ padding: 20 }}>
      <View style={s.card}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <Ionicons name="receipt-outline" size={22} color={C.accent} />
          <Text style={{ fontSize: 20, fontWeight: '700', color: C.text }}>Extracto del Pedido</Text>
        </View>
        <View style={s.row}><Text style={s.lbl}>Tienda</Text><Text style={s.val}>{order.store_name}</Text></View>
        <View style={s.row}><Text style={s.lbl}>Entrega</Text><Text style={s.val}>{order.delivery_date}</Text></View>
        <View style={s.row}><Text style={s.lbl}>Estado</Text><Text style={[s.val, { color: '#f59e0b' }]}>{order.status}</Text></View>

        <Text style={[s.section, { marginTop: 20 }]}>Productos</Text>
        {order.items?.map((item, i) => (
          <View key={item.id} style={s.item}>
            <Text style={{ color: C.text, flex: 1 }}>{i + 1}. {item.product_name}</Text>
            <Text style={{ color: C.muted }}>x{item.quantity} · Bs {Number(item.unit_price).toFixed(2)}</Text>
            <Text style={{ color: C.text, fontWeight: '700', width: 70, textAlign: 'right' }}>Bs {Number(item.subtotal).toFixed(2)}</Text>
          </View>
        ))}

        <View style={[s.row, { marginTop: 16, borderTopWidth: 1, borderTopColor: C.border, paddingTop: 12 }]}>
          <Text style={{ color: C.text, fontWeight: '800', fontSize: 18 }}>TOTAL</Text>
          <Text style={{ color: C.accent, fontWeight: '800', fontSize: 20 }}>Bs {Number(order.total).toFixed(2)}</Text>
        </View>
      </View>

      <Text style={{ color: C.muted, textAlign: 'center', marginTop: 20, fontSize: 13 }}>
        ¿Los datos son correctos? Confirma para enviar tu pedido a AJE.
      </Text>

      <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={handleConfirm} disabled={loading}>
        <View style={{ flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 }}>
          {!loading && <Ionicons name="checkmark-circle-outline" size={20} color="#fff" />}
          <Text style={s.btnText}>{loading ? 'Confirmando...' : 'Confirmar Pedido'}</Text>
        </View>
      </TouchableOpacity>

      <TouchableOpacity style={s.cancelBtn} onPress={() => navigation.goBack()}>
        <View style={{ flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 6 }}>
          <Ionicons name="arrow-back-outline" size={16} color={C.muted} />
          <Text style={{ color: C.muted, textAlign: 'center' }}>Volver a editar</Text>
        </View>
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.card, borderRadius: 14, padding: 20, borderWidth: 1, borderColor: C.border },
  title: { fontSize: 20, fontWeight: '700', color: C.text, marginBottom: 16 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6 },
  lbl: { color: C.muted, fontSize: 14 },
  val: { color: C.text, fontWeight: '600', fontSize: 14 },
  section: { fontSize: 13, fontWeight: '600', color: C.muted, textTransform: 'uppercase', marginBottom: 8 },
  item: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: C.border },
  btn: { backgroundColor: C.success, borderRadius: 12, padding: 16, marginTop: 24 },
  btnText: { color: '#fff', textAlign: 'center', fontWeight: '700', fontSize: 17 },
  cancelBtn: { marginTop: 16, padding: 12, marginBottom: 40 },
});
