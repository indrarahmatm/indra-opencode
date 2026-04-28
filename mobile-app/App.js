// App.js - Main Entry Point for EntokMart Mobile App
// Created with Expo

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text, View } from 'react-native';

// Providers
import { AuthProvider } from './src/context/AuthContext';
import { CartProvider } from './src/context/CartContext';

// Screens
import HomeScreen from './src/screens/HomeScreen';
import ProductDetailScreen from './src/screens/ProductDetailScreen';
import CategoriesScreen from './src/screens/CategoriesScreen';
import CartScreen from './src/screens/CartScreen';
import OrdersScreen from './src/screens/OrdersScreen';
import ProfileScreen from './src/screens/ProfileScreen';

// Utils
import { COLORS } from './src/utils/constants';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// Tab Icon Component
const TabIcon = ({ icon, label, focused }) => (
  <View style={{ alignItems: 'center', justifyContent: 'center' }}>
    <Text style={{ fontSize: 22, marginBottom: 2 }}>{icon}</Text>
    <Text style={{ 
      fontSize: 10, 
      color: focused ? COLORS.primary : COLORS.textSecondary,
      fontWeight: focused ? 'bold' : 'normal'
    }}>
      {label}
    </Text>
  </View>
);

// Home Stack Navigator
function HomeStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="HomeMain" component={HomeScreen} />
      <Stack.Screen 
        name="ProductDetail" 
        component={ProductDetailScreen}
        options={{
          headerShown: true,
          title: 'Detail Produk',
          headerStyle: { backgroundColor: COLORS.primary },
          headerTintColor: '#FFFFFF',
        }}
      />
    </Stack.Navigator>
  );
}

// Main App with Tab Navigation
function MainNavigator() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarShowLabel: false,
        tabBarStyle: {
          height: 65,
          paddingBottom: 8,
          paddingTop: 8,
          backgroundColor: '#FFFFFF',
          borderTopWidth: 1,
          borderTopColor: COLORS.border,
        },
      }}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeStack}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabIcon icon="🏠" label="Home" focused={focused} />
          ),
        }}
      />
      <Tab.Screen
        name="CategoriesTab"
        component={CategoriesScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabIcon icon="📂" label="Kategori" focused={focused} />
          ),
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="CartTab"
        component={CartScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabIcon icon="🛒" label="Keranjang" focused={focused} />
          ),
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="OrdersTab"
        component={OrdersScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabIcon icon="📦" label="Pesanan" focused={focused} />
          ),
          headerShown: false,
        }}
      />
      <Tab.Screen
        name="ProfileTab"
        component={ProfileScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabIcon icon="👤" label="Profil" focused={focused} />
          ),
          headerShown: false,
        }}
      />
    </Tab.Navigator>
  );
}

// Root App
export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <NavigationContainer>
          <StatusBar style="light" />
          <MainNavigator />
        </NavigationContainer>
      </CartProvider>
    </AuthProvider>
  );
}