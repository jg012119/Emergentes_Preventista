import React, { useCallback, useState } from 'react';
import { Alert, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { deleteStore, getStores } from '../services/api';

const C = {
  bg: '#0b141a',
  card: '#17232b',
  accent: '#25d366',
  text: '#eef6f7',
  muted: '#8fa4ad',
  border: '#2a3942',
  danger: '#ef4444',
};

export default function StoresScreen({ navigation }) {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    getStores().then(setStores).catch(() => {}).finally(() => setLoading(false));
  };

  useFocusEffect(useCallback(() => { load(); }, []));

  const goCreateStore = () => {
    const parent = navigation.getParent?.();
    if (parent) {
      parent.navigate('CreateStore');
      return;
    }
    navigation.navigate('CreateStore');
  };

  const handleDelete = (id, name) => {
    Alert.alert('Eliminar sucursal', `Eliminar "${name}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Eliminar', style: 'destructive', onPress: () => deleteStore(id).then(load).catch((e) => Alert.alert('Error', e.message)) },
    ]);
  };

  return (
    <View style={s.container}>
      <TouchableOpacity style={s.addBtn} onPress={goCreateStore}>
        <Ionicons name="add-circle-outline" size={20} color="#0b141a" />
        <Text style={s.addBtnText}>Nueva Sucursal</Text>
      </TouchableOpacity>

      <FlatList
        data={stores}
        keyExtractor={(i) => String(i.id)}
        refreshing={loading}
        onRefresh={load}
        contentContainerStyle={stores.length ? s.list : s.emptyList}
        ListEmptyComponent={<Text style={s.empty}>No tienes sucursales registradas</Text>}
        renderItem={({ item }) => (
          <View style={s.card}>
            <View style={s.iconBox}>
              <Ionicons name="storefront-outline" size={22} color={C.accent} />
            </View>
            <View style={s.cardBody}>
              <Text style={s.name}>{item.name}</Text>
              <View style={s.line}>
                <Ionicons name="location-outline" size={14} color={C.muted} />
                <Text style={s.detail} numberOfLines={2}>{item.address}</Text>
              </View>
              {item.phone ? (
                <View style={s.line}>
                  <Ionicons name="call-outline" size={14} color={C.muted} />
                  <Text style={s.detail}>{item.phone}</Text>
                </View>
              ) : null}
            </View>
            <TouchableOpacity onPress={() => handleDelete(item.id, item.name)} style={s.deleteBtn}>
              <Ionicons name="trash-outline" size={20} color={C.danger} />
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg, padding: 16 },
  addBtn: {
    backgroundColor: C.accent,
    borderRadius: 24,
    minHeight: 46,
    marginBottom: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  addBtnText: { color: '#0b141a', textAlign: 'center', fontWeight: '800', fontSize: 15 },
  list: { paddingBottom: 16 },
  emptyList: { flexGrow: 1, justifyContent: 'center' },
  card: {
    backgroundColor: C.card,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: C.border,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconBox: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: '#10261d',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardBody: { flex: 1 },
  name: { fontSize: 16, fontWeight: '800', color: C.text },
  line: { flexDirection: 'row', alignItems: 'center', marginTop: 4, gap: 4 },
  detail: { flex: 1, fontSize: 13, color: C.muted },
  deleteBtn: { padding: 8 },
  empty: { textAlign: 'center', color: C.muted, fontSize: 14 },
});
