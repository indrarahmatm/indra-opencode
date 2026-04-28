import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS, formatCurrency } from '../utils/constants';

const ProductCard = ({ product, onPress, onAddToCart }) => {
  return (
    <TouchableOpacity style={styles.container} onPress={onPress} activeOpacity={0.8}>
      <View style={styles.imageContainer}>
        {product.image_url ? (
          <Image source={{ uri: product.image_url }} style={styles.image} />
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderText}>📷</Text>
          </View>
        )}
        {product.stok <= 0 && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>Habis</Text>
          </View>
        )}
      </View>
      
      <View style={styles.content}>
        <Text style={styles.name} numberOfLines={2}>
          {product.name}
        </Text>
        
        <Text style={styles.category}>
          {product.jenis}
        </Text>
        
        <View style={styles.priceRow}>
          <Text style={styles.price}>
            {formatCurrency(product.harga)}
          </Text>
          <Text style={styles.weight}>
            {product.berat_kg} kg
          </Text>
        </View>
        
        <View style={styles.footer}>
          <Text style={styles.stock}>
            Stok: {product.stok}
          </Text>
          {product.seller?.nama_toko && (
            <Text style={styles.seller} numberOfLines={1}>
              🏪 {product.seller.nama_toko}
            </Text>
          )}
        </View>
        
        {onAddToCart && product.stok > 0 && (
          <TouchableOpacity 
            style={styles.addButton} 
            onPress={() => onAddToCart(product)}
          >
            <Text style={styles.addButtonText}>+ Keranjang</Text>
          </TouchableOpacity>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    margin: 6,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    overflow: 'hidden',
  },
  imageContainer: {
    position: 'relative',
  },
  image: {
    width: '100%',
    height: 140,
    resizeMode: 'cover',
  },
  placeholder: {
    width: '100%',
    height: 140,
    backgroundColor: COLORS.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 40,
  },
  badge: {
    position: 'absolute',
    top: 8,
    left: 8,
    backgroundColor: COLORS.error,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
  content: {
    padding: 10,
  },
  name: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 4,
    height: 40,
  },
  category: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginBottom: 6,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  price: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  weight: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  footer: {
    marginBottom: 8,
  },
  stock: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginBottom: 2,
  },
  seller: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
  addButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
  },
  addButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
});

export default ProductCard;