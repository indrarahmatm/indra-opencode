import React from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { useCart } from '../context/CartContext';
import { COLORS, formatCurrency } from '../utils/constants';
import Button from '../components/Button';

const CartScreen = ({ navigation }) => {
  const { cartItems, removeFromCart, clearCart, getCartTotal, getCartCount, getTotalWeight } = useCart();

  const handleRemoveItem = (item) => {
    Alert.alert(
      'Hapus dari Keranjang',
      `Hapus ${item.name} dari keranjang?`,
      [
        { text: 'Batal', style: 'cancel' },
        { text: 'Hapus', style: 'destructive', onPress: () => removeFromCart(item.id) },
      ]
    );
  };

  const handleCheckout = () => {
    if (cartItems.length === 0) {
      Alert.alert('Info', 'Keranjang kosong');
      return;
    }
    // Navigate to checkout - for now just show message
    Alert.alert('Info', 'Fitur checkout akan menghubungkan ke web untuk pembayaran');
  };

  const renderItem = ({ item }) => (
    <View style={styles.cartItem}>
      <View style={styles.itemImage}>
        {item.image_url ? (
          <Text>📷</Text>
        ) : (
          <Text style={styles.imagePlaceholder}>📦</Text>
        )}
      </View>
      <View style={styles.itemInfo}>
        <Text style={styles.itemName} numberOfLines={2}>{item.name}</Text>
        <Text style={styles.itemPrice}>{formatCurrency(item.harga)}</Text>
        <Text style={styles.itemWeight}>Berat: {item.berat_kg} kg</Text>
        <View style={styles.itemFooter}>
          <Text style={styles.itemQuantity}>x{item.quantity}</Text>
          <Text style={styles.itemSubtotal}>
            {formatCurrency(item.harga * item.quantity)}
          </Text>
        </View>
      </View>
      <TouchableOpacity 
        style={styles.removeButton} 
        onPress={() => handleRemoveItem(item)}
      >
        <Text style={styles.removeButtonText}>✕</Text>
      </TouchableOpacity>
    </View>
  );

  const total = getCartTotal();
  const count = getCartCount();
  const weight = getTotalWeight();

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Keranjang</Text>
        <Text style={styles.itemCount}>{count} item</Text>
      </View>

      {cartItems.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>🛒</Text>
          <Text style={styles.emptyTitle}>Keranjang Kosong</Text>
          <Text style={styles.emptySubtitle}>
            Silakan pilih produk terlebih dahulu
          </Text>
          <Button
            title="Lihat Produk"
            onPress={() => navigation.navigate('HomeTab')}
            style={{ marginTop: 20 }}
          />
        </View>
      ) : (
        <>
          <FlatList
            data={cartItems}
            renderItem={renderItem}
            keyExtractor={item => item.id.toString()}
            contentContainerStyle={styles.list}
          />

          <View style={styles.summary}>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Subtotal ({count} item)</Text>
              <Text style={styles.summaryValue}>{formatCurrency(total)}</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Berat Total</Text>
              <Text style={styles.summaryValue}>{weight.toFixed(1)} kg</Text>
            </View>
            <View style={styles.divider} />
            <View style={styles.summaryRow}>
              <Text style={styles.totalLabel}>Total</Text>
              <Text style={styles.totalValue}>{formatCurrency(total)}</Text>
            </View>
            
            <Button
              title="Lanjut ke Pembayaran →"
              onPress={handleCheckout}
              style={styles.checkoutButton}
            />
          </View>
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: COLORS.primary,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  itemCount: {
    color: 'rgba(255,255,255,0.8)',
  },
  list: {
    padding: 16,
    paddingBottom: 200,
  },
  cartItem: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    padding: 12,
    borderRadius: 12,
    marginBottom: 12,
    elevation: 2,
  },
  itemImage: {
    width: 70,
    height: 70,
    borderRadius: 8,
    backgroundColor: COLORS.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  imagePlaceholder: {
    fontSize: 30,
  },
  itemInfo: {
    flex: 1,
    marginLeft: 12,
  },
  itemName: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  itemPrice: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  itemWeight: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  itemFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  itemQuantity: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  itemSubtotal: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  removeButton: {
    padding: 8,
  },
  removeButtonText: {
    fontSize: 18,
    color: COLORS.error,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  emptyIcon: {
    fontSize: 80,
    marginBottom: 20,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  emptySubtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 8,
    textAlign: 'center',
  },
  summary: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    elevation: 8,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  summaryValue: {
    fontSize: 14,
    color: COLORS.text,
  },
  divider: {
    height: 1,
    backgroundColor: COLORS.border,
    marginVertical: 8,
  },
  totalLabel: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  totalValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  checkoutButton: {
    marginTop: 16,
  },
});

export default CartScreen;