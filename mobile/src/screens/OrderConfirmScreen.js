import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { confirmOrder, sendMessage } from '../services/api';
import { Ionicons } from '@expo/vector-icons';
import { colors as C } from '../theme';
import { GradientScrollView } from '../components/ScreenBackground';

const ACTIVE_DRAFT_ORDER_KEY = 'preventista.activeDraftOrderId';
const PENDING_ORDER_TEXT_KEY = 'preventista.pendingOrderText';

export default function OrderConfirmScreen({ route, navigation }) {
  const { order, returnToChat = false, sourceChatOrderId = null } = route.params;
  const [loading, setLoading] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      const confirmed = await confirmOrder(order.id);
      await AsyncStorage.multiRemove([ACTIVE_DRAFT_ORDER_KEY, PENDING_ORDER_TEXT_KEY]);
      if (returnToChat) {
        await sendMessage({
          order_id: sourceChatOrderId,
          message: `Pedido #${confirmed.id.slice(0, 8)} confirmado y enviado a AJE. Puedes verlo en la lista de pedidos.`,
          sender: 'system',
        });
      }
      Alert.alert('Pedido confirmado', 'Tu pedido fue enviado a AJE. Te notificaremos cuando lo revisen.', [
        { text: 'OK', onPress: () => navigation.navigate('Main', returnToChat ? { screen: 'Chat' } : undefined) },
      ]);
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GradientScrollView contentContainerStyle={{ padding: 20 }}>
      <View style={s.card}>
        <View style={s.titleRow}>
          <Ionicons name="receipt-outline" size={22} color={C.accent} />
          <Text style={s.title}>Extracto del Pedido</Text>
        </View>
        <View style={s.row}><Text style={s.lbl}>Sucursal</Text><Text style={s.val}>{order.store_name}</Text></View>
        <View style={s.row}><Text style={s.lbl}>Entrega</Text><Text style={s.val}>{order.delivery_date}</Text></View>
        <View style={s.row}><Text style={s.lbl}>Estado</Text><Text style={[s.val, { color: C.warning }]}>{order.status}</Text></View>

        <Text style={[s.section, { marginTop: 20 }]}>Productos</Text>
        {order.items?.map((item, i) => (
          <View key={item.id} style={s.item}>
            <Text style={{ color: C.text, flex: 1 }}>{i + 1}. {item.product_name}</Text>
            <Text style={{ color: C.muted }}>x{item.quantity} - Bs {Number(item.unit_price).toFixed(2)}</Text>
            <Text style={{ color: C.text, fontWeight: '700', width: 70, textAlign: 'right' }}>Bs {Number(item.subtotal).toFixed(2)}</Text>
          </View>
        ))}

        <View style={s.totalRow}>
          <Text style={s.totalLabel}>TOTAL</Text>
          <Text style={s.totalValue}>Bs {Number(order.total).toFixed(2)}</Text>
        </View>
      </View>

      <Text style={s.helper}>Los datos son correctos? Confirma para enviar tu pedido a AJE.</Text>

      <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={handleConfirm} disabled={loading}>
        <View style={s.btnRow}>
          {!loading && <Ionicons name="checkmark-circle-outline" size={20} color={C.white} />}
          <Text style={s.btnText}>{loading ? 'Confirmando...' : 'Confirmar Pedido'}</Text>
        </View>
      </TouchableOpacity>

      <TouchableOpacity style={s.cancelBtn} onPress={() => navigation.goBack()}>
        <View style={s.btnRow}>
          <Ionicons name="arrow-back-outline" size={16} color={C.muted} />
          <Text style={{ color: C.muted, textAlign: 'center' }}>Volver a editar</Text>
        </View>
      </TouchableOpacity>

      <TouchableOpacity
        style={s.saveExitBtn}
        onPress={() => {
          Alert.alert('Borrador guardado', 'Tus cambios fueron guardados como borrador. Podrás enviarlo más tarde.', [
            { text: 'OK', onPress: () => navigation.navigate('Main', { screen: 'Pedidos' }) }
          ]);
        }}
      >
        <Text style={s.saveExitText}>Guardar borrador y salir</Text>
      </TouchableOpacity>
    </GradientScrollView>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.card, borderRadius: 24, padding: 20, borderWidth: 1, borderColor: C.borderStrong },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 16 },
  title: { fontSize: 20, fontWeight: '700', color: C.text },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, gap: 12 },
  lbl: { color: C.muted, fontSize: 14 },
  val: { color: C.text, fontWeight: '600', fontSize: 14, flexShrink: 1, textAlign: 'right' },
  section: { fontSize: 13, fontWeight: '600', color: C.muted, textTransform: 'uppercase', marginBottom: 8 },
  item: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: C.border, gap: 8 },
  totalRow: { marginTop: 16, borderTopWidth: 1, borderTopColor: C.border, paddingTop: 12, flexDirection: 'row', justifyContent: 'space-between' },
  totalLabel: { color: C.text, fontWeight: '800', fontSize: 18 },
  totalValue: { color: C.accent, fontWeight: '800', fontSize: 20 },
  helper: { color: C.muted, textAlign: 'center', marginTop: 20, fontSize: 13 },
  btn: { backgroundColor: C.accent, borderRadius: 18, padding: 16, marginTop: 24 },
  btnRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  btnText: { color: C.white, textAlign: 'center', fontWeight: '700', fontSize: 17 },
  cancelBtn: { marginTop: 16, padding: 12 },
  saveExitBtn: { marginTop: 8, padding: 12, alignItems: 'center', marginBottom: 40 },
  saveExitText: { color: C.accentLight, fontWeight: '600', fontSize: 14, textDecorationLine: 'underline' },
});
