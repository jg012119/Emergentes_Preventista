import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { login } from '../services/api';
import { colors as C } from '../theme';
import { GradientScreen } from '../components/ScreenBackground';

export default function LoginScreen({ navigation, onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Completa todos los campos');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await login(email, password);
      onLogin(res.access_token);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GradientScreen>
      <KeyboardAvoidingView style={s.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <View style={s.card}>
          <View style={s.logoMark}>
            <Ionicons name="sparkles" size={34} color={C.accentLight} />
          </View>
          <Text style={s.logo}>Preventista</Text>
          <Text style={s.subtitle}>Inicia sesion para hacer pedidos</Text>
          {error ? <Text style={s.error}>{error}</Text> : null}
          <Text style={s.label}>Correo electronico</Text>
          <TextInput
            style={s.input}
            value={email}
            onChangeText={setEmail}
            placeholder="tu@email.com"
            placeholderTextColor={C.muted}
            keyboardType="email-address"
            autoCapitalize="none"
          />
          <Text style={s.label}>Contrasena</Text>
          <TextInput
            style={s.input}
            value={password}
            onChangeText={setPassword}
            placeholder="********"
            placeholderTextColor={C.muted}
            secureTextEntry
          />
          <TouchableOpacity style={[s.btn, loading && s.btnDisabled]} onPress={handleLogin} disabled={loading}>
            <Text style={s.btnText}>{loading ? 'Ingresando...' : 'Ingresar'}</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={() => navigation.navigate('Register')} style={s.linkWrap}>
            <Text style={s.linkText}>No tienes cuenta? Registrate</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </GradientScreen>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 24 },
  card: { backgroundColor: C.card, borderRadius: 28, padding: 28, borderWidth: 1, borderColor: C.borderStrong },
  logoMark: {
    width: 72,
    height: 72,
    borderRadius: 24,
    backgroundColor: C.accentSoft,
    borderWidth: 1,
    borderColor: C.borderStrong,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: 14,
  },
  logo: { fontSize: 30, fontWeight: '800', textAlign: 'center', color: C.text, marginBottom: 4 },
  subtitle: { fontSize: 14, color: C.muted, textAlign: 'center', marginBottom: 24 },
  label: { fontSize: 13, fontWeight: '600', color: C.muted, marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: C.input, borderWidth: 1, borderColor: C.border, borderRadius: 18, padding: 13, color: C.text, fontSize: 15 },
  btn: { backgroundColor: C.accent, borderRadius: 18, padding: 15, marginTop: 24 },
  btnDisabled: { opacity: 0.6 },
  btnText: { color: C.white, textAlign: 'center', fontWeight: '700', fontSize: 16 },
  linkWrap: { marginTop: 16 },
  linkText: { color: C.accentLight, textAlign: 'center' },
  error: { color: C.danger, textAlign: 'center', fontSize: 13, marginBottom: 8 },
});
