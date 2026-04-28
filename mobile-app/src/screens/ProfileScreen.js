import React from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Linking,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { COLORS } from '../utils/constants';

const ProfileScreen = ({ navigation }) => {
  const { user, isAuthenticated, logout } = useAuth();

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Apakah Anda yakin ingin logout?',
      [
        { text: 'Batal', style: 'cancel' },
        { 
          text: 'Logout', 
          style: 'destructive',
          onPress: async () => {
            await logout();
          }
        },
      ]
    );
  };

  const handleOpenWeb = () => {
    Linking.openURL('http://192.168.1.100:5003');
  };

  const MenuItem = ({ icon, title, onPress }) => (
    <TouchableOpacity style={styles.menuItem} onPress={onPress}>
      <Text style={styles.menuIcon}>{icon}</Text>
      <Text style={styles.menuTitle}>{title}</Text>
      <Text style={styles.menuArrow}>→</Text>
    </TouchableOpacity>
  );

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <Text style={styles.avatarText}>👤</Text>
        </View>
        {isAuthenticated && user ? (
          <>
            <Text style={styles.userName}>{user.username}</Text>
            <Text style={styles.userEmail}>{user.email}</Text>
          </>
        ) : (
          <Text style={styles.guestText}>Guest User</Text>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Akun</Text>
        
        <MenuItem 
          icon="📦" 
          title="Pesanan Saya" 
          onPress={() => navigation.navigate('OrdersTab')}
        />
        <MenuItem 
          icon="❤️" 
          title="Wishlist" 
          onPress={() => Alert.alert('Info', 'Fitur wishlist')}
        />
        <MenuItem 
          icon="📍" 
          title="Alamat Tersimpan" 
          onPress={() => Alert.alert('Info', 'Fitur alamat')}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Bantuan</Text>
        
        <MenuItem 
          icon="💬" 
          title="Hubungi CS" 
          onPress={() => Alert.alert('Info', 'Hubungi via Telegram atau WhatsApp')}
        />
        <MenuItem 
          icon="❓" 
          title="FAQ" 
          onPress={() => Alert.alert('Info', 'FAQ akan tersedia soon')}
        />
        <MenuItem 
          icon="📖" 
          title="Panduan Belanja" 
          onPress={() => Alert.alert('Info', 'Panduan akan tersedia')}
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Lainnya</Text>
        
        <MenuItem 
          icon="🌐" 
          title="Buka Versi Web" 
          onPress={handleOpenWeb}
        />
        <MenuItem 
          icon="ℹ️" 
          title="Tentang EntokMart" 
          onPress={() => Alert.alert('EntokMart', 'Version 1.0.0\nMarketplace untuk交易各类鸭子')}
        />
      </View>

      {isAuthenticated ? (
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutText}>🚪 Logout</Text>
        </TouchableOpacity>
      ) : (
        <TouchableOpacity 
          style={styles.loginButton} 
          onPress={() => Alert.alert('Info', 'Silakan login melalui browser')}
        >
          <Text style={styles.loginText}>Login / Register</Text>
        </TouchableOpacity>
      )}

      <View style={styles.footer}>
        <Text style={styles.footerText}>EntokMart v1.0.0</Text>
        <Text style={styles.footerText}>© 2024 EntokMart Marketplace</Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    alignItems: 'center',
    padding: 30,
    backgroundColor: COLORS.primary,
  },
  avatarContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatarText: {
    fontSize: 40,
  },
  userName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  userEmail: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 4,
  },
  guestText: {
    fontSize: 18,
    color: '#FFFFFF',
    fontWeight: '600',
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.textSecondary,
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderRadius: 12,
    marginBottom: 8,
    elevation: 1,
  },
  menuIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  menuTitle: {
    flex: 1,
    fontSize: 16,
    color: COLORS.text,
  },
  menuArrow: {
    fontSize: 18,
    color: COLORS.textSecondary,
  },
  logoutButton: {
    margin: 16,
    padding: 16,
    backgroundColor: COLORS.error,
    borderRadius: 12,
    alignItems: 'center',
  },
  logoutText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  loginButton: {
    margin: 16,
    padding: 16,
    backgroundColor: COLORS.primary,
    borderRadius: 12,
    alignItems: 'center',
  },
  loginText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    alignItems: 'center',
    padding: 20,
    marginBottom: 40,
  },
  footerText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
});

export default ProfileScreen;