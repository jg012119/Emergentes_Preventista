import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getOrder, confirmOrder } from '../services/api';
import { Ionicons } from '@expo/vector-icons';
import { colors as C, statusColors } from '../theme';
import { GradientScreen, GradientScrollView } from '../components/ScreenBackground';

const ACTIVE_DRAFT_ORDER_KEY = 'preventista.activeDraftOrderId';
const PENDING_ORDER_TEXT_KEY = 'preventista.pendingOrderText';

export default function OrderDetailScreen({ route, navigation }) {
  const { orderId } = route.params;
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    getOrder(orderId).then(setOrder).catch(() => navigation.goBack()).finally(() => setLoading(false));
  }, [orderId, navigation]);

  const handleConfirmOrder = () => {
    Alert.alert(
      'Confirmar pedido',
      '¿Confirmas que quieres enviar este pedido a AJE? Quedará en estado Pendiente.',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Enviar',
          style: 'default',
          onPress: async () => {
            setSubmitting(true);
            try {
              const confirmed = await confirmOrder(orderId);
              await AsyncStorage.multiRemove([ACTIVE_DRAFT_ORDER_KEY, PENDING_ORDER_TEXT_KEY]);
              setOrder(confirmed);
              Alert.alert('Pedido enviado', 'Tu pedido fue enviado correctamente a AJE.');
            } catch (e) {
              Alert.alert('Error', e?.message || 'No se pudo confirmar el pedido. Intenta de nuevo.');
            } finally {
              setSubmitting(false);
            }
          },
        },
      ]
    );
  };

  const handleEditOrder = () => {
    if (!order) return;
    navigation.navigate('Catalog', {
      initialCart: order.items,
      isEditingOrderId: order.id,
      sendToChat: false,
      orderId: null,
    });
  };

  if (loading || !order) {
    return (
      <GradientScreen style={s.loading}>
        <Text style={{ color: C.muted, textAlign: 'center' }}>Cargando...</Text>
      </GradientScreen>
    );
  }

  const badgeColor = statusColors[order.status] || C.accent;

  return (
    <GradientScrollView contentContainerStyle={{ padding: 20 }}>
      <View style={s.card}>
        <View style={s.headerRow}>
          <Text style={s.title}>Pedido #{order.id.slice(0, 8)}</Text>
          <View style={[s.badge, { backgroundColor: `${badgeColor}22` }]}>
            <Text style={{ color: badgeColor, fontWeight: '600' }}>{order.status}</Text>
          </View>
        </View>

        <View style={s.row}><Text style={s.lbl}>Sucursal</Text><Text style={s.val}>{order.store_name}</Text></View>
        <View style={s.row}><Text style={s.lbl}>Entrega</Text><Text style={s.val}>{order.delivery_date || '-'}</Text></View>
        <View style={s.row}><Text style={s.lbl}>Creado</Text><Text style={s.val}>{order.created_at ? new Date(order.created_at).toLocaleString('es-BO') : '-'}</Text></View>
        {order.notes ? <View style={s.row}><Text style={s.lbl}>Notas</Text><Text style={s.val}>{order.notes}</Text></View> : null}
      </View>

      <View style={[s.card, { marginTop: 16 }]}>
        <Text style={s.sectionTitle}>Productos</Text>
        {order.items?.map((item, i) => (
          <View key={item.id} style={s.item}>
            <Text style={{ color: C.text, flex: 1 }}>{i + 1}. {item.product_name}</Text>
            <Text style={{ color: C.muted, fontSize: 13 }}>x{item.quantity}</Text>
            <Text style={{ color: C.text, fontWeight: '700', width: 70, textAlign: 'right' }}>Bs {Number(item.subtotal).toFixed(2)}</Text>
          </View>
        ))}
        <View style={s.totalRow}>
          <Text style={{ color: C.text, fontWeight: '800', fontSize: 16 }}>TOTAL</Text>
          <Text style={{ color: C.accent, fontWeight: '800', fontSize: 18 }}>Bs {Number(order.total).toFixed(2)}</Text>
        </View>
      </View>

      {order.status === 'borrador' ? (
        <View style={s.borradorContainer}>
          <TouchableOpacity
            style={[s.btn, s.btnSuccess, submitting && { opacity: 0.6 }]}
            onPress={handleConfirmOrder}
            disabled={submitting}
            activeOpacity={0.82}
          >
            <View style={s.btnRow}>
              <Ionicons name="paper-plane-outline" size={20} color={C.white} />
              <Text style={s.btnText}>{submitting ? 'Enviando...' : 'Confirmar y Enviar Pedido'}</Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={[s.btn, s.btnOutline]}
            onPress={handleEditOrder}
            disabled={submitting}
            activeOpacity={0.82}
          >
            <View style={s.btnRow}>
              <Ionicons name="create-outline" size={20} color={C.accentLight} />
              <Text style={[s.btnText, s.btnTextOutline]}>Editar Pedido</Text>
            </View>
          </TouchableOpacity>
        </View>
      ) : null}

      <TouchableOpacity style={s.chatBtn} onPress={() => navigation.navigate('OrderChat', { orderId: order.id, orderStatus: order.status })}>
        <View style={s.chatRow}>
          <Ionicons name="chatbubble-ellipses-outline" size={20} color={C.white} />
          <Text style={{ color: C.white, fontWeight: '700', textAlign: 'center' }}>Ver Chat del Pedido</Text>
        </View>
      </TouchableOpacity>
    </GradientScrollView>
  );
}

const s = StyleSheet.create({
  loading: { justifyContent: 'center' },
  card: { backgroundColor: C.card, borderRadius: 24, padding: 20, borderWidth: 1, borderColor: C.borderStrong },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, gap: 10 },
  title: { fontSize: 18, fontWeight: '700', color: C.text, flexShrink: 1 },
  badge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, gap: 12 },
  lbl: { color: C.muted },
  val: { color: C.text, fontWeight: '500', flexShrink: 1, textAlign: 'right' },
  sectionTitle: { color: C.muted, fontSize: 12, fontWeight: '600', textTransform: 'uppercase', marginBottom: 12 },
  item: { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: C.border, gap: 8 },
  totalRow: { borderTopWidth: 1, borderTopColor: C.border, marginTop: 8, paddingTop: 12, flexDirection: 'row', justifyContent: 'space-between' },
  chatBtn: { backgroundColor: C.accent, borderRadius: 18, padding: 16, marginTop: 14, marginBottom: 40 },
  chatRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 8 },
  borradorContainer: {
    marginTop: 20,
    gap: 10,
  },
  btn: {
    borderRadius: 18,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnSuccess: {
    backgroundColor: '#10b981',
  },
  btnOutline: {
    backgroundColor: C.surfaceAlt,
    borderWidth: 1,
    borderColor: C.borderStrong,
  },
  btnRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  btnText: {
    color: C.white,
    fontWeight: '700',
    fontSize: 16,
  },
  btnTextOutline: {
    color: C.accentLight,
  },
});
