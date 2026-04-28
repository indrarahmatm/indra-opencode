import React, { createContext, useState, useEffect, useContext } from 'react';
import { getCart, addToCart as apiAddToCart, removeFromCart as apiRemoveFromCart, clearCart as apiClearCart } from '../services/api';

const CartContext = createContext();

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCart();
  }, []);

  const loadCart = async () => {
    try {
      const items = await getCart();
      setCartItems(items);
    } catch (error) {
      console.log('Load cart error:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (product, quantity = 1) => {
    try {
      const result = await apiAddToCart(product, quantity);
      if (result.success) {
        setCartItems(result.cart);
        return { success: true };
      }
      return result;
    } catch (error) {
      return { success: false, message: error.message };
    }
  };

  const removeFromCart = async (productId) => {
    try {
      const result = await apiRemoveFromCart(productId);
      if (result.success) {
        setCartItems(result.cart);
        return { success: true };
      }
      return result;
    } catch (error) {
      return { success: false, message: error.message };
    }
  };

  const clearCart = async () => {
    try {
      await apiClearCart();
      setCartItems([]);
      return { success: true };
    } catch (error) {
      return { success: false, message: error.message };
    }
  };

  const getCartTotal = () => {
    return cartItems.reduce((total, item) => total + (item.harga * item.quantity), 0);
  };

  const getCartCount = () => {
    return cartItems.reduce((total, item) => total + item.quantity, 0);
  };

  const getTotalWeight = () => {
    return cartItems.reduce((total, item) => total + ((item.berat_kg || 0) * item.quantity), 0);
  };

  const value = {
    cartItems,
    loading,
    addToCart,
    removeFromCart,
    clearCart,
    getCartTotal,
    getCartCount,
    getTotalWeight,
    refreshCart: loadCart,
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export default CartContext;