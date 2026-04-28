import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  RefreshControl,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { useFocusEffect } from '@react-navigation/native';
import ProductCard from '../components/ProductCard';
import { getProducts, getCategories, getFavorites, toggleFavorite } from '../services/api';
import { COLORS } from '../utils/constants';

const HomeScreen = ({ navigation }) => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [favorites, setFavorites] = useState([]);

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [])
  );

  const loadData = async () => {
    setLoading(true);
    try {
      const [productsRes, categoriesRes, favRes] = await Promise.all([
        getProducts({ search: search || undefined, category: selectedCategory || undefined }),
        getCategories(),
        getFavorites(),
      ]);

      if (productsRes.success) {
        setProducts(productsRes.data.data || []);
      }
      if (categoriesRes.success) {
        setCategories(categoriesRes.data || []);
      }
      setFavorites(favRes);
    } catch (error) {
      console.log('Load data error:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleSearch = () => {
    loadData();
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category?.slug === selectedCategory ? null : category?.slug);
    loadData();
  };

  const handleProductPress = (product) => {
    navigation.navigate('ProductDetail', { product });
  };

  const handleAddToCart = (product) => {
    // Navigate to cart or show success
    navigation.navigate('CartTab');
  };

  const handleToggleFavorite = async (productId) => {
    const result = await toggleFavorite(productId);
    if (result.success) {
      setFavorites(result.favorites);
    }
  };

  const filteredProducts = products.filter(p => 
    !selectedCategory || p.jenis?.toLowerCase().includes(selectedCategory.toLowerCase())
  );

  const renderCategoryItem = ({ item }) => {
    const isSelected = item.slug === selectedCategory;
    return (
      <TouchableOpacity
        style={[styles.categoryChip, isSelected && styles.categoryChipActive]}
        onPress={() => handleCategorySelect(item)}
      >
        <Text style={[styles.categoryText, isSelected && styles.categoryTextActive]}>
          {item.name}
        </Text>
      </TouchableOpacity>
    );
  };

  const renderProduct = ({ item }) => (
    <ProductCard
      product={item}
      onPress={() => handleProductPress(item)}
      onAddToCart={handleAddToCart}
    />
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Memuat produk...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.logo}>🐤 EntokMart</Text>
        <TouchableOpacity onPress={() => navigation.navigate('ProfileTab')}>
          <Text style={styles.profileIcon}>👤</Text>
        </TouchableOpacity>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <TextInput
            style={styles.searchInput}
            placeholder="Cari produk entok..."
            value={search}
            onChangeText={setSearch}
            onSubmitEditing={handleSearch}
            returnKeyType="search"
          />
          <TouchableOpacity style={styles.searchButton} onPress={handleSearch}>
            <Text style={styles.searchButtonText}>🔍</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Categories */}
      {categories.length > 0 && (
        <View style={styles.categoriesContainer}>
          <FlatList
            horizontal
            data={[{ id: null, name: 'Semua', slug: null }, ...categories]}
            renderItem={renderCategoryItem}
            keyExtractor={item => item.id?.toString() || 'all'}
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.categoriesList}
          />
        </View>
      )}

      {/* Products Grid */}
      <FlatList
        data={filteredProducts}
        renderItem={renderProduct}
        keyExtractor={item => item.id.toString()}
        numColumns={2}
        contentContainerStyle={styles.productList}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={[COLORS.primary]}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>📦</Text>
            <Text style={styles.emptyTitle}>Tidak ada produk</Text>
            <Text style={styles.emptySubtitle}>
              {search ? 'Coba kata kunci lain' : 'Belum ada produk tersedia'}
            </Text>
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
    marginTop: 10,
    color: COLORS.textSecondary,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 50,
    paddingBottom: 10,
    backgroundColor: COLORS.primary,
  },
  logo: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  profileIcon: {
    fontSize: 24,
  },
  searchContainer: {
    padding: 12,
    backgroundColor: COLORS.primary,
  },
  searchBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    overflow: 'hidden',
  },
  searchInput: {
    flex: 1,
    padding: 12,
    fontSize: 14,
  },
  searchButton: {
    padding: 12,
    backgroundColor: COLORS.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchButtonText: {
    fontSize: 18,
  },
  categoriesContainer: {
    backgroundColor: COLORS.background,
    paddingVertical: 8,
  },
  categoriesList: {
    paddingHorizontal: 12,
  },
  categoryChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginRight: 8,
    borderRadius: 20,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  categoryChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  categoryText: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  categoryTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  productList: {
    padding: 8,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyText: {
    fontSize: 60,
    marginBottom: 10,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  emptySubtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
});

export default HomeScreen;