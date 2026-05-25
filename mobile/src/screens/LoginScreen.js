import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { login } from '../services/api';
import { Ionicons } from '@expo/vector-icons';

const C = { bg: '#0f1117', card: '#1a1d29', accent: '#6366f1', accentLight: '#818cf8', text: '#f0f2f5', muted: '#8b92a5', border: '#2a2f45', danger: '#ef4444', input: '#181b27' };

export default function LoginScreen({ navigation, onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) { setError('Completa todos los campos'); return; }
    setError(''); setLoading(true);
    try {
      const res = await login(email, password);
      onLogin(res.access_token);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <KeyboardAvoidingView style={s.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={s.card}>
        <View style={{ alignItems: 'center', marginBottom: 8 }}>
          <Ionicons name="business" size={48} color={C.accentLight} />
        </View>
        <Text style={s.logo}>Preventista</Text>
        <Text style={s.subtitle}>Inicia sesión para hacer pedidos</Text>
        {error ? <Text style={s.error}>{error}</Text> : null}
        <Text style={s.label}>Correo electrónico</Text>
        <TextInput style={s.input} value={email} onChangeText={setEmail} placeholder="tu@email.com" placeholderTextColor={C.muted} keyboardType="email-address" autoCapitalize="none" />
        <Text style={s.label}>Contraseña</Text>
        <TextInput style={s.input} value={password} onChangeText={setPassword} placeholder="••••••••" placeholderTextColor={C.muted} secureTextEntry />
        <TouchableOpacity style={[s.btn, loading && s.btnDisabled]} onPress={handleLogin} disabled={loading}>
          <Text style={s.btnText}>{loading ? 'Ingresando...' : 'Ingresar'}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => navigation.navigate('Register')} style={{ marginTop: 16 }}>
          <Text style={{ color: C.accentLight, textAlign: 'center' }}>¿No tienes cuenta? Regístrate</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg, justifyContent: 'center', padding: 24 },
  card: { backgroundColor: C.card, borderRadius: 16, padding: 28, borderWidth: 1, borderColor: C.border },
  logo: { fontSize: 28, fontWeight: '800', textAlign: 'center', color: C.accentLight, marginBottom: 4 },
  subtitle: { fontSize: 14, color: C.muted, textAlign: 'center', marginBottom: 24 },
  label: { fontSize: 13, fontWeight: '600', color: C.muted, marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: C.input, borderWidth: 1, borderColor: C.border, borderRadius: 10, padding: 12, color: C.text, fontSize: 15 },
  btn: { backgroundColor: C.accent, borderRadius: 10, padding: 14, marginTop: 24 },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: '#fff', textAlign: 'center', fontWeight: '700', fontSize: 16 },
  error: { color: C.danger, textAlign: 'center', fontSize: 13, marginBottom: 8 },
});
