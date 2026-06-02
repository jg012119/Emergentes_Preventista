import React, { useCallback, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { getStores, createDraft, updateDraft, sendMessage } from '../services/api';
import { Ionicons } from '@expo/vector-icons';
import { colors as C } from '../theme';

export default function CreateOrderScreen({ route, navigation }) {
  const { cart, sendToChat = false, orderId = null, isEditingOrderId = null } = route.params;
  const [stores, setStores] = useState([]);
  const [selectedStore, setSelectedStore] = useState(null);
  const [deliveryDate] = useState(new Date(Date.now() + 86400000));
  const [loading, setLoading] = useState(false);

  // Re-fetch stores every time this screen gets focus
  // (covers: created a new store and navigated back)
  useFocusEffect(
    useCallback(() => {
      getStores().then((items) => {
        setStores(items);
        // Auto-select first store if nothing is selected yet or the
        // previously-selected store was deleted
        setSelectedStore((prev) => {
          if (!prev || !items.find((s) => s.id === prev)) {
            return items.length ? items[0].id : null;
          }
          return prev;
        });
      }).catch(() => {});
    }, [])
  );

  const total = cart.reduce((sum, item) => sum + item.price * item.qty, 0);

  const buildChatRequest = (store) => {
    const lines = cart.map((item) => `- ${item.qty} x ${item.name}: Bs ${(item.price * item.qty).toFixed(2)}`);
    return [
      'Pedido estructurado desde catalogo:',
      `Sucursal: ${store?.name || 'Sin sucursal'}`,
      `Entrega: ${deliveryDate.toLocaleDateString('es-BO')}`,
      'Productos:',
      ...lines,
      `Total estimado: Bs ${total.toFixed(2)}`,
    ].join('\n');
  };

  const handleCreate = async () => {
    if (!selectedStore) {
      Alert.alert('Error', 'Selecciona una sucursal');
      return;
    }
    setLoading(true);
    try {
      const orderData = {
        store_id: selectedStore,
        delivery_date: deliveryDate.toISOString().split('T')[0],
        items: cart.map((item) => ({ product_id: item.id, quantity: item.qty })),
      };

      const order = isEditingOrderId
        ? await updateDraft(isEditingOrderId, orderData)
        : await createDraft(orderData);

      if (sendToChat) {
        const store = stores.find((item) => item.id === selectedStore);
        await sendMessage({
          order_id: orderId,
          message: buildChatRequest(store),
          sender: 'user',
        });
        await sendMessage({
          order_id: orderId,
          message: `Pedido estructurado entendido. Cree el borrador #${order.id.slice(0, 8)} con esos datos. Confirma para enviarlo a AJE.`,
          sender: 'system',
        });
      }

      navigation.navigate('OrderConfirm', {
        order,
        returnToChat: sendToChat,
        sourceChatOrderId: orderId,
      });
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ padding: 20 }}>
      <View style={s.card}>
        <Text style={s.title}>{sendToChat ? 'Crear pedido desde chat' : 'Resumen del pedido'}</Text>
        {cart.map((item) => (
          <View key={item.id} style={s.row}>
            <Text style={{ color: C.text, flex: 1 }}>{item.name}</Text>
            <Text style={{ color: C.muted }}>x{item.qty}</Text>
            <Text style={{ color: C.text, fontWeight: '700', width: 80, textAlign: 'right' }}>Bs {(item.price * item.qty).toFixed(2)}</Text>
          </View>
        ))}
        <View style={s.totalRow}>
          <Text style={{ color: C.text, fontWeight: '800', fontSize: 16 }}>TOTAL</Text>
          <Text style={{ color: C.accent, fontWeight: '800', fontSize: 18 }}>Bs {total.toFixed(2)}</Text>
        </View>
      </View>

      <View style={[s.card, { marginTop: 16 }]}>
        <Text style={s.label}>Sucursal</Text>
        {stores.map((store) => (
          <TouchableOpacity
            key={store.id}
            style={[s.storeBtn, selectedStore === store.id && s.storeBtnActive]}
            onPress={() => setSelectedStore(store.id)}
          >
            <Text style={{ color: selectedStore === store.id ? C.white : C.text }}>{store.name}</Text>
            <Text style={{ color: selectedStore === store.id ? C.whiteSoft : C.muted, fontSize: 12 }}>{store.address}</Text>
          </TouchableOpacity>
        ))}
        {stores.length === 0 ? (
          <TouchableOpacity style={s.addStoreBtn} onPress={() => navigation.navigate('CreateStore')}>
            <Ionicons name="add-circle-outline" size={18} color={C.accent} />
            <Text style={s.addStoreBtnText}>Registrar una sucursal primero</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={s.addStoreLinkRow} onPress={() => navigation.navigate('CreateStore')}>
            <Ionicons name="add-outline" size={15} color={C.muted} />
            <Text style={s.addStoreLinkText}>Añadir otra sucursal</Text>
          </TouchableOpacity>
        )}

        <Text style={[s.label, { marginTop: 16 }]}>Fecha de entrega</Text>
        <Text style={{ color: C.text, fontSize: 16, marginTop: 4 }}>{deliveryDate.toLocaleDateString('es-BO')}</Text>
      </View>

      <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={handleCreate} disabled={loading}>
        <Text style={s.btnText}>
          {loading ? 'Guardando...' : sendToChat ? 'Crear Pedido y Confirmar' : isEditingOrderId ? 'Guardar Cambios' : 'Crear Pedido Borrador'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.card, borderRadius: 14, padding: 20, borderWidth: 1, borderColor: C.border },
  title: { fontSize: 18, fontWeight: '700', color: C.text, marginBottom: 16 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8, gap: 8 },
  totalRow: { borderTopWidth: 1, borderTopColor: C.border, marginTop: 8, paddingTop: 12, flexDirection: 'row', justifyContent: 'space-between' },
  label: { fontSize: 13, fontWeight: '600', color: C.muted, marginBottom: 8 },
  storeBtn: { backgroundColor: C.input, borderRadius: 10, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: C.border },
  storeBtnActive: { backgroundColor: C.accentDark, borderColor: C.accent },
  addStoreBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    backgroundColor: C.accentSoft, borderRadius: 10, padding: 14,
    borderWidth: 1, borderColor: C.accent, marginTop: 4,
  },
  addStoreBtnText: { color: C.accent, fontWeight: '600', fontSize: 14 },
  addStoreLinkRow: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 6 },
  addStoreLinkText: { color: C.muted, fontSize: 12 },
  btn: { backgroundColor: C.accent, borderRadius: 12, padding: 16, marginTop: 24, marginBottom: 40 },
  btnText: { color: C.white, textAlign: 'center', fontWeight: '700', fontSize: 16 },
});
