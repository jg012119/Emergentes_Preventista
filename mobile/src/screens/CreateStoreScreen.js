import React, { useEffect, useLayoutEffect, useMemo, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { createStore, updateStore } from '../services/api';
import { Ionicons } from '@expo/vector-icons';
import { colors as C } from '../theme';

export default function CreateStoreScreen({ route, navigation }) {
  const store = route?.params?.store ?? null;
  const isEditing = Boolean(store?.id);
  const initialValues = useMemo(() => ({
    name: store?.name ?? '',
    address: store?.address ?? '',
    phone: store?.phone ?? '',
    latitude: store?.latitude != null ? String(store.latitude) : '-17.3935',
    longitude: store?.longitude != null ? String(store.longitude) : '-66.157',
  }), [store]);

  const [name, setName] = useState(initialValues.name);
  const [address, setAddress] = useState(initialValues.address);
  const [phone, setPhone] = useState(initialValues.phone);
  const [latitude, setLatitude] = useState(initialValues.latitude);
  const [longitude, setLongitude] = useState(initialValues.longitude);
  const [loading, setLoading] = useState(false);

  useLayoutEffect(() => {
    navigation.setOptions({ title: isEditing ? 'Editar Sucursal' : 'Nueva Sucursal' });
  }, [isEditing, navigation]);

  useEffect(() => {
    setName(initialValues.name);
    setAddress(initialValues.address);
    setPhone(initialValues.phone);
    setLatitude(initialValues.latitude);
    setLongitude(initialValues.longitude);
  }, [initialValues]);

  const handleSave = async () => {
    const payload = {
      name: name.trim(),
      address: address.trim(),
      phone: phone.trim(),
      latitude: parseFloat(latitude) || -17.3935,
      longitude: parseFloat(longitude) || -66.157,
    };

    if (!payload.name || !payload.address) {
      Alert.alert('Error', 'Nombre y direccion son obligatorios');
      return;
    }

    setLoading(true);
    try {
      if (isEditing) {
        await updateStore(store.id, payload);
      } else {
        await createStore(payload);
      }
      navigation.goBack();
    } catch (e) {
      Alert.alert('Error', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ padding: 20 }}>
      <View style={s.card}>
        <View style={s.headerRow}>
          <Ionicons name={isEditing ? 'create-outline' : 'storefront-outline'} size={22} color={C.accent} />
          <Text style={s.title}>{isEditing ? 'Actualizar sucursal' : 'Registrar sucursal'}</Text>
        </View>

        <Text style={s.label}>Nombre de la sucursal *</Text>
        <TextInput style={s.input} value={name} onChangeText={setName} placeholder="Ej: Sucursal San Miguel" placeholderTextColor={C.muted} />

        <Text style={s.label}>Direccion *</Text>
        <TextInput style={s.input} value={address} onChangeText={setAddress} placeholder="Ej: Av. Blanco Galindo #1234" placeholderTextColor={C.muted} />

        <Text style={s.label}>Telefono</Text>
        <TextInput style={s.input} value={phone} onChangeText={setPhone} placeholder="77712345" placeholderTextColor={C.muted} keyboardType="phone-pad" />

        <View style={{ flexDirection: 'row', gap: 12 }}>
          <View style={{ flex: 1 }}>
            <Text style={s.label}>Latitud</Text>
            <TextInput style={s.input} value={latitude} onChangeText={setLatitude} placeholder="-17.3935" placeholderTextColor={C.muted} keyboardType="decimal-pad" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={s.label}>Longitud</Text>
            <TextInput style={s.input} value={longitude} onChangeText={setLongitude} placeholder="-66.157" placeholderTextColor={C.muted} keyboardType="decimal-pad" />
          </View>
        </View>

        <View style={s.infoRow}>
          <Ionicons name="information-circle-outline" size={16} color={C.accent} />
          <Text style={s.infoText}>En una version futura se podra seleccionar la ubicacion desde el mapa.</Text>
        </View>

        <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={handleSave} disabled={loading}>
          <Text style={s.btnText}>
            {loading ? 'Guardando...' : isEditing ? 'Actualizar Sucursal' : 'Guardar Sucursal'}
          </Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.card, borderRadius: 16, padding: 24, borderWidth: 1, borderColor: C.border },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 },
  title: { color: C.text, fontSize: 18, fontWeight: '800' },
  label: { fontSize: 13, fontWeight: '600', color: C.muted, marginBottom: 6, marginTop: 16 },
  input: { backgroundColor: C.input, borderWidth: 1, borderColor: C.border, borderRadius: 10, padding: 12, color: C.text, fontSize: 15 },
  infoRow: { flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 6 },
  infoText: { color: C.muted, fontSize: 12, flex: 1 },
  btn: { backgroundColor: C.accent, borderRadius: 10, padding: 14, marginTop: 28 },
  btnText: { color: C.white, textAlign: 'center', fontWeight: '700', fontSize: 16 },
});
