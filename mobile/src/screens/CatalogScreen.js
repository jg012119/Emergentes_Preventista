import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { getProducts } from '../services/api';
import { colors as C } from '../theme';
import { GradientScreen } from '../components/ScreenBackground';

export default function CatalogScreen({ route, navigation }) {
  const sendToChat = Boolean(route?.params?.sendToChat);
  const orderId = route?.params?.orderId ?? null;
  const isEditingOrderId = route?.params?.isEditingOrderId ?? null;
  const initialCart = route?.params?.initialCart ?? null;

  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState(() => {
    const init = {};
    if (initialCart && Array.isArray(initialCart)) {
      initialCart.forEach((item) => {
        const pid = item.product_id;
        init[pid] = {
          id: pid,
          name: item.product_name || 'Producto',
          price: Number(item.unit_price || 0),
          qty: Number(item.quantity || 1),
          stock: 999, // default safety, stock will be overwritten by product list
        };
      });
    }
    return init;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProducts().then(setProducts).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const add = (product) => {
    setCart((prev) => ({
      ...prev,
      [product.id]: { ...product, qty: (prev[product.id]?.qty || 0) + 1 },
    }));
  };

  const remove = (id) => {
    setCart((prev) => {
      const next = { ...prev };
      if (next[id]?.qty > 1) {
        next[id] = { ...next[id], qty: next[id].qty - 1 };
      } else {
        delete next[id];
      }
      return next;
    });
  };

  const items = Object.values(cart);
  const total = items.reduce((sum, item) => sum + item.price * item.qty, 0);

  const goNext = () => {
    navigation.navigate('CreateOrder', { cart: items, sendToChat, orderId, isEditingOrderId });
  };

  return (
    <GradientScreen style={s.c}>
      <FlatList
        data={products}
        keyExtractor={(item) => item.id}
        refreshing={loading}
        onRefresh={() => {
          setLoading(true);
          getProducts().then(setProducts).finally(() => setLoading(false));
        }}
        renderItem={({ item }) => {
          const quantity = cart[item.id]?.qty || 0;
          return (
            <View style={s.card}>
              <View style={{ flex: 1 }}>
                <Text style={s.name}>{item.name}</Text>
                <Text style={{ fontSize: 12, color: C.accentLight }}>{item.category}</Text>
                <Text style={{ fontSize: 16, fontWeight: '800', color: C.text, marginTop: 4 }}>
                  Bs {Number(item.price).toFixed(2)}
                </Text>
                <Text style={{ fontSize: 12, color: item.stock < 10 ? C.danger : C.success }}>
                  Stock: {item.stock}
                </Text>
              </View>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                {quantity > 0 ? (
                  <TouchableOpacity style={s.qb} onPress={() => remove(item.id)}>
                    <Text style={s.qt}>-</Text>
                  </TouchableOpacity>
                ) : null}
                {quantity > 0 ? (
                  <Text style={{ color: C.text, fontSize: 18, fontWeight: '700' }}>{quantity}</Text>
                ) : null}
                <TouchableOpacity style={[s.qb, { backgroundColor: C.accent }]} onPress={() => add(item)}>
                  <Text style={s.qt}>+</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        }}
      />
      {items.length > 0 ? (
        <View style={s.footer}>
          <Text style={{ color: C.text, fontWeight: '700', fontSize: 16 }}>
            {items.length} item(s) - Bs {total.toFixed(2)}
          </Text>
          <TouchableOpacity style={s.go} onPress={goNext}>
            <Text style={{ color: C.white, fontWeight: '700' }}>
              {sendToChat ? 'Crear pedido' : 'Continuar'}
            </Text>
          </TouchableOpacity>
        </View>
      ) : null}
    </GradientScreen>
  );
}

const s = StyleSheet.create({
  c: {},
  card: {
    backgroundColor: C.card,
    marginHorizontal: 16,
    marginTop: 10,
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: C.borderStrong,
    flexDirection: 'row',
    alignItems: 'center',
  },
  name: { fontSize: 15, fontWeight: '700', color: C.text },
  qb: {
    width: 36,
    height: 36,
    borderRadius: 14,
    backgroundColor: C.surfaceAlt,
    borderWidth: 1,
    borderColor: C.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  qt: { color: C.white, fontSize: 20, fontWeight: '700' },
  footer: {
    backgroundColor: C.panel,
    borderTopWidth: 1,
    borderTopColor: C.border,
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  go: { backgroundColor: C.accent, borderRadius: 18, paddingVertical: 12, paddingHorizontal: 24 },
});
