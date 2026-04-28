import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { getCategories } from '../services/api';
import { COLORS } from '../utils/constants';

const CategoriesScreen = ({ navigation }) => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const result = await getCategories();
      if (result.success) {
        setCategories(result.data || []);
      }
    } catch (error) {
      console.log('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryIcon = (name) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('bibit') || lowerName.includes('muda')) return '🐣';
    if (lowerName.includes('dewasa') || lowerName.includes('afkir')) return '🦆';
    if (lowerName.includes('telur')) return '🥚';
    if (lowerName.includes('daging')) return '🍖';
    if (lowerName.includes('pakan') || lowerName.includes('obat')) return '🌾';
    return '📦';
  };

  const renderCategory = ({ item }) => (
    <TouchableOpacity 
      style={styles.categoryCard}
      onPress={() => navigation.navigate('ProductsByCategory', { category: item })}
    >
      <View style={styles.categoryIcon}>
        <Text style={styles.iconText}>{getCategoryIcon(item.name)}</Text>
      </View>
      <View style={styles.categoryInfo}>
        <Text style={styles.categoryName}>{item.name}</Text>
        <Text style={styles.categoryDesc} numberOfLines={2}>
          {item.description || 'Lihat produk dalam kategori ini'}
        </Text>
      </View>
      <Text style={styles.arrow}>→</Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Memuat kategori...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Kategori Produk</Text>
        <Text style={styles.subtitle}>Pilih kategori untuk melihat produk</Text>
      </View>

      <FlatList
        data={categories}
        renderItem={renderCategory}
        keyExtractor={item => item.id.toString()}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>📂</Text>
            <Text style={styles.emptyText}>Belum ada kategori</Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: COLORS.textSecondary,
  },
  header: {
    padding: 16,
    backgroundColor: COLORS.primary,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  subtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 4,
  },
  list: {
    padding: 16,
  },
  categoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  categoryIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  iconText: {
    fontSize: 28,
  },
  categoryInfo: {
    flex: 1,
    marginLeft: 12,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  categoryDesc: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  arrow: {
    fontSize: 20,
    color: COLORS.textSecondary,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyIcon: {
    fontSize: 60,
    marginBottom: 10,
  },
  emptyText: {
    fontSize: 16,
    color: COLORS.textSecondary,
  },
});

export default CategoriesScreen;