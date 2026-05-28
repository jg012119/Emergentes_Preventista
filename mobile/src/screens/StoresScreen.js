import React, { useCallback, useState } from 'react';
import { Alert, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { deleteStore, getStores } from '../services/api';
import { colors as C } from '../theme';
import { GradientScreen } from '../components/ScreenBackground';

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

  const goEditStore = (store) => {
    const parent = navigation.getParent?.();
    if (parent) {
      parent.navigate('CreateStore', { store });
      return;
    }
    navigation.navigate('CreateStore', { store });
  };

  const handleDelete = (id, name) => {
    Alert.alert('Eliminar sucursal', `Eliminar "${name}"?`, [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Eliminar', style: 'destructive', onPress: () => deleteStore(id).then(load).catch((e) => Alert.alert('Error', e.message)) },
    ]);
  };

  return (
    <GradientScreen style={s.container}>
      <TouchableOpacity style={s.addBtn} onPress={goCreateStore}>
        <Ionicons name="add-circle-outline" size={20} color={C.white} />
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
            <View style={s.actions}>
              <TouchableOpacity onPress={() => goEditStore(item)} style={s.actionBtn}>
                <Ionicons name="create-outline" size={20} color={C.accent} />
              </TouchableOpacity>
              <TouchableOpacity onPress={() => handleDelete(item.id, item.name)} style={s.actionBtn}>
                <Ionicons name="trash-outline" size={20} color={C.danger} />
              </TouchableOpacity>
            </View>
          </View>
        )}
      />
    </GradientScreen>
  );
}

const s = StyleSheet.create({
  container: { padding: 16 },
  addBtn: {
    backgroundColor: C.accent,
    borderRadius: 22,
    minHeight: 46,
    marginBottom: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  addBtnText: { color: C.white, textAlign: 'center', fontWeight: '800', fontSize: 15 },
  list: { paddingBottom: 16 },
  emptyList: { flexGrow: 1, justifyContent: 'center' },
  card: {
    backgroundColor: C.card,
    borderRadius: 24,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: C.borderStrong,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconBox: {
    width: 42,
    height: 42,
    borderRadius: 18,
    backgroundColor: C.accentSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardBody: { flex: 1 },
  name: { fontSize: 16, fontWeight: '800', color: C.text },
  line: { flexDirection: 'row', alignItems: 'center', marginTop: 4, gap: 4 },
  detail: { flex: 1, fontSize: 13, color: C.muted },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  actionBtn: { padding: 8 },
  empty: { textAlign: 'center', color: C.muted, fontSize: 14 },
});
