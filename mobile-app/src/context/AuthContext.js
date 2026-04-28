import React, { createContext, useState, useEffect, useContext } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { STORAGE_KEYS } from '../utils/constants';
import * as api from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const { token, user: userData } = await api.getStoredAuth();
      if (token && userData) {
        setUser(userData);
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.log('Auth check error:', error);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    // For mobile app, we need to use web-based login
    // This is a placeholder - implement based on your needs
    try {
      // Check if token exists
      const { token } = await api.getStoredAuth();
      if (token) {
        setIsAuthenticated(true);
        return { success: true };
      }
      return { success: false, message: 'Silakan login melalui browser' };
    } catch (error) {
      return { success: false, message: error.message };
    }
  };

  const logout = async () => {
    try {
      await api.logout();
      setUser(null);
      setIsAuthenticated(false);
      return { success: true };
    } catch (error) {
      return { success: false, message: error.message };
    }
  };

  const updateUser = (userData) => {
    setUser(userData);
    AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(userData));
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;