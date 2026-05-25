import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import { createStore } from '../services/api';
import { Ionicons } from '@expo/vector-icons';

const C = { bg: '#0f1117', card: '#1a1d29', accent: '#6366f1', text: '#f0f2f5', muted: '#8b92a5', border: '#2a2f45', input: '#181b27' };

export default function CreateStoreScreen({ navigation }) {
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [phone, setPhone] = useState('');
  const [latitude, setLatitude] = useState('-17.3935');
  const [longitude, setLongitude] = useState('-66.157');
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!name || !address) { Alert.alert('Error', 'Nombre y dirección son obligatorios'); return; }
    setLoading(true);
    try {
      await createStore({
        name, address, phone,
        latitude: parseFloat(latitude) || -17.3935,
        longitude: parseFloat(longitude) || -66.157,
      });
      navigation.goBack();
    } catch (e) { Alert.alert('Error', e.message); }
    finally { setLoading(false); }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ padding: 20 }}>
      <View style={s.card}>
        <Text style={s.label}>Nombre de la tienda *</Text>
        <TextInput style={s.input} value={name} onChangeText={setName} placeholder="Ej: Tienda San Miguel" placeholderTextColor={C.muted} />

        <Text style={s.label}>Dirección *</Text>
        <TextInput style={s.input} value={address} onChangeText={setAddress} placeholder="Ej: Av. Blanco Galindo #1234" placeholderTextColor={C.muted} />

        <Text style={s.label}>Teléfono</Text>
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

        <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: 12, gap: 6 }}>
          <Ionicons name="information-circle-outline" size={16} color={C.accent} />
          <Text style={{ color: C.muted, fontSize: 12, flex: 1 }}>
            En una versión futura se podrá seleccionar la ubicación desde el mapa.
          </Text>
        </View>

        <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={handleSave} disabled={loading}>
          <Text style={s.btnText}>{loading ? 'Guardando...' : 'Guardar Tienda'}</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.card, borderRadius: 16, padding: 24, borderWidth: 1, borderColor: C.border },
  label: { fontSize: 13, fontWeight: '600', color: C.muted, marginBottom: 6, marginTop: 16 },
  input: { backgroundColor: C.input, borderWidth: 1, borderColor: C.border, borderRadius: 10, padding: 12, color: C.text, fontSize: 15 },
  btn: { backgroundColor: C.accent, borderRadius: 10, padding: 14, marginTop: 28 },
  btnText: { color: '#fff', textAlign: 'center', fontWeight: '700', fontSize: 16 },
});
