import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { getMe, updateMe } from '../services/api';
import { colors as C } from '../theme';
import { GradientScreen, GradientScrollView } from '../components/ScreenBackground';

export default function ProfileScreen({ onLogout }) {
  const [user, setUser] = useState(null);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    getMe()
      .then((u) => {
        setUser(u);
        setName(u.name || '');
        setPhone(u.phone || '');
      })
      .catch(() => setError('No se pudo cargar el perfil.'))
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (field, value) => {
    if (field === 'name') setName(value);
    if (field === 'phone') setPhone(value);
    setDirty(true);
    setSuccess('');
    setError('');
  };

  const handleSave = async () => {
    if (!name.trim()) {
      setError('El nombre no puede estar vacío.');
      return;
    }
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const updated = await updateMe({ name: name.trim(), phone: phone.trim() });
      setUser(updated);
      setDirty(false);
      setSuccess('Perfil actualizado correctamente.');
    } catch (e) {
      setError(e.message || 'No se pudo guardar el perfil.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Cerrar sesión',
      '¿Estás seguro que deseas cerrar sesión?',
      [
        { text: 'Cancelar', style: 'cancel' },
        { text: 'Cerrar sesión', style: 'destructive', onPress: onLogout },
      ]
    );
  };

  if (loading) {
    return (
      <GradientScreen style={s.centered}>
        <ActivityIndicator size="large" color={C.accent} />
      </GradientScreen>
    );
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <GradientScrollView
        contentContainerStyle={s.content}
        keyboardShouldPersistTaps="handled"
      >
        {/* Avatar Section */}
        <View style={s.avatarSection}>
          <View style={s.avatarCircle}>
            <Text style={s.avatarLetter}>
              {(name || user?.email || '?')[0].toUpperCase()}
            </Text>
          </View>
          <Text style={s.emailText}>{user?.email}</Text>
          <View style={s.roleBadge}>
            <Ionicons name="shield-checkmark-outline" size={13} color={C.accent} />
            <Text style={s.roleText}>{user?.role || 'preventista'}</Text>
          </View>
        </View>

        {/* Form */}
        <View style={s.card}>
          <Text style={s.sectionTitle}>Información personal</Text>

          <Text style={s.label}>Nombre</Text>
          <TextInput
            style={s.input}
            value={name}
            onChangeText={(v) => handleChange('name', v)}
            placeholder="Tu nombre"
            placeholderTextColor={C.muted}
            autoCapitalize="words"
          />

          <Text style={s.label}>Teléfono</Text>
          <TextInput
            style={s.input}
            value={phone}
            onChangeText={(v) => handleChange('phone', v)}
            placeholder="Tu número de teléfono"
            placeholderTextColor={C.muted}
            keyboardType="phone-pad"
          />
        </View>

        {/* Feedback */}
        {error ? (
          <View style={s.errorBar}>
            <Ionicons name="alert-circle-outline" size={15} color={C.danger} />
            <Text style={s.errorText}>{error}</Text>
          </View>
        ) : null}

        {success ? (
          <View style={s.successBar}>
            <Ionicons name="checkmark-circle-outline" size={15} color={C.success} />
            <Text style={s.successText}>{success}</Text>
          </View>
        ) : null}

        {/* Save Button */}
        <TouchableOpacity
          style={[s.saveBtn, (!dirty || saving) && s.saveBtnDisabled]}
          onPress={handleSave}
          disabled={!dirty || saving}
        >
          {saving ? (
            <ActivityIndicator size="small" color={C.white} />
          ) : (
            <>
              <Ionicons name="save-outline" size={18} color={C.white} />
              <Text style={s.saveBtnText}>Guardar cambios</Text>
            </>
          )}
        </TouchableOpacity>

        {/* Logout */}
        <TouchableOpacity style={s.logoutBtn} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={18} color={C.danger} />
          <Text style={s.logoutText}>Cerrar sesión</Text>
        </TouchableOpacity>
      </GradientScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  content: { padding: 20, paddingBottom: 40 },
  centered: { alignItems: 'center', justifyContent: 'center' },

  avatarSection: { alignItems: 'center', marginBottom: 24, marginTop: 8 },
  avatarCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: C.accentSoft,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: C.borderStrong,
    marginBottom: 10,
  },
  avatarLetter: { fontSize: 36, fontWeight: '900', color: C.white },
  emailText: { color: C.muted, fontSize: 14, marginBottom: 6 },
  roleBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: C.accentSoft,
    borderWidth: 1,
    borderColor: C.borderStrong,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  roleText: { color: C.accent, fontSize: 12, fontWeight: '700', textTransform: 'capitalize' },

  card: {
    backgroundColor: C.card,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: C.borderStrong,
    padding: 16,
    marginBottom: 14,
  },
  sectionTitle: { color: C.muted, fontSize: 12, fontWeight: '700', marginBottom: 14, textTransform: 'uppercase', letterSpacing: 0.8 },

  label: { color: C.muted, fontSize: 12, fontWeight: '600', marginBottom: 6, marginTop: 4 },
  input: {
    backgroundColor: C.input,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 18,
    color: C.text,
    fontSize: 15,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginBottom: 14,
  },

  errorBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    backgroundColor: C.dangerSoft,
    borderWidth: 1,
    borderColor: C.dangerBorder,
    borderRadius: 18,
    padding: 10,
    marginBottom: 12,
  },
  errorText: { color: C.dangerText, fontSize: 13, flex: 1 },

  successBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    backgroundColor: 'rgba(34,197,94,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(34,197,94,0.3)',
    borderRadius: 18,
    padding: 10,
    marginBottom: 12,
  },
  successText: { color: C.success, fontSize: 13, flex: 1 },

  saveBtn: {
    backgroundColor: C.accent,
    borderRadius: 18,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 12,
  },
  saveBtnDisabled: { opacity: 0.45 },
  saveBtnText: { color: C.white, fontSize: 15, fontWeight: '700' },

  logoutBtn: {
    borderRadius: 18,
    paddingVertical: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: C.dangerBorder,
    backgroundColor: C.dangerSoft,
  },
  logoutText: { color: C.danger, fontSize: 15, fontWeight: '700' },
});
