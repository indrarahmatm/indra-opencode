import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  Image,
  TouchableOpacity,
  StyleSheet,
  Alert,
  TextInput,
} from 'react-native';
import { COLORS, formatCurrency } from '../utils/constants';
import { useCart } from '../context/CartContext';
import Button from '../components/Button';

const ProductDetailScreen = ({ route, navigation }) => {
  const { product } = route.params;
  const { addToCart } = useCart();
  const [quantity, setQuantity] = useState(1);

  const handleAddToCart = async () => {
    const result = await addToCart(product, quantity);
    if (result.success) {
      Alert.alert(
        '✓ Berhasil',
        `${product.name} (${quantity}x) ditambahkan ke keranjang`,
        [
          { text: 'Lanjut Belanja', style: 'cancel' },
          { text: 'Ke Keranjang', onPress: () => navigation.navigate('CartTab') },
        ]
      );
    } else {
      Alert.alert('Error', result.message || 'Gagal menambahkan ke keranjang');
    }
  };

  const increaseQuantity = () => {
    if (quantity < product.stok) {
      setQuantity(quantity + 1);
    }
  };

  const decreaseQuantity = () => {
    if (quantity > 1) {
      setQuantity(quantity - 1);
    }
  };

  const totalPrice = product.harga * quantity;

  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Product Image */}
        <View style={styles.imageContainer}>
          {product.image_url ? (
            <Image source={{ uri: product.image_url }} style={styles.image} />
          ) : (
            <View style={styles.imagePlaceholder}>
              <Text style={styles.placeholderText}>📷</Text>
            </View>
          )}
          <TouchableOpacity 
            style={styles.backButton} 
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.backButtonText}>←</Text>
          </TouchableOpacity>
        </View>

        {/* Product Info */}
        <View style={styles.content}>
          <Text style={styles.name}>{product.name}</Text>
          
          <View style={styles.priceRow}>
            <Text style={styles.price}>{formatCurrency(product.harga)}</Text>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{product.jenis}</Text>
            </View>
          </View>

          <View style={styles.infoGrid}>
            <View style={styles.infoItem}>
              <Text style={styles.infoLabel}>Berat</Text>
              <Text style={styles.infoValue}>{product.berat_kg} kg</Text>
            </View>
            <View style={styles.infoItem}>
              <Text style={styles.infoLabel}>Stok</Text>
              <Text style={styles.infoValue}>{product.stok} pcs</Text>
            </View>
          </View>

          {/* Description */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Deskripsi</Text>
            <Text style={styles.description}>
              {product.deskripsi || 'Tidak ada deskripsi'}
            </Text>
          </View>

          {/* Seller Info */}
          {product.seller && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Informasi Toko</Text>
              <View style={styles.sellerCard}>
                <Text style={styles.sellerName}>{product.seller.nama_toko || product.seller.username}</Text>
                <Text style={styles.sellerUsername}>@{product.seller.username}</Text>
                {product.seller.no_hp && (
                  <Text style={styles.sellerPhone}>📞 {product.seller.no_hp}</Text>
                )}
              </View>
            </View>
          )}

          {/* Quantity Selector */}
          {product.stok > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Jumlah</Text>
              <View style={styles.quantityRow}>
                <TouchableOpacity 
                  style={styles.quantityButton} 
                  onPress={decreaseQuantity}
                  disabled={quantity <= 1}
                >
                  <Text style={styles.quantityButtonText}>-</Text>
                </TouchableOpacity>
                <Text style={styles.quantityValue}>{quantity}</Text>
                <TouchableOpacity 
                  style={styles.quantityButton} 
                  onPress={increaseQuantity}
                  disabled={quantity >= product.stok}
                >
                  <Text style={styles.quantityButtonText}>+</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Bottom Action Bar */}
      {product.stok > 0 && (
        <View style={styles.bottomBar}>
          <View style={styles.totalContainer}>
            <Text style={styles.totalLabel}>Total</Text>
            <Text style={styles.totalPrice}>{formatCurrency(totalPrice)}</Text>
          </View>
          <Button
            title="🛒 Tambah ke Keranjang"
            onPress={handleAddToCart}
            style={styles.addButton}
          />
        </View>
      )}

      {product.stok <= 0 && (
        <View style={styles.bottomBar}>
          <Text style={styles.outOfStockText}>Produk Habis</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  imageContainer: {
    position: 'relative',
  },
  image: {
    width: '100%',
    height: 300,
    resizeMode: 'cover',
  },
  imagePlaceholder: {
    width: '100%',
    height: 300,
    backgroundColor: COLORS.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 60,
  },
  backButton: {
    position: 'absolute',
    top: 50,
    left: 16,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  backButtonText: {
    color: '#FFFFFF',
    fontSize: 20,
  },
  content: {
    padding: 16,
  },
  name: {
    fontSize: 22,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 8,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  price: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  badge: {
    backgroundColor: COLORS.primaryLight,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  infoGrid: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  infoItem: {
    flex: 1,
    backgroundColor: COLORS.surface,
    padding: 12,
    borderRadius: 8,
    marginRight: 8,
  },
  infoLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 10,
  },
  description: {
    fontSize: 14,
    color: COLORS.textSecondary,
    lineHeight: 22,
  },
  sellerCard: {
    backgroundColor: COLORS.surface,
    padding: 16,
    borderRadius: 12,
  },
  sellerName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  sellerUsername: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  sellerPhone: {
    fontSize: 14,
    color: COLORS.primary,
    marginTop: 8,
  },
  quantityRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  quantityButton: {
    width: 40,
    height: 40,
    borderRadius: 8,
    backgroundColor: COLORS.surface,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  quantityButtonText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  quantityValue: {
    fontSize: 20,
    fontWeight: 'bold',
    marginHorizontal: 30,
    minWidth: 40,
    textAlign: 'center',
  },
  bottomBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  totalContainer: {
    flex: 1,
  },
  totalLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  totalPrice: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  addButton: {
    flex: 1.5,
    marginLeft: 16,
  },
  outOfStockText: {
    flex: 1,
    textAlign: 'center',
    color: COLORS.error,
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default ProductDetailScreen;