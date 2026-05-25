import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';
import { setToken } from './src/services/api';

// Auth Screens
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';

// Main Screens
import StoresScreen from './src/screens/StoresScreen';
import CreateStoreScreen from './src/screens/CreateStoreScreen';
import CatalogScreen from './src/screens/CatalogScreen';
import CreateOrderScreen from './src/screens/CreateOrderScreen';
import OrderConfirmScreen from './src/screens/OrderConfirmScreen';
import OrdersScreen from './src/screens/OrdersScreen';
import OrderDetailScreen from './src/screens/OrderDetailScreen';
import ChatScreen from './src/screens/ChatScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const COLORS = {
  bg: '#0b141a',
  card: '#111b21',
  accent: '#25d366',
  text: '#eef6f7',
  muted: '#8fa4ad',
  border: '#2a3942',
};

function MainTabs() {
  return (
    <Tab.Navigator
      initialRouteName="Chat"
      screenOptions={({ route }) => ({
        headerStyle: { backgroundColor: COLORS.card },
        headerTintColor: COLORS.text,
        headerShadowVisible: false,
        tabBarStyle: {
          backgroundColor: COLORS.card,
          borderTopColor: COLORS.border,
          paddingBottom: 6,
          paddingTop: 6,
          height: 64,
        },
        tabBarActiveTintColor: COLORS.accent,
        tabBarInactiveTintColor: COLORS.muted,
        tabBarHideOnKeyboard: true,
        tabBarLabelStyle: { fontSize: 12, fontWeight: '700' },
        tabBarIcon: ({ color, size }) => {
          let iconName = 'ellipse-outline';
          if (route.name === 'Chat') {
            iconName = 'chatbubble-ellipses-outline';
          } else if (route.name === 'Pedidos') {
            iconName = 'clipboard-outline';
          } else if (route.name === 'Sucursales') {
            iconName = 'storefront-outline';
          }
          return <Ionicons name={iconName} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Chat" component={ChatScreen} options={{ tabBarLabel: 'Chat', headerShown: false }} />
      <Tab.Screen name="Pedidos" component={OrdersScreen} options={{ title: 'Pedidos', tabBarLabel: 'Pedidos' }} />
      <Tab.Screen name="Sucursales" component={StoresScreen} options={{ title: 'Sucursales', tabBarLabel: 'Sucursales' }} />
    </Tab.Navigator>
  );
}

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [userToken, setUserToken] = useState(null);

  useEffect(() => {
    AsyncStorage.getItem('token').then((t) => {
      if (t) {
        setToken(t);
        setUserToken(t);
      }
      setIsLoading(false);
    });
  }, []);

  const handleLogin = async (token) => {
    await AsyncStorage.setItem('token', token);
    setToken(token);
    setUserToken(token);
  };

  if (isLoading) return null;

  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: COLORS.card },
          headerTintColor: COLORS.text,
          headerShadowVisible: false,
          contentStyle: { backgroundColor: COLORS.bg },
        }}
      >
        {userToken == null ? (
          <>
            <Stack.Screen name="Login" options={{ headerShown: false }}>
              {(props) => <LoginScreen {...props} onLogin={handleLogin} />}
            </Stack.Screen>
            <Stack.Screen name="Register" options={{ title: 'Registro' }}>
              {(props) => <RegisterScreen {...props} onLogin={handleLogin} />}
            </Stack.Screen>
          </>
        ) : (
          <>
            <Stack.Screen name="Main" options={{ headerShown: false }}>
              {() => <MainTabs />}
            </Stack.Screen>
            <Stack.Screen name="CreateStore" component={CreateStoreScreen} options={{ title: 'Nueva Sucursal' }} />
            <Stack.Screen name="Catalog" component={CatalogScreen} options={{ title: 'Catalogo' }} />
            <Stack.Screen name="CreateOrder" component={CreateOrderScreen} options={{ title: 'Nuevo Pedido' }} />
            <Stack.Screen name="OrderConfirm" component={OrderConfirmScreen} options={{ title: 'Confirmar Pedido' }} />
            <Stack.Screen name="OrderDetail" component={OrderDetailScreen} options={{ title: 'Detalle del Pedido' }} />
            <Stack.Screen name="OrderChat" component={ChatScreen} options={{ headerShown: false }} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
