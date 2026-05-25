import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { getStores, createDraft } from '../services/api';
import DateTimePicker from '@react-native-community/datetimepicker';

const C = { bg: '#0f1117', card: '#1a1d29', accent: '#6366f1', text: '#f0f2f5', muted: '#8b92a5', border: '#2a2f45', success: '#22c55e' };

export default function CreateOrderScreen({ route, navigation }) {
  const { cart } = route.params;
  const [stores, setStores] = useState([]);
  const [selectedStore, setSelectedStore] = useState(null);
  const [deliveryDate, setDeliveryDate] = useState(new Date(Date.now() + 86400000));
  const [loading, setLoading] = useState(false);

  useEffect(() => { getStores().then(s => { setStores(s); if (s.length) setSelectedStore(s[0].id); }); }, []);

  const total = cart.reduce((s, i) => s + i.price * i.qty, 0);

  const handleCreate = async () => {
    if (!selectedStore) { Alert.alert('Error', 'Selecciona una tienda'); return; }
    setLoading(true);
    try {
      const order = await createDraft({
        store_id: selectedStore,
        delivery_date: deliveryDate.toISOString().split('T')[0],
        items: cart.map(i => ({ product_id: i.id, quantity: i.qty })),
      });
      navigation.navigate('OrderConfirm', { order });
    } catch (e) { Alert.alert('Error', e.message); }
    finally { setLoading(false); }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ padding: 20 }}>
      <View style={s.card}>
        <Text style={s.title}>Resumen del pedido</Text>
        {cart.map(i => (
          <View key={i.id} style={s.row}>
            <Text style={{ color: C.text, flex: 1 }}>{i.name}</Text>
            <Text style={{ color: C.muted }}>x{i.qty}</Text>
            <Text style={{ color: C.text, fontWeight: '700', width: 80, textAlign: 'right' }}>Bs {(i.price * i.qty).toFixed(2)}</Text>
          </View>
        ))}
        <View style={[s.row, { borderTopWidth: 1, borderTopColor: C.border, marginTop: 8, paddingTop: 12 }]}>
          <Text style={{ color: C.text, fontWeight: '800', fontSize: 16 }}>TOTAL</Text>
          <Text style={{ color: C.accent, fontWeight: '800', fontSize: 18 }}>Bs {total.toFixed(2)}</Text>
        </View>
      </View>

      <View style={[s.card, { marginTop: 16 }]}>
        <Text style={s.label}>Tienda</Text>
        {stores.map(st => (
          <TouchableOpacity key={st.id} style={[s.storeBtn, selectedStore === st.id && s.storeBtnActive]} onPress={() => setSelectedStore(st.id)}>
            <Text style={{ color: selectedStore === st.id ? '#fff' : C.text }}>{st.name}</Text>
            <Text style={{ color: selectedStore === st.id ? 'rgba(255,255,255,0.7)' : C.muted, fontSize: 12 }}>{st.address}</Text>
          </TouchableOpacity>
        ))}
        {stores.length === 0 && (
          <TouchableOpacity onPress={() => navigation.navigate('CreateStore')}>
            <Text style={{ color: C.accent, marginTop: 8 }}>+ Registrar una tienda primero</Text>
          </TouchableOpacity>
        )}

        <Text style={[s.label, { marginTop: 16 }]}>Fecha de entrega</Text>
        <Text style={{ color: C.text, fontSize: 16, marginTop: 4 }}>{deliveryDate.toLocaleDateString('es-BO')}</Text>
      </View>

      <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={handleCreate} disabled={loading}>
        <Text style={s.btnText}>{loading ? 'Creando...' : 'Crear Pedido Borrador'}</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.card, borderRadius: 14, padding: 20, borderWidth: 1, borderColor: C.border },
  title: { fontSize: 18, fontWeight: '700', color: C.text, marginBottom: 16 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8 },
  label: { fontSize: 13, fontWeight: '600', color: C.muted, marginBottom: 8 },
  storeBtn: { backgroundColor: '#181b27', borderRadius: 10, padding: 12, marginBottom: 8, borderWidth: 1, borderColor: C.border },
  storeBtnActive: { backgroundColor: C.accent, borderColor: C.accent },
  btn: { backgroundColor: C.accent, borderRadius: 12, padding: 16, marginTop: 24, marginBottom: 40 },
  btnText: { color: '#fff', textAlign: 'center', fontWeight: '700', fontSize: 16 },
});
