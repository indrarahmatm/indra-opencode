import React, { useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  TextInput,
} from 'react-native';
import { trackOrder } from '../services/api';
import { COLORS, formatCurrency, formatDate } from '../utils/constants';

const OrdersScreen = () => {
  const [orderId, setOrderId] = useState('');
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTrackOrder = async () => {
    if (!orderId.trim()) {
      setError('Masukkan nomor pesanan');
      return;
    }

    setLoading(true);
    setError('');
    setOrder(null);

    try {
      const result = await trackOrder(orderId, '');
      if (result.success && result.data) {
        setOrder(result.data);
      } else {
        setError(result.message || 'Pesanan tidak ditemukan');
      }
    } catch (err) {
      setError('Terjadi kesalahan');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'selesai': return COLORS.success;
      case 'dikirim': return '#2196F3';
      case 'diproses': return COLORS.warning;
      case 'pending': return COLORS.textSecondary;
      default: return COLORS.textSecondary;
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'pending': return 'Menunggu';
      case 'diproses': return 'Diproses';
      case 'dikirim': return 'Dikirim';
      case 'selesai': return 'Selesai';
      default: return status;
    }
  };

  const renderOrderDetails = () => (
    <View style={styles.orderCard}>
      <View style={styles.orderHeader}>
        <Text style={styles.orderId}>Pesanan #{order.id}</Text>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(order.status) }]}>
          <Text style={styles.statusText}>{getStatusLabel(order.status)}</Text>
        </View>
      </View>

      <View style={styles.orderInfo}>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Pembeli:</Text>
          <Text style={styles.infoValue}>{order.nama_penerima}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Total:</Text>
          <Text style={styles.infoValueTotal}>{formatCurrency(order.total_harga)}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Ongkir:</Text>
          <Text style={styles.infoValue}>{formatCurrency(order.ongkir || 0)}</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Pembayaran:</Text>
          <Text style={styles.infoValue}>{order.payment_method?.toUpperCase()}</Text>
        </View>
        {order.resi && (
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>No. Resi:</Text>
            <Text style={styles.infoValue}>{order.resi}</Text>
          </View>
        )}
      </View>

      <View style={styles.shippingInfo}>
        <Text style={styles.shippingTitle}>Alamat Pengiriman:</Text>
        <Text style={styles.shippingAddress}>{order.alamat}</Text>
        <Text style={styles.shippingPhone}>📞 {order.telp}</Text>
      </View>

      {order.items && order.items.length > 0 && (
        <View style={styles.itemsSection}>
          <Text style={styles.itemsTitle}>Item Pesanan:</Text>
          {order.items.map((item, index) => (
            <View key={index} style={styles.itemRow}>
              <Text style={styles.itemName}>• {item.name}</Text>
              <Text style={styles.itemQty}>x{item.jumlah}</Text>
              <Text style={styles.itemPrice}>{formatCurrency(item.harga * item.jumlah)}</Text>
            </View>
          ))}
        </View>
      )}

      <Text style={styles.orderDate}>
        {order.created_at ? formatDate(order.created_at) : ''}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Lacak Pesanan</Text>
      </View>

      <View style={styles.searchSection}>
        <TextInput
          style={styles.input}
          placeholder="Masukkan nomor pesanan..."
          value={orderId}
          onChangeText={setOrderId}
          keyboardType="numeric"
        />
        <TouchableOpacity 
          style={styles.searchButton}
          onPress={handleTrackOrder}
          disabled={loading}
        >
          <Text style={styles.searchButtonText}>
            {loading ? '...' : '🔍 Lacak'}
          </Text>
        </TouchableOpacity>
      </View>

      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
        </View>
      )}

      {order ? (
        renderOrderDetails()
      ) : (
        !error && (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>📦</Text>
            <Text style={styles.emptyText}>
              Masukkan nomor pesanan untuk melacak
            </Text>
          </View>
        )
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
    padding: 16,
    backgroundColor: COLORS.primary,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  searchSection: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: '#FFFFFF',
    elevation: 2,
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: 12,
    marginRight: 8,
    fontSize: 16,
  },
  searchButton: {
    backgroundColor: COLORS.primary,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    justifyContent: 'center',
  },
  searchButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  errorContainer: {
    margin: 16,
    padding: 12,
    backgroundColor: '#FFEBEE',
    borderRadius: 8,
  },
  errorText: {
    color: COLORS.error,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  emptyIcon: {
    fontSize: 60,
    marginBottom: 10,
  },
  emptyText: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  orderCard: {
    margin: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    elevation: 3,
  },
  orderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  orderId: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  statusText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  orderInfo: {
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  infoLabel: {
    color: COLORS.textSecondary,
    fontSize: 14,
  },
  infoValue: {
    color: COLORS.text,
    fontSize: 14,
  },
  infoValueTotal: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  shippingInfo: {
    padding: 12,
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    marginBottom: 16,
  },
  shippingTitle: {
    fontWeight: 'bold',
    marginBottom: 8,
  },
  shippingAddress: {
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  shippingPhone: {
    color: COLORS.primary,
  },
  itemsSection: {
    marginBottom: 16,
  },
  itemsTitle: {
    fontWeight: 'bold',
    marginBottom: 8,
  },
  itemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  itemName: {
    flex: 1,
    color: COLORS.text,
  },
  itemQty: {
    color: COLORS.textSecondary,
    marginHorizontal: 8,
  },
  itemPrice: {
    color: COLORS.text,
  },
  orderDate: {
    textAlign: 'right',
    color: COLORS.textSecondary,
    fontSize: 12,
  },
});

export default OrdersScreen;