import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { NativeModulesProxy } from 'expo-modules-core';
import { useFocusEffect } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { confirmOrder, getChat, getGeneralChat, parseOrderText, sendMessage } from '../services/api';
import { colors as C } from '../theme';
import { GradientScreen } from '../components/ScreenBackground';

const INTRO_MESSAGE = {
  id: 'intro-message',
  sender: 'empresa',
  message: 'Hola, soy tu preventista. Puedes escribir o tocar el microfono para dictar un pedido.',
  created_at: new Date().toISOString(),
};

const getSpeechRecognitionModule = () => {
  if (!NativeModulesProxy?.ExpoSpeechRecognition) {
    return null;
  }
  try {
    return require('expo-speech-recognition').ExpoSpeechRecognitionModule;
  } catch (error) {
    return null;
  }
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

const buildInterpretationMessage = (parsed) => {
  if (parsed?.message) return parsed.message;
  if (!parsed?.products?.length) {
    return 'No pude identificar productos en el audio. Intenta decir cantidad y producto.';
  }
  const lines = parsed.products.map((item) => `- ${item.quantity} x ${item.name}: Bs ${Number(item.subtotal).toFixed(2)}`);
  return `Pedido interpretado:\n${lines.join('\n')}\nTotal estimado: Bs ${Number(parsed.total || 0).toFixed(2)}`;
};

const GENERAL_SUGGESTIONS = [
  'Menu',
  'Lista de pedidos',
  'Pedidos pendientes',
  'Pedidos confirmados',
  'Pedidos rechazados',
  'Pedidos en proceso',
];

const ORDER_SUGGESTIONS = [
  'Estado del pedido',
  'Lista de pedidos',
  'Menu',
  'Pedidos pendientes',
];

const CHAT_ACTION_PREFIX = '@@action ';

const parseMessageParts = (message) => {
  const actions = [];
  const visibleLines = [];

  String(message || '').split('\n').forEach((line) => {
    const trimmed = line.trim();
    if (trimmed.startsWith(CHAT_ACTION_PREFIX)) {
      try {
        const action = JSON.parse(trimmed.slice(CHAT_ACTION_PREFIX.length));
        if (action?.type) actions.push(action);
      } catch (_) {
        visibleLines.push(line);
      }
      return;
    }
    visibleLines.push(line);
  });

  return { text: visibleLines.join('\n').trim(), actions };
};

const getChatActionIcon = (type) => {
  if (type === 'order') return 'receipt-outline';
  if (type === 'orders') return 'list-outline';
  return 'chatbubble-ellipses-outline';
};

const getChatActionMeta = (action) => (
  [action.store, action.status, action.total, action.delivery ? `Entrega ${action.delivery}` : null]
    .filter(Boolean)
    .join(' - ')
);

export default function ChatScreen({ route, navigation }) {
  const orderId = route?.params?.orderId ?? null;
  const isOrderChat = Boolean(orderId);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const [orderStatus, setOrderStatus] = useState(route?.params?.orderStatus ?? null);
  const [submitting, setSubmitting] = useState(false);
  const [recognizing, setRecognizing] = useState(false);
  const [voiceHint, setVoiceHint] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const listRef = useRef(null);
  const speechModuleRef = useRef(null);
  const lastTranscriptRef = useRef('');
  const autoInterpretRef = useRef(false);
  const autoSendLockedRef = useRef(false);
  const insets = useSafeAreaInsets();

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      try {
        listRef.current?.scrollToOffset({ offset: 0, animated: true });
      } catch (_) {}
    }, 50);
  }, []);

  const load = useCallback(() => {
    const request = isOrderChat ? getChat(orderId) : getGeneralChat();
    request
      .then((data) => {
        const nextMsgs = Array.isArray(data) ? data : [];
        setMessages((prev) => {
          if (nextMsgs.length > prev.length) {
            scrollToBottom();
          }
          return nextMsgs;
        });
        setErrorMessage('');
      })
      .catch(() => {
        setErrorMessage('No se pudo actualizar el chat. Revisa la conexion.');
      });
  }, [isOrderChat, orderId, scrollToBottom]);

  const sendTextMessage = useCallback(async (rawText, options = {}) => {
    const clean = String(rawText || '').trim();
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

      if (options.interpret) {
        try {
          const parsed = await parseOrderText(clean);
          const interpretation = buildInterpretationMessage(parsed);
          const systemMessage = await sendMessage({ order_id: orderId, message: interpretation, sender: 'system' });
          setMessages((prev) => [...prev, systemMessage]);
        } catch (e) {
          setErrorMessage('El mensaje se envio, pero no pude interpretar el pedido por voz.');
        }
      }

      load();
    } catch (e) {
      setMessages((prev) => prev.map((m) => (m.id === optimistic.id ? { ...m, failed: true } : m)));
      setErrorMessage('El mensaje quedo pendiente. Intenta enviarlo otra vez.');
    } finally {
      setSending(false);
      scrollToBottom();
    }
  }, [load, orderId, scrollToBottom, sending]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 5000);
    return () => clearInterval(interval);
  }, [load]);

  useFocusEffect(useCallback(() => {
    load();
  }, [load]));

  useEffect(() => {
    const speech = getSpeechRecognitionModule();
    speechModuleRef.current = speech;
    if (!speech?.addListener) return undefined;

    const subscriptions = [
      speech.addListener('start', () => {
        setRecognizing(true);
        setVoiceHint('Escuchando pedido...');
      }),
      speech.addListener('result', (event) => {
        const transcript = event?.results?.[0]?.transcript || event?.transcript || '';
        const clean = String(transcript).trim();
        if (!clean) return;
        lastTranscriptRef.current = clean;
        setText(clean);
        setVoiceHint(event?.isFinal ? 'Listo, interpretando...' : 'Escuchando pedido...');
      }),
      speech.addListener('end', () => {
        setRecognizing(false);
        const transcript = lastTranscriptRef.current.trim();
        if (autoInterpretRef.current && transcript && !autoSendLockedRef.current) {
          autoSendLockedRef.current = true;
          setVoiceHint('Interpretando pedido...');
          sendTextMessage(transcript, { interpret: true }).finally(() => {
            autoInterpretRef.current = false;
            autoSendLockedRef.current = false;
            setVoiceHint('');
          });
          return;
        }
        autoInterpretRef.current = false;
        setVoiceHint(transcript ? 'Texto listo para enviar.' : 'No se detecto voz.');
      }),
      speech.addListener('error', () => {
        autoInterpretRef.current = false;
        autoSendLockedRef.current = false;
        setRecognizing(false);
        setVoiceHint('No pude reconocer el audio. Intenta otra vez.');
      }),
    ];

    return () => {
      subscriptions.forEach((sub) => sub?.remove?.());
    };
  }, [sendTextMessage]);

  const openParentRoute = (screen, params) => {
    const parent = navigation.getParent?.();
    if (parent) {
      parent.navigate(screen, params);
      return;
    }
    navigation.navigate(screen, params);
  };

  const openCatalogForChat = () => {
    openParentRoute('Catalog', { sendToChat: true, orderId });
  };

  const openCatalogForNewOrder = () => {
    openParentRoute('Catalog', { sendToChat: false, orderId: null });
  };

  const openOrderDetail = useCallback((targetOrderId) => {
    if (!targetOrderId) return;
    const routeNames = navigation.getState?.()?.routeNames || [];
    if (routeNames.includes('OrderDetail')) {
      navigation.navigate('OrderDetail', { orderId: targetOrderId });
      return;
    }
    openParentRoute('OrderDetail', { orderId: targetOrderId });
  }, [navigation]);

  const openOrdersList = useCallback((statusFilter = null) => {
    const params = { statusFilter: statusFilter || null };
    const routeNames = navigation.getState?.()?.routeNames || [];
    if (routeNames.includes('Pedidos')) {
      navigation.navigate('Pedidos', params);
      return;
    }
    navigation.navigate('Main', { screen: 'Pedidos', params });
  }, [navigation]);

  const handleChatAction = useCallback((action) => {
    if (action.type === 'order') {
      openOrderDetail(action.order_id);
      return;
    }
    if (action.type === 'orders') {
      openOrdersList(action.status);
      return;
    }
    if (action.type === 'message') {
      sendTextMessage(action.message || action.label);
    }
  }, [openOrderDetail, openOrdersList, sendTextMessage]);

  const handleSend = () => {
    sendTextMessage(text);
  };

  const handleSubmitOrder = async () => {
    Alert.alert(
      'Enviar pedido',
      '¿Confirmas que quieres enviar este pedido? Quedará en estado Pendiente.',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Enviar',
          style: 'default',
          onPress: async () => {
            setSubmitting(true);
            try {
              await confirmOrder(orderId);
              setOrderStatus('pendiente');
              load();
            } catch (e) {
              Alert.alert('Error', e?.message || 'No se pudo enviar el pedido. Intenta de nuevo.');
            } finally {
              setSubmitting(false);
            }
          },
        },
      ]
    );
  };

  const handleVoice = async () => {
    const speech = speechModuleRef.current || getSpeechRecognitionModule();
    speechModuleRef.current = speech;

    if (!speech) {
      Alert.alert(
        'Voz no disponible',
        'Para usar el microfono necesitas abrir la app en una build de desarrollo con reconocimiento de voz instalado.'
      );
      return;
    }

    if (recognizing) {
      autoInterpretRef.current = true;
      setVoiceHint('Cerrando audio...');
      try {
        await speech.stop();
      } catch (e) {
        try {
          await speech.abort();
        } catch (_) {}
      }
      return;
    }

    if (sending) return;

    try {
      const available = await speech.isRecognitionAvailable?.();
      if (available === false) {
        Alert.alert('Voz no disponible', 'El dispositivo no tiene un servicio de reconocimiento de voz activo.');
        return;
      }

      const permission = await speech.requestPermissionsAsync();
      if (!permission?.granted) {
        Alert.alert('Permiso requerido', 'Activa el permiso de microfono y reconocimiento de voz para dictar pedidos.');
        return;
      }

      lastTranscriptRef.current = '';
      autoInterpretRef.current = true;
      autoSendLockedRef.current = false;
      setText('');
      setVoiceHint('Escuchando pedido...');

      await speech.start({
        lang: 'es-BO',
        interimResults: true,
        continuous: false,
        maxAlternatives: 1,
        addsPunctuation: true,
        androidIntentOptions: {
          EXTRA_LANGUAGE_MODEL: 'free_form',
        },
      });
    } catch (e) {
      autoInterpretRef.current = false;
      autoSendLockedRef.current = false;
      setRecognizing(false);
      setVoiceHint('');
      Alert.alert('No pude iniciar la voz', e?.message || 'Intenta otra vez.');
    }
  };

  const chatMessages = messages.length ? messages : [INTRO_MESSAGE];
  const suggestions = isOrderChat ? ORDER_SUGGESTIONS : GENERAL_SUGGESTIONS;
  const hasText = text.trim().length > 0;
  const actionIcon = recognizing ? 'stop' : hasText ? 'send' : 'mic';

  return (
    <GradientScreen style={s.screen}>
      <View style={[s.header, { paddingTop: Math.max(insets.top, 10) }]}>
        {isOrderChat && navigation.canGoBack() ? (
          <TouchableOpacity style={s.headerIcon} onPress={() => navigation.goBack()}>
            <Ionicons name="chevron-back" size={24} color={C.text} />
          </TouchableOpacity>
        ) : (
          <View style={s.avatar}>
            <Ionicons name="chatbubble-ellipses" size={20} color={C.text} />
          </View>
        )}

        <View style={s.headerCopy}>
          <Text style={s.title}>{isOrderChat ? `Pedido #${String(orderId).slice(0, 8)}` : 'Preventista AJE'}</Text>
          <Text style={s.status}>En linea para tomar pedidos</Text>
        </View>

        {!isOrderChat ? (
          <TouchableOpacity style={s.headerIcon} onPress={openCatalogForNewOrder}>
            <Ionicons name="cart-outline" size={22} color={C.text} />
          </TouchableOpacity>
        ) : null}
      </View>

      <KeyboardAvoidingView
        style={s.keyboard}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 4 : 0}
      >
        {isOrderChat && orderStatus === 'borrador' ? (
          <View style={s.submitBanner}>
            <View style={s.submitBannerInfo}>
              <Ionicons name="time-outline" size={18} color={C.warning} />
              <Text style={s.submitBannerText}>Este pedido está en borrador</Text>
            </View>
            <TouchableOpacity
              style={[s.submitButton, submitting && s.submitButtonDisabled]}
              onPress={handleSubmitOrder}
              disabled={submitting}
              activeOpacity={0.82}
            >
              <Ionicons name="paper-plane-outline" size={16} color={C.white} />
              <Text style={s.submitButtonText}>{submitting ? 'Enviando...' : 'Enviar pedido'}</Text>
            </TouchableOpacity>
          </View>
        ) : null}

        {!isOrderChat ? (
          <View style={s.shortcuts}>
            <TouchableOpacity style={s.shortcut} onPress={openCatalogForNewOrder}>
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
          data={[...chatMessages].reverse()}
          inverted
          keyExtractor={(item) => String(item.id)}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={s.listContent}
          renderItem={({ item }) => {
            const isUser = item.sender === 'user';
            const parsed = parseMessageParts(item.message);
            return (
              <View style={[s.bubble, isUser ? s.userBubble : s.agentBubble, item.failed && s.failedBubble]}>
                {parsed.text ? <Text style={s.messageText}>{parsed.text}</Text> : null}
                {parsed.actions.length ? (
                  <View style={[s.messageActions, !parsed.text && s.messageActionsOnly]}>
                    {parsed.actions.map((action, index) => {
                      const meta = getChatActionMeta(action);
                      return (
                        <TouchableOpacity
                          key={`${action.type}-${action.order_id || action.status || action.message || index}`}
                          activeOpacity={0.82}
                          style={s.messageAction}
                          onPress={() => handleChatAction(action)}
                        >
                          <View style={s.messageActionIcon}>
                            <Ionicons name={getChatActionIcon(action.type)} size={15} color={C.accent} />
                          </View>
                          <View style={s.messageActionCopy}>
                            <Text style={s.messageActionTitle}>{action.label || action.message || 'Abrir'}</Text>
                            {meta ? <Text style={s.messageActionMeta}>{meta}</Text> : null}
                          </View>
                          <Ionicons name="chevron-forward" size={16} color={C.muted} />
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                ) : null}
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

        {voiceHint ? (
          <View style={s.voiceBar}>
            <Ionicons name={recognizing ? 'mic' : 'sparkles-outline'} size={15} color={recognizing ? C.accent : C.muted} />
            <Text style={s.voiceText}>{voiceHint}</Text>
          </View>
        ) : null}

        {errorMessage ? (
          <View style={s.errorBar}>
            <Text style={s.errorText}>{errorMessage}</Text>
          </View>
        ) : null}

        <View style={s.suggestionWrap}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={s.suggestionContent}
          >
            {suggestions.map((suggestion) => (
              <TouchableOpacity
                key={suggestion}
                activeOpacity={0.82}
                style={[s.suggestionChip, sending && s.suggestionChipDisabled]}
                onPress={() => sendTextMessage(suggestion)}
                disabled={sending}
              >
                <Text style={s.suggestionText}>{suggestion}</Text>
                <Ionicons name="send" size={12} color={C.whiteSoft} />
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        <View style={[s.composerWrap, { paddingBottom: Math.max(insets.bottom, 10) }]}>
          <View style={s.composer}>
            <TouchableOpacity style={s.inlineIcon} onPress={openCatalogForChat}>
              <Ionicons name="add" size={22} color={C.muted} />
            </TouchableOpacity>
            <TextInput
              style={s.input}
              value={text}
              onChangeText={setText}
              placeholder="Escribe o dicta un pedido"
              placeholderTextColor={C.muted}
              multiline
              maxLength={500}
              returnKeyType="default"
              textAlignVertical="center"
            />
          </View>
          <TouchableOpacity
            style={[
              s.actionButton,
              recognizing ? s.stopButton : hasText ? s.sendButton : s.micButton,
              sending && !recognizing && s.disabledButton,
            ]}
            onPress={recognizing ? handleVoice : hasText ? handleSend : handleVoice}
            disabled={sending && !recognizing}
          >
            <Ionicons name={actionIcon} size={21} color={C.white} />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </GradientScreen>
  );
}

const s = StyleSheet.create({
  screen: {},
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
    backgroundColor: C.accentSoft,
    borderWidth: 1,
    borderColor: C.borderStrong,
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
    backgroundColor: 'transparent',
  },
  shortcut: {
    flex: 1,
    minHeight: 40,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.surfaceAlt,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 6,
    paddingHorizontal: 8,
  },
  shortcutText: { color: C.text, fontSize: 12, fontWeight: '700' },
  suggestionWrap: {
    backgroundColor: 'transparent',
    paddingBottom: 6,
  },
  suggestionContent: {
    paddingHorizontal: 12,
    paddingTop: 4,
    paddingBottom: 2,
    gap: 7,
    alignItems: 'flex-end',
  },
  suggestionChip: {
    minHeight: 36,
    maxWidth: 210,
    borderRadius: 17,
    borderBottomRightRadius: 5,
    borderWidth: 1,
    borderColor: C.borderStrong,
    backgroundColor: 'rgba(126,87,255,0.42)',
    paddingLeft: 13,
    paddingRight: 10,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 7,
  },
  suggestionChipDisabled: { opacity: 0.55 },
  suggestionText: { color: C.text, fontSize: 12, fontWeight: '700', flexShrink: 1 },
  listContent: {
    paddingHorizontal: 12,
    paddingTop: 12,
    paddingBottom: 12,
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
    borderColor: C.userBubbleBorder,
    borderBottomRightRadius: 4,
  },
  agentBubble: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(42,33,82,0.64)',
    borderColor: C.border,
    borderBottomLeftRadius: 4,
  },
  failedBubble: { borderColor: C.danger },
  messageText: { color: C.text, fontSize: 15, lineHeight: 21 },
  messageActions: {
    marginTop: 10,
    gap: 7,
  },
  messageActionsOnly: { marginTop: 0 },
  messageAction: {
    minWidth: 230,
    borderRadius: 13,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: 'rgba(28,20,58,0.76)',
    paddingHorizontal: 9,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  messageActionIcon: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: C.accentSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  messageActionCopy: { flex: 1, minWidth: 0 },
  messageActionTitle: { color: C.text, fontSize: 12, fontWeight: '800' },
  messageActionMeta: { color: C.muted, fontSize: 11, marginTop: 2 },
  metaRow: {
    marginTop: 4,
    alignSelf: 'flex-end',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  metaText: { color: C.muted, fontSize: 10 },
  userMetaText: { color: C.whiteMuted },
  voiceBar: {
    marginHorizontal: 12,
    marginBottom: 6,
    borderRadius: 14,
    backgroundColor: C.surface,
    borderWidth: 1,
    borderColor: C.border,
    paddingHorizontal: 10,
    paddingVertical: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },
  voiceText: { color: C.text, fontSize: 12, flex: 1 },
  errorBar: {
    marginHorizontal: 12,
    marginBottom: 6,
    borderRadius: 10,
    backgroundColor: C.dangerSoft,
    borderWidth: 1,
    borderColor: C.dangerBorder,
    padding: 8,
  },
  errorText: { color: C.dangerText, fontSize: 12, textAlign: 'center' },
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
  stopButton: { backgroundColor: C.danger },
  sendButton: { backgroundColor: C.accent },
  disabledButton: { opacity: 0.6 },
  submitBanner: {
    marginHorizontal: 12,
    marginTop: 10,
    marginBottom: 4,
    borderRadius: 14,
    backgroundColor: 'rgba(245,158,11,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(245,158,11,0.35)',
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  submitBannerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flex: 1,
  },
  submitBannerText: {
    color: C.warning,
    fontSize: 13,
    fontWeight: '700',
    flexShrink: 1,
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: C.accent,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: C.white,
    fontSize: 13,
    fontWeight: '800',
  },
});
