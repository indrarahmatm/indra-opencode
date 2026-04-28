import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { COLORS } from '../utils/constants';
import { ShippingService, PaymentService } from '../services/api';

const CheckoutScreen = ({ navigation }) => {
  const { isAuthenticated } = useAuth();
  const { cartItems, clearCart, getCartTotal } = useCart();
  
  const [loading, setLoading] = useState(false);
  const [shippingLoading, setShippingLoading] = useState(false);
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState('');
  const [shippingCost, setShippingCost] = useState(0);
  
  const [formData, setFormData] = useState({
    nama_penerima: '',
    alamat: '',
    telp: '',
    payment_method: 'cod',
  });

  const [paymentMethods, setPaymentMethods] = useState([]);
  const [midtransEnabled, setMidtransEnabled] = useState(false);
  const [midtransLoading, setMidtransLoading] = useState(false);

  useEffect(() => {
    loadZones();
    loadPaymentMethods();
  }, []);

  const loadZones = async () => {
    try {
      const response = await ShippingService.getZones();
      if (response.data.success) {
        setZones(response.data.zones);
      }
    } catch (error) {
      console.error('Error loading zones:', error);
    }
  };

  const loadPaymentMethods = async () => {
    try {
      const response = await PaymentService.getMethods();
      if (response.data.success) {
        setPaymentMethods(response.data.methods);
        setMidtransEnabled(response.data.midtrans_enabled);
      }
    } catch (error) {
      console.error('Error loading payment methods:', error);
    }
  };

  const calculateShipping = async (zoneCode) => {
    if (!zoneCode) {
      setShippingCost(0);
      return;
    }

    setShippingLoading(true);
    try {
      const totalWeight = cartItems.reduce((sum, item) => sum + (item.weight || 1) * item.quantity, 0);
      const response = await ShippingService.calculateShipping(zoneCode, totalWeight);
      
      if (response.data.success) {
        setShippingCost(response.data.cost);
      }
    } catch (error) {
      console.error('Error calculating shipping:', error);
      Alert.alert('Error', 'Gagal menghitung ongkir');
    } finally {
      setShippingLoading(false);
    }
  };

  const handleZoneChange = (zoneCode) => {
    setSelectedZone(zoneCode);
    calculateShipping(zoneCode);
  };

  const handlePaymentMethodChange = (method) => {
    setFormData({ ...formData, payment_method: method });
  };

    const handleCheckout = async () => {
    if (!isAuthenticated) {
      Alert.alert('Info', 'Silakan login untuk checkout');
      return;
    }

    const { nama_penerima, alamat, telp, payment_method } = formData;
    if (!nama_penerima || !alamat || !telp) {
      Alert.alert('Error', 'Mohon lengkapi data pengiriman');
      return;
    }

    if (!selectedZone) {
      Alert.alert('Error', 'Pilih zona pengiriman');
      return;
    }

    setLoading(true);

    try {
      // Calculate order total
      const orderTotal = getCartTotal() + shippingCost;
      
      if (payment_method === 'midtrans' && midtransEnabled) {
        // Handle Midtrans payment
        handleMidtransPayment(orderTotal);
      } else {
        // For COD or Manual Transfer, create order directly
        // In a real app, this would call an API to create the order
        Alert.alert(
          'Pesanan Diterima!',
          `Total: Rp ${orderTotal.toLocaleString('id-ID')}\nMetode: ${payment_method === 'cod' ? 'COD' : 'Transfer Bank'}\n\nPesanan akan segera diproses.`,
          [
            {
              text: 'Lihat Pesanan',
              onPress: () => {
                clearCart();
                navigation.navigate('OrdersTab');
              },
            },
            {
              text: 'Beranda',
              onPress: () => {
                clearCart();
                navigation.navigate('HomeTab');
              },
            },
          ]
        );
      }
    } catch (error) {
      console.error('Checkout error:', error);
      Alert.alert('Error', 'Gagal memproses pesanan');
    } finally {
      setLoading(false);
    }
  };

    const handleMidtransPayment = async (amount) => {
    setMidtransLoading(true);
    try {
      // Get client key first
      const clientKeyRes = await PaymentService.getClientKey();
      if (!clientKeyRes.data.success || !clientKeyRes.data.enabled) {
        Alert.alert('Error', 'Payment gateway tidak tersedia');
        setMidtransLoading(false);
        return;
      }

      // Create Snap token
      const snapRes = await PaymentService.createSnapToken(Date.now().toString(), amount);
      
      if (snapRes.data.success && snapRes.data.token) {
        // In a real app, you would open Midtrans payment page here
        // For React Native, you could use WebView or redirect to snap URL
        Alert.alert(
          'Pembayaran Midtrans',
          `Silakan selesaikan pembayaran melalui Midtrans.\nToken: ${snapRes.data.token.substring(0, 10)}...\n\nDi aplikasi nyata, ini akan membuka halaman pembayaran Midtrans.`,
          [
            {
              text: 'Bayar Nanti',
              onPress: () => {
                // Simulate successful payment after user confirmation
                Alert.alert(
                  'Pembayaran Berhasil!',
                  'Pembayaran Anda telah diproses. Terima kasih!',
                  [
                    {
                      text: 'OK',
                      onPress: () => {
                        clearCart();
                        navigation.navigate('HomeTab');
                      },
                    },
                  ]
                );
              },
            },
            {
              text: 'Batal',
              onPress: () => {
                setMidtransLoading(false);
              },
            },
          ]
        );
      } else {
        Alert.alert('Error', snapRes.data.message || 'Gagal membuat token pembayaran');
      }
    } catch (error) {
      console.error('Midtrans error:', error);
      Alert.alert('Error', 'Gagal inisiasi payment');
    } finally {
      setMidtransLoading(false);
    }
  };

  const subtotal = getCartTotal();
  const total = subtotal + shippingCost;

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📍 Data Pengiriman</Text>
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Nama Penerima</Text>
          <TextInput
            style={styles.input}
            value={formData.nama_penerima}
            onChangeText={(text) => setFormData({ ...formData, nama_penerima: text })}
            placeholder="Nama lengkap penerima"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Alamat Lengkap</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={formData.alamat}
            onChangeText={(text) => setFormData({ ...formData, alamat: text })}
            placeholder="Alamat lengkap"
            multiline
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>No. Telepon</Text>
          <TextInput
            style={styles.input}
            value={formData.telp}
            onChangeText={(text) => setFormData({ ...formData, telp: text })}
            placeholder="Nomor WhatsApp"
            keyboardType="phone-pad"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Zona Pengiriman</Text>
          <View style={styles.zoneContainer}>
            {zones.map((zone) => (
              <TouchableOpacity
                key={zone.zone_code}
                style={[
                  styles.zoneOption,
                  selectedZone === zone.zone_code && styles.zoneOptionSelected,
                ]}
                onPress={() => handleZoneChange(zone.zone_code)}
              >
                <Text
                  style={[
                    styles.zoneText,
                    selectedZone === zone.zone_code && styles.zoneTextSelected,
                  ]}
                >
                  {zone.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>💳 Metode Pembayaran</Text>
        
        <TouchableOpacity
          style={[
            styles.paymentOption,
            formData.payment_method === 'cod' && styles.paymentOptionSelected,
          ]}
          onPress={() => handlePaymentMethodChange('cod')}
        >
          <Text style={styles.paymentIcon}>💵</Text>
          <View style={styles.paymentInfo}>
            <Text style={styles.paymentTitle}>Cash on Delivery (COD)</Text>
            <Text style={styles.paymentDesc}>Bayar saat barang diterima</Text>
          </View>
          <Text style={styles.paymentCheck}>
            {formData.payment_method === 'cod' ? '✓' : ''}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.paymentOption,
            formData.payment_method === 'manual' && styles.paymentOptionSelected,
          ]}
          onPress={() => handlePaymentMethodChange('manual')}
        >
          <Text style={styles.paymentIcon}>🏦</Text>
          <View style={styles.paymentInfo}>
            <Text style={styles.paymentTitle}>Transfer Bank Manual</Text>
            <Text style={styles.paymentDesc}>Transfer ke rekening, upload bukti</Text>
          </View>
          <Text style={styles.paymentCheck}>
            {formData.payment_method === 'manual' ? '✓' : ''}
          </Text>
        </TouchableOpacity>

        {midtransEnabled && (
          <TouchableOpacity
            style={[
              styles.paymentOption,
              formData.payment_method === 'midtrans' && styles.paymentOptionSelected,
            ]}
            onPress={() => handlePaymentMethodChange('midtrans')}
          >
            <Text style={styles.paymentIcon}>💳</Text>
            <View style={styles.paymentInfo}>
              <Text style={styles.paymentTitle}>Midtrans (Kartu Kredit/VA/e-Wallet)</Text>
              <Text style={styles.paymentDesc}>Bayar instan dengan berbagai metode</Text>
            </View>
            <Text style={styles.paymentCheck}>
              {formData.payment_method === 'midtrans' ? '✓' : ''}
            </Text>
          </TouchableOpacity>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📦 Rincian Pesanan</Text>
        
        {cartItems.map((item) => (
          <View key={item.id} style={styles.cartItem}>
            <Text style={styles.itemName}>{item.name}</Text>
            <Text style={styles.itemQty}>x{item.quantity}</Text>
            <Text style={styles.itemPrice}>Rp {(item.price * item.quantity).toLocaleString('id-ID')}</Text>
          </View>
        ))}
        
        <View style={styles.summaryRow}>
          <Text>Subtotal</Text>
          <Text>Rp {subtotal.toLocaleString('id-ID')}</Text>
        </View>
        
        <View style={styles.summaryRow}>
          <Text>Ongkir {shippingLoading && '(menghitung...)'}</Text>
          <Text>Rp {shippingCost.toLocaleString('id-ID')}</Text>
        </View>
        
        <View style={styles.totalRow}>
          <Text style={styles.totalLabel}>TOTAL</Text>
          <Text style={styles.totalValue}>Rp {total.toLocaleString('id-ID')}</Text>
        </View>
      </View>

      <TouchableOpacity
        style={[styles.checkoutButton, loading && styles.buttonDisabled]}
        onPress={handleCheckout}
        disabled={loading || shippingLoading || midtransLoading}
      >
        {loading || midtransLoading ? (
          <ActivityIndicator color="#FFF" />
        ) : (
          <Text style={styles.checkoutButtonText}>Pesan Sekarang</Text>
        )}
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  section: {
    padding: 16,
    backgroundColor: '#FFF',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 16,
    color: COLORS.text,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
    color: COLORS.text,
  },
  input: {
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    backgroundColor: '#FAFAFA',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  zoneContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  zoneOption: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: '#FFF',
  },
  zoneOptionSelected: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  zoneText: {
    fontSize: 13,
    color: COLORS.text,
  },
  zoneTextSelected: {
    color: '#FFF',
    fontWeight: '600',
  },
  paymentOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 12,
    backgroundColor: '#FFF',
  },
  paymentOptionSelected: {
    borderColor: COLORS.primary,
    backgroundColor: '#E8F5E9',
  },
  paymentIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  paymentInfo: {
    flex: 1,
  },
  paymentTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  paymentDesc: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  paymentCheck: {
    fontSize: 20,
    color: COLORS.primary,
    fontWeight: 'bold',
  },
  cartItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  itemName: {
    flex: 1,
    fontSize: 14,
    color: COLORS.text,
  },
  itemQty: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginRight: 16,
  },
  itemPrice: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  totalRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderTopWidth: 2,
    borderTopColor: COLORS.primary,
    marginTop: 8,
  },
  totalLabel: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  totalValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  checkoutButton: {
    backgroundColor: COLORS.primary,
    padding: 16,
    margin: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  checkoutButtonText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default CheckoutScreen;