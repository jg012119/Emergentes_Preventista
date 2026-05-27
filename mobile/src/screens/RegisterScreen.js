import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { register } from '../services/api';
import { colors as C } from '../theme';

export default function RegisterScreen({ onLogin }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name || !email || !phone || !password) { setError('Completa todos los campos'); return; }
    setError(''); setLoading(true);
    try {
      const res = await register(name, email, phone, password);
      onLogin(res.access_token);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <ScrollView style={{ flex: 1, backgroundColor: C.bg }} contentContainerStyle={{ padding: 24 }}>
      <View style={s.card}>
        <Text style={s.title}>Crear cuenta</Text>
        {error ? <Text style={s.error}>{error}</Text> : null}
        <Text style={s.label}>Nombre completo</Text>
        <TextInput style={s.input} value={name} onChangeText={setName} placeholder="Tu nombre" placeholderTextColor={C.muted} />
        <Text style={s.label}>Correo electrónico</Text>
        <TextInput style={s.input} value={email} onChangeText={setEmail} placeholder="tu@email.com" placeholderTextColor={C.muted} keyboardType="email-address" autoCapitalize="none" />
        <Text style={s.label}>Teléfono</Text>
        <TextInput style={s.input} value={phone} onChangeText={setPhone} placeholder="77712345" placeholderTextColor={C.muted} keyboardType="phone-pad" />
        <Text style={s.label}>Contraseña</Text>
        <TextInput style={s.input} value={password} onChangeText={setPassword} placeholder="Mínimo 6 caracteres" placeholderTextColor={C.muted} secureTextEntry />
        <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={handleRegister} disabled={loading}>
          <Text style={s.btnText}>{loading ? 'Registrando...' : 'Registrarme'}</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  card: { backgroundColor: C.card, borderRadius: 16, padding: 28, borderWidth: 1, borderColor: C.border },
  title: { fontSize: 22, fontWeight: '700', color: C.text, marginBottom: 20 },
  label: { fontSize: 13, fontWeight: '600', color: C.muted, marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: C.input, borderWidth: 1, borderColor: C.border, borderRadius: 10, padding: 12, color: C.text, fontSize: 15 },
  btn: { backgroundColor: C.accent, borderRadius: 10, padding: 14, marginTop: 24 },
  btnText: { color: C.white, textAlign: 'center', fontWeight: '700', fontSize: 16 },
  error: { color: C.danger, textAlign: 'center', fontSize: 13, marginBottom: 8 },
});
