import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  FlatList,
  Keyboard,
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
import AsyncStorage from '@react-native-async-storage/async-storage';
import { NativeModulesProxy } from 'expo-modules-core';
import { useFocusEffect } from '@react-navigation/native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { confirmOrder, getChat, getGeneralChat, rateChatMessage, sendMessage } from '../services/api';
import { colors as C } from '../theme';
import { GradientScreen } from '../components/ScreenBackground';
import VoiceNoteBubble from '../components/VoiceNoteBubble';

const INTRO_MESSAGE = {
  id: 'intro-message',
  sender: 'empresa',
  message: 'Hola, soy tu preventista. Puedes escribir o tocar el microfono para dictar un pedido.',
  created_at: new Date().toISOString(),
};

const getSpeechRecognitionModule = () => {
  try {
    const { ExpoSpeechRecognitionModule } = require('expo-speech-recognition');
    return ExpoSpeechRecognitionModule || null;
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
const ACTIVE_DRAFT_ORDER_KEY = 'preventista.activeDraftOrderId';
const LEGACY_PENDING_ORDER_TEXT_KEY = 'preventista.pendingOrderText';
const PENDING_ORDER_TEXT_KEY = 'preventista.pendingOrderText.v2';

const ORDER_CONTEXT_RE = /\b(big|cielo|agua|volt|oro|pulp|cifrut|cola|lata|caja|litro|litros|ml|manana|mañana|hoy|tienda|cliente|un|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|\d+)\b/i;
const NON_ORDER_RE = /^(menu|catalogo|catálogo|lista|lista de pedidos|pedidos|estado|seguimiento)$/i;
const FRESH_ORDER_RE = /^\s*(quiero|necesito|dame|manda|mandame|mándame|mandale|mándale|pedido|orden)\b/i;
const CONTEXT_APPEND_RE = /^\s*(tambien|también|ademas|además|y|sumale|súmale|agrega|agregale|agrégale|agregame|agrégame|para|pa|de)\b/i;
const SHORT_CLARIFICATION_RE = /^\s*(si|sí|ok|okay|dale|correcto|esa|ese|eso|\d+(?:[.,]\d+)?(?:\s*(?:ml|l|lt|lts|litro|litros))?)\s*$/i;

const parseMessageParts = (message) => {
  const actions = [];
  const visibleLines = [];
  let isVoice = false;
  let voiceText = '';
  let voiceDuration = 0;

  let messageToParse = message;
  try {
    const jsonParsed = JSON.parse(message);
    if (jsonParsed && jsonParsed.is_voice) {
      isVoice = true;
      voiceText = jsonParsed.text || '';
      voiceDuration = jsonParsed.duration || 5;
      messageToParse = jsonParsed.text || '';
    }
  } catch (_) {}

  String(messageToParse || '').split('\n').forEach((line) => {
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

  return {
    text: visibleLines.join('\n').trim(),
    actions,
    isVoice,
    voiceText,
    voiceDuration
  };
};

const findActiveDraftOrderId = (messages) => {
  let activeId = null;
  (messages || []).forEach((message) => {
    const parsed = parseMessageParts(message.message);
    parsed.actions.forEach((action) => {
      if (action.type === 'confirm_order' && action.order_id) {
        activeId = action.order_id;
      }
    });

    const text = String(message.message || '').toLowerCase();
    if (
      activeId
      && (text.includes('confirmado y enviado') || text.includes('estado: pendiente'))
    ) {
      activeId = null;
    }
  });
  return activeId;
};

const shouldKeepPendingOrderText = (message) => {
  const clean = String(message || '').trim();
  if (!clean || NON_ORDER_RE.test(clean)) return false;
  if (SHORT_CLARIFICATION_RE.test(clean)) return false;
  return ORDER_CONTEXT_RE.test(clean);
};

const shouldClearPendingBeforeSend = (message) => {
  const clean = String(message || '').trim();
  if (!clean) return false;
  if (NON_ORDER_RE.test(clean)) return true;
  return FRESH_ORDER_RE.test(clean) && !CONTEXT_APPEND_RE.test(clean);
};

const mergePendingOrderText = (previous, current) => {
  const before = String(previous || '').trim();
  const next = String(current || '').trim();
  if (!before) return next;
  if (!next) return before;
  return `${before} ${next}`;
};

const getChatActionIcon = (type) => {
  if (type === 'order') return 'receipt-outline';
  if (type === 'orders') return 'list-outline';
  if (type === 'confirm_order') return 'checkmark-circle-outline';
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
  const [feedbackPending, setFeedbackPending] = useState({});
  const [activeDraftOrderId, setActiveDraftOrderId] = useState(null);
  const [pendingOrderText, setPendingOrderText] = useState('');
  const [keyboardVisible, setKeyboardVisible] = useState(false);
  const listRef = useRef(null);
  const speechModuleRef = useRef(null);
  const lastTranscriptRef = useRef('');
  const autoInterpretRef = useRef(false);
  const autoSendLockedRef = useRef(false);
  const voiceStartRef = useRef(0);
  const insets = useSafeAreaInsets();

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      try {
        listRef.current?.scrollToOffset({ offset: 0, animated: false });
      } catch (_) {}
    }, 80);
  }, []);

  const persistActiveDraftOrderId = useCallback((nextOrderId) => {
    setActiveDraftOrderId(nextOrderId || null);
    if (nextOrderId) {
      AsyncStorage.setItem(ACTIVE_DRAFT_ORDER_KEY, String(nextOrderId)).catch(() => {});
    } else {
      AsyncStorage.removeItem(ACTIVE_DRAFT_ORDER_KEY).catch(() => {});
    }
  }, []);

  const persistPendingOrderText = useCallback((nextText) => {
    const clean = String(nextText || '').trim();
    setPendingOrderText(clean);
    if (clean) {
      AsyncStorage.setItem(PENDING_ORDER_TEXT_KEY, clean).catch(() => {});
    } else {
      AsyncStorage.removeItem(PENDING_ORDER_TEXT_KEY).catch(() => {});
    }
  }, []);

  const load = useCallback(() => {
    if (sending) return;
    const request = isOrderChat ? getChat(orderId) : getGeneralChat();
    request
      .then((data) => {
        const nextMsgs = Array.isArray(data) ? data : [];
        if (!isOrderChat) {
          const nextActiveDraftOrderId = findActiveDraftOrderId(nextMsgs);
          if (nextActiveDraftOrderId !== activeDraftOrderId) {
            persistActiveDraftOrderId(nextActiveDraftOrderId);
          }
          if (nextActiveDraftOrderId && pendingOrderText) {
            persistPendingOrderText('');
          } else if (!nextActiveDraftOrderId && pendingOrderText) {
            const hasConfirmedDraft = nextMsgs.some((message) => {
              const lower = String(message.message || '').toLowerCase();
              return lower.includes('confirmado y enviado') || lower.includes('estado: pendiente');
            });
            if (hasConfirmedDraft) {
              persistPendingOrderText('');
            }
          }
        }
        setMessages((prev) => {
          const localPending = prev.filter(
            (m) => String(m.id).startsWith('local-') &&
                   !nextMsgs.some((msg) => msg.sender === 'user' && msg.message === m.message)
          );
          const combined = [...nextMsgs, ...localPending];
          if (combined.length > prev.length) {
            scrollToBottom();
          }
          return combined;
        });
        setErrorMessage('');
      })
      .catch(() => {
        setErrorMessage('No se pudo actualizar el chat. Revisa la conexion.');
      });
  }, [
    activeDraftOrderId,
    isOrderChat,
    orderId,
    pendingOrderText,
    persistActiveDraftOrderId,
    persistPendingOrderText,
    scrollToBottom,
    sending,
  ]);

  useEffect(() => {
    if (isOrderChat) return;
    AsyncStorage.multiGet([ACTIVE_DRAFT_ORDER_KEY, PENDING_ORDER_TEXT_KEY])
      .then((entries) => {
        const values = Object.fromEntries(entries || []);
        if (values[ACTIVE_DRAFT_ORDER_KEY]) {
          setActiveDraftOrderId(values[ACTIVE_DRAFT_ORDER_KEY]);
        }
        if (values[PENDING_ORDER_TEXT_KEY]) {
          setPendingOrderText(values[PENDING_ORDER_TEXT_KEY]);
        }
        AsyncStorage.removeItem(LEGACY_PENDING_ORDER_TEXT_KEY).catch(() => {});
      })
      .catch(() => {});
  }, [isOrderChat]);

  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';
    const showSub = Keyboard.addListener(showEvent, () => {
      setKeyboardVisible(true);
      scrollToBottom();
    });
    const hideSub = Keyboard.addListener(hideEvent, () => {
      setKeyboardVisible(false);
      scrollToBottom();
    });

    return () => {
      showSub.remove();
      hideSub.remove();
    };
  }, [scrollToBottom]);

  const sendTextMessage = useCallback(async (rawText, voiceOptions = null) => {
    const clean = String(rawText || '').trim();
    if (!clean || sending) return;
    const transportOrderId = isOrderChat ? orderId : null;
    const clearPendingContext = !isOrderChat && shouldClearPendingBeforeSend(clean);
    const contextPendingOrderText = clearPendingContext ? '' : pendingOrderText;
    const messageContext = isOrderChat ? null : {
      active_order_id: activeDraftOrderId,
      pending_order_text: contextPendingOrderText || null,
    };

    // Construir mensaje final: si es de voz, codificar como JSON
    const finalMessage = voiceOptions && voiceOptions.isVoice
      ? JSON.stringify({
          is_voice: true,
          text: clean,
          duration: Math.max(1, Math.round(voiceOptions.duration || 5))
        })
      : clean;

    const optimistic = {
      id: `local-${Date.now()}`,
      order_id: transportOrderId,
      sender: 'user',
      message: finalMessage,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimistic]);
    setText('');
    Keyboard.dismiss();
    setKeyboardVisible(false);
    setSending(true);
    setErrorMessage('');
    scrollToBottom();

    try {
      if (!isOrderChat) {
        if (clearPendingContext) {
          persistPendingOrderText('');
        }
        if (!activeDraftOrderId && shouldKeepPendingOrderText(clean)) {
          persistPendingOrderText(mergePendingOrderText(contextPendingOrderText, clean));
        }
      }

      const saved = await sendMessage({
        order_id: transportOrderId,
        message: finalMessage,
        sender: 'user',
        context: messageContext,
      });
      setMessages((prev) => prev.map((m) => (m.id === optimistic.id ? saved : m)));

      load();
    } catch (e) {
      setMessages((prev) => prev.map((m) => (m.id === optimistic.id ? { ...m, failed: true } : m)));
      setErrorMessage('El mensaje quedo pendiente. Intenta enviarlo otra vez.');
    } finally {
      setSending(false);
      scrollToBottom();
    }
  }, [
    activeDraftOrderId,
    isOrderChat,
    load,
    orderId,
    pendingOrderText,
    persistPendingOrderText,
    scrollToBottom,
    sending,
  ]);

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
        const durationSeconds = voiceStartRef.current ? Math.max(1, (Date.now() - voiceStartRef.current) / 1000) : 5;
        if (autoInterpretRef.current && transcript && !autoSendLockedRef.current) {
          autoSendLockedRef.current = true;
          setVoiceHint('Interpretando pedido...');
          sendTextMessage(transcript, { isVoice: true, duration: durationSeconds }).finally(() => {
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
    if (action.type === 'confirm_order') {
      Alert.alert(
        'Confirmar pedido',
        'El pedido pasara a Pendiente y sera enviado a AJE.',
        [
          { text: 'Cancelar', style: 'cancel' },
          {
            text: 'Confirmar',
            onPress: async () => {
              try {
                const confirmed = await confirmOrder(action.order_id);
                if (orderId === action.order_id) {
                  setOrderStatus('pendiente');
                }
                if (!isOrderChat && activeDraftOrderId === action.order_id) {
                  persistActiveDraftOrderId(null);
                  persistPendingOrderText('');
                }
                const confirmationMessage = `Pedido #${String(confirmed.id).slice(0, 8)} confirmado y enviado a AJE. Estado: Pendiente.`;
                const saved = await sendMessage({
                  order_id: isOrderChat ? orderId : null,
                  message: confirmationMessage,
                  sender: 'system',
                });
                setMessages((prev) => [...prev, saved]);
                load();
              } catch (e) {
                Alert.alert('Error', e?.message || 'No se pudo confirmar el pedido.');
              }
            },
          },
        ]
      );
      return;
    }
    if (action.type === 'orders') {
      openOrdersList(action.status);
      return;
    }
    if (action.type === 'message') {
      sendTextMessage(action.message || action.label);
    }
  }, [
    activeDraftOrderId,
    isOrderChat,
    load,
    openOrderDetail,
    openOrdersList,
    orderId,
    persistActiveDraftOrderId,
    persistPendingOrderText,
    sendTextMessage,
  ]);

  const handleFeedback = useCallback(async (message, rating) => {
    if (!message?.id || String(message.id).startsWith('intro-') || String(message.id).startsWith('local-')) return;
    const key = `${message.id}:${rating}`;
    if (feedbackPending[key]) return;

    setFeedbackPending((prev) => ({ ...prev, [key]: true }));
    try {
      const feedback = await rateChatMessage(message.id, {
        rating,
        context: {
          order_id: message.order_id || orderId,
          screen: isOrderChat ? 'order_chat' : 'general_chat',
        },
      });
      setMessages((prev) => prev.map((item) => (
        item.id === message.id ? { ...item, feedback_rating: feedback.rating } : item
      )));
    } catch (e) {
      setErrorMessage('No se pudo guardar tu evaluacion de la respuesta.');
    } finally {
      setFeedbackPending((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
  }, [feedbackPending, isOrderChat, orderId]);

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
              persistActiveDraftOrderId(null);
              persistPendingOrderText('');
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
      voiceStartRef.current = Date.now();
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
  const showCompactChat = keyboardVisible || sending;

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
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={Platform.OS === 'ios' ? Math.max(insets.top, 0) : 0}
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

        {!isOrderChat && !showCompactChat ? (
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
          keyboardDismissMode={Platform.OS === 'ios' ? 'interactive' : 'on-drag'}
          removeClippedSubviews={false}
          maintainVisibleContentPosition={{ minIndexForVisible: 0 }}
          contentContainerStyle={[
            s.listContent,
            showCompactChat && s.listContentCompact,
          ]}
          renderItem={({ item }) => {
            const isUser = item.sender === 'user';
            const canRate = !isUser && !item.failed && !String(item.id).startsWith('intro-') && !String(item.id).startsWith('local-');
            const parsed = parseMessageParts(item.message);
            return (
              <View style={[s.bubble, isUser ? s.userBubble : s.agentBubble, item.failed && s.failedBubble]}>
                {parsed.isVoice ? (
                  <VoiceNoteBubble text={parsed.voiceText} duration={parsed.voiceDuration} isUser={isUser} />
                ) : (
                  parsed.text ? <Text style={s.messageText}>{parsed.text}</Text> : null
                )}
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
                {canRate ? (
                  <View style={s.feedbackRow}>
                    {['like', 'dislike'].map((rating) => {
                      const active = item.feedback_rating === rating;
                      const icon = rating === 'like'
                        ? (active ? 'thumbs-up' : 'thumbs-up-outline')
                        : (active ? 'thumbs-down' : 'thumbs-down-outline');
                      return (
                        <TouchableOpacity
                          key={rating}
                          activeOpacity={0.8}
                          style={[s.feedbackButton, active && s.feedbackButtonActive]}
                          onPress={() => handleFeedback(item, rating)}
                          disabled={Boolean(feedbackPending[`${item.id}:${rating}`])}
                        >
                          <Ionicons name={icon} size={14} color={active ? C.white : C.muted} />
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

        {!showCompactChat ? (
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
        ) : null}

        <View
          style={[
            s.composerWrap,
            { paddingBottom: keyboardVisible ? 8 : Math.max(insets.bottom, 10) },
          ]}
        >
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
              blurOnSubmit={false}
              scrollEnabled
              textAlignVertical="top"
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
  listContentCompact: {
    paddingTop: 8,
    paddingBottom: 8,
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
    maxWidth: '82%',
    backgroundColor: C.userBubble,
    borderColor: C.userBubbleBorder,
    borderBottomRightRadius: 4,
  },
  agentBubble: {
    alignSelf: 'flex-start',
    maxWidth: '90%',
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
  feedbackRow: {
    marginTop: 8,
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  feedbackButton: {
    width: 30,
    height: 26,
    borderRadius: 13,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: 'rgba(22,16,48,0.66)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  feedbackButtonActive: {
    borderColor: C.accent,
    backgroundColor: C.accent,
  },
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
    minHeight: 48,
    maxHeight: 112,
    borderRadius: 24,
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
    height: 46,
    alignItems: 'center',
    justifyContent: 'center',
  },
  input: {
    flex: 1,
    minHeight: 46,
    maxHeight: 104,
    color: C.text,
    fontSize: 15,
    lineHeight: 20,
    paddingTop: 12,
    paddingBottom: 10,
    paddingHorizontal: 0,
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
