import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { getProducts } from '../services/api';

const C = { bg: '#0f1117', card: '#1a1d29', accent: '#6366f1', accentLight: '#818cf8', text: '#f0f2f5', muted: '#8b92a5', border: '#2a2f45', success: '#22c55e', danger: '#ef4444' };

export default function CatalogScreen({ navigation }) {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => { getProducts().then(setProducts).catch(() => {}).finally(() => setLoading(false)); }, []);

  const add = (p) => setCart(prev => ({ ...prev, [p.id]: { ...p, qty: (prev[p.id]?.qty || 0) + 1 } }));
  const remove = (id) => setCart(prev => {
    const n = { ...prev };
    if (n[id]?.qty > 1) n[id] = { ...n[id], qty: n[id].qty - 1 }; else delete n[id];
    return n;
  });

  const items = Object.values(cart);
  const total = items.reduce((s, i) => s + i.price * i.qty, 0);

  return (
    <View style={s.c}>
      <FlatList data={products} keyExtractor={i => i.id} refreshing={loading}
        onRefresh={() => { setLoading(true); getProducts().then(setProducts).finally(() => setLoading(false)); }}
        renderItem={({ item }) => {
          const q = cart[item.id]?.qty || 0;
          return (
            <View style={s.card}>
              <View style={{ flex: 1 }}>
                <Text style={s.name}>{item.name}</Text>
                <Text style={{ fontSize: 12, color: C.accentLight }}>{item.category}</Text>
                <Text style={{ fontSize: 16, fontWeight: '800', color: C.text, marginTop: 4 }}>Bs {Number(item.price).toFixed(2)}</Text>
                <Text style={{ fontSize: 12, color: item.stock < 10 ? C.danger : C.success }}>Stock: {item.stock}</Text>
              </View>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                {q > 0 && <TouchableOpacity style={s.qb} onPress={() => remove(item.id)}><Text style={s.qt}>−</Text></TouchableOpacity>}
                {q > 0 && <Text style={{ color: C.text, fontSize: 18, fontWeight: '700' }}>{q}</Text>}
                <TouchableOpacity style={[s.qb, { backgroundColor: C.accent }]} onPress={() => add(item)}><Text style={s.qt}>+</Text></TouchableOpacity>
              </View>
            </View>
          );
        }}
      />
      {items.length > 0 && (
        <View style={s.footer}>
          <Text style={{ color: C.text, fontWeight: '700', fontSize: 16 }}>{items.length} item(s) — Bs {total.toFixed(2)}</Text>
          <TouchableOpacity style={s.go} onPress={() => navigation.navigate('CreateOrder', { cart: items })}>
            <Text style={{ color: '#fff', fontWeight: '700' }}>Continuar →</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  c: { flex: 1, backgroundColor: C.bg },
  card: { backgroundColor: C.card, marginHorizontal: 16, marginTop: 10, borderRadius: 12, padding: 16, borderWidth: 1, borderColor: C.border, flexDirection: 'row', alignItems: 'center' },
  name: { fontSize: 15, fontWeight: '700', color: C.text },
  qb: { width: 36, height: 36, borderRadius: 8, backgroundColor: C.border, justifyContent: 'center', alignItems: 'center' },
  qt: { color: '#fff', fontSize: 20, fontWeight: '700' },
  footer: { backgroundColor: C.card, borderTopWidth: 1, borderTopColor: C.border, padding: 16, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  go: { backgroundColor: C.accent, borderRadius: 10, paddingVertical: 12, paddingHorizontal: 24 },
});
