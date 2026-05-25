import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { getChat, getGeneralChat, sendMessage } from '../services/api';

const C = {
  bg: '#0b141a',
  panel: '#111b21',
  surface: '#17232b',
  surfaceAlt: '#202c33',
  accent: '#25d366',
  accentDark: '#128c7e',
  userBubble: '#005c4b',
  text: '#eef6f7',
  muted: '#8fa4ad',
  border: '#2a3942',
  danger: '#ef4444',
};

const INTRO_MESSAGE = {
  id: 'intro-message',
  sender: 'empresa',
  message: 'Hola, soy tu preventista. Puedes escribir tu pedido, consultar estados o pedir ayuda con tus sucursales.',
  created_at: new Date().toISOString(),
};

const formatTime = (dateStr) => {
  if (!dateStr) return '';
  try {
    let cleaned = String(dateStr).trim();
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(cleaned)) {
      cleaned = cleaned.replace(' ', 'T') + 'Z';
    } else {
      if (cleaned.includes(' ') && !cleaned.includes('T')) {
        cleaned = cleaned.replace(' ', 'T');
      }
      cleaned = cleaned.replace(/\.(\d{3})\d+/, '.$1');
    }
    const date = new Date(cleaned);
    if (Number.isNaN(date.getTime())) return '';
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
  } catch (e) {
    return '';
  }
};

export default function ChatScreen({ route, navigation }) {
  const orderId = route?.params?.orderId ?? null;
  const isOrderChat = Boolean(orderId);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const listRef = useRef(null);
  const insets = useSafeAreaInsets();

  const scrollToBottom = () => {
    requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
  };

  const load = useCallback(() => {
    const request = isOrderChat ? getChat(orderId) : getGeneralChat();
    request
      .then((data) => {
        setMessages(Array.isArray(data) ? data : []);
        setErrorMessage('');
      })
      .catch(() => {
        setErrorMessage('No se pudo actualizar el chat. Revisa la conexion.');
      });
  }, [isOrderChat, orderId]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  const openParentRoute = (screen) => {
    const parent = navigation.getParent?.();
    if (parent) {
      parent.navigate(screen);
      return;
    }
    navigation.navigate(screen);
  };

  const handleSend = async () => {
    const clean = text.trim();
    if (!clean || sending) return;

    const optimistic = {
      id: `local-${Date.now()}`,
      order_id: orderId,
      sender: 'user',
      message: clean,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimistic]);
    setText('');
    setSending(true);
    setErrorMessage('');
    scrollToBottom();

    try {
      const saved = await sendMessage({ order_id: orderId, message: clean, sender: 'user' });
      setMessages((prev) => prev.map((m) => (m.id === optimistic.id ? saved : m)));
      load();
    } catch (e) {
      setMessages((prev) => prev.map((m) => (m.id === optimistic.id ? { ...m, failed: true } : m)));
      setErrorMessage('El mensaje quedo pendiente. Intenta enviarlo otra vez.');
    } finally {
      setSending(false);
    }
  };

  const handleVoice = () => {
    Alert.alert('Microfono', 'Boton listo para el mockup. La grabacion de audio se puede conectar en el siguiente paso.');
  };

  const chatMessages = messages.length ? messages : [INTRO_MESSAGE];
  const hasText = text.trim().length > 0;

  return (
    <View style={s.screen}>
      <View style={[s.header, { paddingTop: Math.max(insets.top, 10) }]}>
        {isOrderChat && navigation.canGoBack() ? (
          <TouchableOpacity style={s.headerIcon} onPress={() => navigation.goBack()}>
            <Ionicons name="chevron-back" size={24} color={C.text} />
          </TouchableOpacity>
        ) : (
          <View style={s.avatar}>
            <Ionicons name="chatbubble-ellipses" size={20} color={C.panel} />
          </View>
        )}

        <View style={s.headerCopy}>
          <Text style={s.title}>{isOrderChat ? `Pedido #${String(orderId).slice(0, 8)}` : 'Preventista AJE'}</Text>
          <Text style={s.status}>En linea para tomar pedidos</Text>
        </View>

        {!isOrderChat ? (
          <TouchableOpacity style={s.headerIcon} onPress={() => openParentRoute('Catalog')}>
            <Ionicons name="cart-outline" size={22} color={C.text} />
          </TouchableOpacity>
        ) : null}
      </View>

      <KeyboardAvoidingView
        style={s.keyboard}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 4 : 0}
      >
        {!isOrderChat ? (
          <View style={s.shortcuts}>
            <TouchableOpacity style={s.shortcut} onPress={() => openParentRoute('Catalog')}>
              <Ionicons name="add-circle-outline" size={18} color={C.accent} />
              <Text style={s.shortcutText}>Nuevo pedido</Text>
            </TouchableOpacity>
            <TouchableOpacity style={s.shortcut} onPress={() => navigation.navigate('Pedidos')}>
              <Ionicons name="receipt-outline" size={18} color={C.accent} />
              <Text style={s.shortcutText}>Pedidos</Text>
            </TouchableOpacity>
            <TouchableOpacity style={s.shortcut} onPress={() => navigation.navigate('Sucursales')}>
              <Ionicons name="storefront-outline" size={18} color={C.accent} />
              <Text style={s.shortcutText}>Sucursales</Text>
            </TouchableOpacity>
          </View>
        ) : null}

        <FlatList
          ref={listRef}
          data={chatMessages}
          keyExtractor={(item) => String(item.id)}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={s.listContent}
          onContentSizeChange={scrollToBottom}
          renderItem={({ item }) => {
            const isUser = item.sender === 'user';
            return (
              <View style={[s.bubble, isUser ? s.userBubble : s.agentBubble, item.failed && s.failedBubble]}>
                <Text style={s.messageText}>{item.message}</Text>
                <View style={s.metaRow}>
                  {item.failed ? <Ionicons name="alert-circle" size={12} color={C.danger} /> : null}
                  <Text style={[s.metaText, isUser && s.userMetaText]}>
                    {item.failed ? 'Pendiente' : formatTime(item.created_at)}
                  </Text>
                </View>
              </View>
            );
          }}
        />

        {errorMessage ? (
          <View style={s.errorBar}>
            <Text style={s.errorText}>{errorMessage}</Text>
          </View>
        ) : null}

        <View style={[s.composerWrap, { paddingBottom: Math.max(insets.bottom, 10) }]}>
          <View style={s.composer}>
            <TouchableOpacity style={s.inlineIcon} onPress={() => openParentRoute('Catalog')}>
              <Ionicons name="add" size={22} color={C.muted} />
            </TouchableOpacity>
            <TextInput
              style={s.input}
              value={text}
              onChangeText={setText}
              placeholder="Escribe un mensaje"
              placeholderTextColor={C.muted}
              multiline
              maxLength={500}
              returnKeyType="default"
              textAlignVertical="center"
            />
          </View>
          <TouchableOpacity
            style={[s.actionButton, hasText ? s.sendButton : s.micButton, sending && s.disabledButton]}
            onPress={hasText ? handleSend : handleVoice}
            disabled={sending}
          >
            <Ionicons name={hasText ? 'send' : 'mic'} size={21} color="#fff" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  header: {
    backgroundColor: C.panel,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingBottom: 10,
    gap: 10,
  },
  avatar: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: C.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerCopy: { flex: 1 },
  title: { color: C.text, fontSize: 18, fontWeight: '800' },
  status: { color: C.muted, fontSize: 12, marginTop: 1 },
  keyboard: { flex: 1 },
  shortcuts: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 12,
    paddingTop: 10,
    paddingBottom: 6,
    backgroundColor: C.bg,
  },
  shortcut: {
    flex: 1,
    minHeight: 40,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surface,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 8,
  },
  shortcutText: { color: C.text, fontSize: 12, fontWeight: '700' },
  listContent: {
    paddingHorizontal: 12,
    paddingTop: 12,
    paddingBottom: 12,
    flexGrow: 1,
    justifyContent: 'flex-end',
  },
  bubble: {
    maxWidth: '82%',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingTop: 9,
    paddingBottom: 6,
    marginBottom: 8,
    borderWidth: 1,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: C.userBubble,
    borderColor: '#0b6b59',
    borderBottomRightRadius: 4,
  },
  agentBubble: {
    alignSelf: 'flex-start',
    backgroundColor: C.surfaceAlt,
    borderColor: C.border,
    borderBottomLeftRadius: 4,
  },
  failedBubble: { borderColor: C.danger },
  messageText: { color: C.text, fontSize: 15, lineHeight: 21 },
  metaRow: {
    marginTop: 4,
    alignSelf: 'flex-end',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  metaText: { color: C.muted, fontSize: 10 },
  userMetaText: { color: 'rgba(255,255,255,0.65)' },
  errorBar: {
    marginHorizontal: 12,
    marginBottom: 6,
    borderRadius: 10,
    backgroundColor: 'rgba(239,68,68,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.3)',
    padding: 8,
  },
  errorText: { color: '#fecaca', fontSize: 12, textAlign: 'center' },
  composerWrap: {
    backgroundColor: C.panel,
    borderTopWidth: 1,
    borderTopColor: C.border,
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
    paddingHorizontal: 10,
    paddingTop: 8,
  },
  composer: {
    flex: 1,
    minHeight: 46,
    maxHeight: 112,
    borderRadius: 23,
    backgroundColor: C.surfaceAlt,
    borderWidth: 1,
    borderColor: C.border,
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingLeft: 8,
    paddingRight: 12,
  },
  inlineIcon: {
    width: 34,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 104,
    color: C.text,
    fontSize: 15,
    paddingTop: 11,
    paddingBottom: 10,
  },
  actionButton: {
    width: 46,
    height: 46,
    borderRadius: 23,
    alignItems: 'center',
    justifyContent: 'center',
  },
  micButton: { backgroundColor: C.accentDark },
  sendButton: { backgroundColor: C.accent },
  disabledButton: { opacity: 0.6 },
});
