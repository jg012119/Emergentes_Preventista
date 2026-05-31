import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, Alert, ActivityIndicator,
} from 'react-native';
import MapView, { Marker } from 'react-native-maps';
import * as Location from 'expo-location';
import { createStore, updateStore } from '../services/api';
import { Ionicons } from '@expo/vector-icons';
import { colors as C } from '../theme';

// Default coords: Cochabamba, Bolivia
const DEFAULT_LAT = -17.3935;
const DEFAULT_LNG = -66.157;
const DELTA = 0.01;

export default function CreateStoreScreen({ route, navigation }) {
  const store = route?.params?.store ?? null;
  const isEditing = Boolean(store?.id);

  const initialLat = store?.latitude != null ? Number(store.latitude) : DEFAULT_LAT;
  const initialLng = store?.longitude != null ? Number(store.longitude) : DEFAULT_LNG;

  const [name, setName] = useState(store?.name ?? '');
  const [address, setAddress] = useState(store?.address ?? '');
  const [phone, setPhone] = useState(store?.phone ?? '');
  const [pinCoords, setPinCoords] = useState({ latitude: initialLat, longitude: initialLng });
  const [locating, setLocating] = useState(false);
  const [loading, setLoading] = useState(false);

  const mapRef = useRef(null);

  useLayoutEffect(() => {
    navigation.setOptions({ title: isEditing ? 'Editar Sucursal' : 'Nueva Sucursal' });
  }, [isEditing, navigation]);

  // Sync if navigated with different store params
  useEffect(() => {
    setName(store?.name ?? '');
    setAddress(store?.address ?? '');
    setPhone(store?.phone ?? '');
    setPinCoords({ latitude: initialLat, longitude: initialLng });
  }, [store?.id]);

  const handleMapPress = useCallback((e) => {
    setPinCoords(e.nativeEvent.coordinate);
  }, []);

  const handleDragEnd = useCallback((e) => {
    setPinCoords(e.nativeEvent.coordinate);
  }, []);

  const handleMyLocation = async () => {
    setLocating(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permiso denegado', 'Activa el permiso de ubicación en los ajustes del teléfono.');
        return;
      }
      const loc = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced });
      const coords = { latitude: loc.coords.latitude, longitude: loc.coords.longitude };
      setPinCoords(coords);
      mapRef.current?.animateToRegion({ ...coords, latitudeDelta: DELTA, longitudeDelta: DELTA }, 600);
    } catch (err) {
      Alert.alert('Error', 'No se pudo obtener tu ubicación.');
    } finally {
      setLocating(false);
    }
  };

  const handleSave = async () => {
    const payload = {
      name: name.trim(),
      address: address.trim(),
      phone: phone.trim(),
      latitude: pinCoords.latitude,
      longitude: pinCoords.longitude,
    };

    if (!payload.name || !payload.address) {
      Alert.alert('Error', 'Nombre y dirección son obligatorios.');
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

  const region = useMemo(() => ({
    latitude: pinCoords.latitude,
    longitude: pinCoords.longitude,
    latitudeDelta: DELTA,
    longitudeDelta: DELTA,
  }), []);

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ padding: 20 }}>
      <View style={s.card}>
        {/* Header */}
        <View style={s.headerRow}>
          <Ionicons name={isEditing ? 'create-outline' : 'storefront-outline'} size={22} color={C.accent} />
          <Text style={s.title}>{isEditing ? 'Actualizar sucursal' : 'Registrar sucursal'}</Text>
        </View>

        {/* Nombre */}
        <Text style={s.label}>Nombre de la sucursal *</Text>
        <TextInput
          style={s.input}
          value={name}
          onChangeText={setName}
          placeholder="Ej: Sucursal San Miguel"
          placeholderTextColor={C.muted}
        />

        {/* Dirección */}
        <Text style={s.label}>Dirección *</Text>
        <TextInput
          style={s.input}
          value={address}
          onChangeText={setAddress}
          placeholder="Ej: Av. Blanco Galindo #1234"
          placeholderTextColor={C.muted}
        />

        {/* Teléfono */}
        <Text style={s.label}>Teléfono</Text>
        <TextInput
          style={s.input}
          value={phone}
          onChangeText={setPhone}
          placeholder="77712345"
          placeholderTextColor={C.muted}
          keyboardType="phone-pad"
        />

        {/* Mapa */}
        <Text style={s.label}>Ubicación en el mapa *</Text>
        <Text style={s.hint}>Toca el mapa para colocar el pin o arrástralo para ajustar.</Text>

        <View style={s.mapContainer}>
          <MapView
            ref={mapRef}
            style={s.map}
            initialRegion={region}
            onPress={handleMapPress}
            showsUserLocation={false}
            showsMyLocationButton={false}
          >
            <Marker
              coordinate={pinCoords}
              draggable
              onDragEnd={handleDragEnd}
              pinColor={C.accent}
            />
          </MapView>

          {/* Botón Mi Ubicación */}
          <TouchableOpacity style={s.myLocationBtn} onPress={handleMyLocation} disabled={locating}>
            {locating
              ? <ActivityIndicator size="small" color={C.accent} />
              : <Ionicons name="locate-outline" size={22} color={C.accent} />
            }
          </TouchableOpacity>
        </View>

        {/* Coordenadas como referencia */}
        <View style={s.coordsRow}>
          <Ionicons name="location-outline" size={14} color={C.accent} />
          <Text style={s.coordsText}>
            {pinCoords.latitude.toFixed(6)}, {pinCoords.longitude.toFixed(6)}
          </Text>
        </View>

        {/* Botón guardar */}
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
  card: {
    backgroundColor: C.card,
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: C.border,
  },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 },
  title: { color: C.text, fontSize: 18, fontWeight: '800' },
  label: { fontSize: 13, fontWeight: '600', color: C.muted, marginBottom: 6, marginTop: 16 },
  hint: { fontSize: 12, color: C.muted, marginBottom: 10 },
  input: {
    backgroundColor: C.input,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 10,
    padding: 12,
    color: C.text,
    fontSize: 15,
  },

  // Mapa
  mapContainer: {
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: C.border,
    height: 260,
  },
  map: { flex: 1 },
  myLocationBtn: {
    position: 'absolute',
    bottom: 12,
    right: 12,
    backgroundColor: C.card,
    borderRadius: 24,
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: C.border,
    elevation: 4,
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
  },

  // Coordenadas
  coordsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 8,
    backgroundColor: C.input,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    alignSelf: 'flex-start',
  },
  coordsText: { color: C.muted, fontSize: 12, fontFamily: 'monospace' },

  // Botón
  btn: { backgroundColor: C.accent, borderRadius: 10, padding: 14, marginTop: 28 },
  btnText: { color: C.white, textAlign: 'center', fontWeight: '700', fontSize: 16 },
});
