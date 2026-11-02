import { View, Text, StyleSheet, SafeAreaView, TouchableOpacity } from 'react-native';
import { router } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { Colors } from '@/constants';

export default function DoctorDashboard() {
  const logout = useAuthStore((s) => s.logout);

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/portal-select');
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.icon}>🩺</Text>
        <Text style={styles.title}>Doctor Portal</Text>
        <Text style={styles.subtitle}>Coming soon — Doctor screens are being built.</Text>
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
  icon: { fontSize: 56, marginBottom: 16 },
  title: { fontSize: 22, fontWeight: 'bold', color: Colors.text, marginBottom: 10 },
  subtitle: { fontSize: 14, color: Colors.textSecondary, textAlign: 'center', lineHeight: 20, marginBottom: 32 },
  logoutBtn: { backgroundColor: '#fee2e2', borderRadius: 10, paddingVertical: 12, paddingHorizontal: 32 },
  logoutText: { color: Colors.error, fontWeight: '700' },
});
