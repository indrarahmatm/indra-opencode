// main.dart - Flutter App for EntokMart
// Install: flutter create entokmart_app
// Add to pubspec.yaml:
//   dependencies:
//     http: ^1.1.0
//     shared_preferences: ^2.2.0
//     cached_network_image: ^3.3.0

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

const String API_URL = 'http://YOUR_SERVER_IP:5003/api/v1';

// =====================
// API SERVICE
// =====================
class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString('api_token');
  }

  Map<String, String> get headers => {
    'Content-Type': 'application/json',
    if (_token != null) 'X-API-Key': _token!,
  };

  Future<List<dynamic>> getProducts() async {
    final res = await http.get(Uri.parse('$API_URL/products'), headers: headers);
    return json.decode(res.body)['data'];
  }

  Future<List<dynamic>> getCategories() async {
    final res = await http.get(Uri.parse('$API_URL/categories'), headers: headers);
    return json.decode(res.body)['data'];
  }

  Future<List<dynamic>> getSellers() async {
    final res = await http.get(Uri.parse('$API_URL/sellers'), headers: headers);
    return json.decode(res.body)['data'];
  }

  Future<List<dynamic>> getZones() async {
    final res = await http.get(Uri.parse('$API_URL/zones'), headers: headers);
    return json.decode(res.body)['data'];
  }

  Future<Map<String, dynamic>> calculateShipping(double weight, String zoneCode) async {
    final res = await http.post(
      Uri.parse('$API_URL/calculate-shipping'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'weight': weight, 'zone_code': zoneCode}),
    );
    return json.decode(res.body)['data'];
  }
}

// =====================
// MODELS
// =====================
class Product {
  final int id;
  final String name;
  final String jenis;
  final int harga;
  final double beratKg;
  final int stok;
  final String? imageUrl;
  final Map<String, dynamic>? seller;

  Product({
    required this.id,
    required this.name,
    required this.jenis,
    required this.harga,
    required this.beratKg,
    required this.stok,
    this.imageUrl,
    this.seller,
  });

  factory Product.fromJson(Map<String, dynamic> json) => Product(
    id: json['id'],
    name: json['name'],
    jenis: json['jenis'],
    harga: json['harga'],
    beratKg: json['berat_kg']?.toDouble() ?? 0,
    stok: json['stok'],
    imageUrl: json['image_url'],
    seller: json['seller'],
  );
}

class Category {
  final int id;
  final String name;
  final String slug;

  Category({required this.id, required this.name, required this.slug});

  factory Category.fromJson(Map<String, dynamic> json) => Category(
    id: json['id'],
    name: json['name'],
    slug: json['slug'],
  );
}

// =====================
// SCREENS
// =====================

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _api = ApiService();
  List<Product> _products = [];
  bool _loading = true;
  String _search = '';

  @override
  void initState() {
    super.initState();
    loadProducts();
  }

  Future<void> loadProducts() async {
    try {
      final data = await _api.getProducts();
      setState(() {
        _products = data.map((p) => Product.fromJson(p)).toList();
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final filtered = _products.where((p) => 
      p.name.toLowerCase().contains(_search.toLowerCase())
    ).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('EntokMart'),
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              decoration: InputDecoration(
                hintText: 'Cari produk...',
                prefixIcon: const Icon(Icons.search),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              onChanged: (v) => setState(() => _search = v),
            ),
          ),
          Expanded(
            child: _loading
              ? const Center(child: CircularProgressIndicator())
              : GridView.builder(
                  padding: const EdgeInsets.all(16),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 0.7,
                    crossAxisSpacing: 10,
                    mainAxisSpacing: 10,
                  ),
                  itemCount: filtered.length,
                  itemBuilder: (ctx, i) => ProductCard(product: filtered[i]),
                ),
          ),
        ],
      ),
    );
  }
}

class ProductCard extends StatelessWidget {
  final Product product;
  const ProductCard({super.key, required this.product});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Container(
              width: double.infinity,
              color: Colors.grey[200],
              child: product.imageUrl != null
                ? Image.network(product.imageUrl!, fit: BoxFit.cover)
                : const Icon(Icons.image, size: 50, color: Colors.grey),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  product.name,
                  maxLines: 2,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 4),
                Text(
                  'Rp ${product.harga.toString().replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (m) => '${m[1]}.')}',
                  style: const TextStyle(
                    color: Color(0xFF2E7D32),
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Stok: ${product.stok}',
                  style: const TextStyle(fontSize: 12, color: Colors.grey),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class CategoriesScreen extends StatefulWidget {
  const CategoriesScreen({super.key});

  @override
  State<CategoriesScreen> createState() => _CategoriesScreenState();
}

class _CategoriesScreenState extends State<CategoriesScreen> {
  final ApiService _api = ApiService();
  List<Category> _categories = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    loadCategories();
  }

  Future<void> loadCategories() async {
    try {
      final data = await _api.getCategories();
      setState(() {
        _categories = data.map((c) => Category.fromJson(c)).toList();
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Kategori'), backgroundColor: const Color(0xFF2E7D32), foregroundColor: Colors.white),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : GridView.builder(
            padding: const EdgeInsets.all(16),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
            ),
            itemCount: _categories.length,
            itemBuilder: (ctx, i) => Card(
              child: Center(
                child: Text(
                  _categories[i].name,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ),
    );
  }
}

class CartScreen extends StatelessWidget {
  const CartScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Keranjang'), backgroundColor: const Color(0xFF2E7D32), foregroundColor: Colors.white),
      body: const Center(child: Text('Keranjang kosong')),
    );
  }
}

class OrdersScreen extends StatelessWidget {
  const OrdersScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Pesanan'), backgroundColor: const Color(0xFF2E7D32), foregroundColor: Colors.white),
      body: const Center(child: Text('Belum ada pesanan')),
    );
  }
}

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Profil'), backgroundColor: const Color(0xFF2E7D32), foregroundColor: Colors.white),
      body: const Center(child: Text('Silakan login')),
    );
  }
}

// =====================
// MAIN APP
// =====================
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiService().init();
  runApp(const EntokMartApp());
}

class EntokMartApp extends StatelessWidget {
  const EntokMartApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EntokMart',
      theme: ThemeData(
        primarySwatch: Colors.green,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2E7D32)),
      ),
      home: const MainNavigation(),
    );
  }
}

class MainNavigation extends StatefulWidget {
  const MainNavigation({super.key});

  @override
  State<MainNavigation> createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [
    const HomeScreen(),
    const CategoriesScreen(),
    const CartScreen(),
    const OrdersScreen(),
    const ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.category), label: 'Kategori'),
          NavigationDestination(icon: Icon(Icons.shopping_cart), label: 'Keranjang'),
          NavigationDestination(icon: Icon(Icons.receipt_long), label: 'Pesanan'),
          NavigationDestination(icon: Icon(Icons.person), label: 'Profil'),
        ],
      ),
    );
  }
}