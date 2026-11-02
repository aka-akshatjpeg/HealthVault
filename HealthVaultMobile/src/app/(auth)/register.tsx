import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, SafeAreaView, Alert, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/store/authStore';
import { Colors } from '@/constants';
import { Logo } from '@/components/Logo';

export default function RegisterScreen() {
  const { role } = useLocalSearchParams<{ role: string }>();
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '', phone: '', date_of_birth: '', blood_group: '', biological_sex: '' });
  const [loading, setLoading] = useState(false);
  const setUser = useAuthStore((s) => s.setUser);

  const update = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }));

  const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

  const handleRegister = async () => {
    if (!form.full_name || !form.email || !form.password) {
      Alert.alert('Required', 'Please fill in all required fields.');
      return;
    }
    setLoading(true);
    try {
      const res = await authService.register({ ...form, role: role || 'patient' });
      setUser(res.user);
      if (res.role === 'patient') router.replace('/(patient)/dashboard');
      else if (res.role === 'doctor') router.replace('/(doctor)/dashboard');
      else if (res.role === 'lab') router.replace('/(lab)/dashboard');
    } catch (err: any) {
      Alert.alert('Error', err?.response?.data?.error || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <Logo width={120} height={100} style={{ alignSelf: 'center', marginBottom: 12 }} />
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>As a {role || 'patient'}</Text>
          {[
            { key: 'full_name', label: 'Full Name *', ph: 'Your full name', cap: 'words' as const },
            { key: 'email', label: 'Email *', ph: 'you@example.com', cap: 'none' as const },
            { key: 'password', label: 'Password *', ph: 'Min 8 characters', secure: true, cap: 'none' as const },
            { key: 'confirm_password', label: 'Confirm Password *', ph: 'Re-enter password', secure: true, cap: 'none' as const },
            { key: 'phone', label: 'Phone', ph: '9876543210', cap: 'none' as const },
            { key: 'date_of_birth', label: 'Date of Birth', ph: 'YYYY-MM-DD', cap: 'none' as const },
          ].map((f) => (
            <View key={f.key}>
              <Text style={styles.label}>{f.label}</Text>
              <TextInput
                style={styles.input}
                value={(form as any)[f.key]}
                onChangeText={(v) => update(f.key, v)}
                placeholder={f.ph}
                secureTextEntry={f.secure}
                autoCapitalize={f.cap}
                keyboardType={f.key === 'phone' ? 'phone-pad' : 'default'}
              />
            </View>
          ))}
          {role === 'patient' && (
            <>
              <Text style={styles.label}>Blood Group</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 12 }}>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  {bloodGroups.map((bg) => (
                    <TouchableOpacity key={bg} style={[styles.bgChip, form.blood_group === bg && styles.bgChipActive]} onPress={() => update('blood_group', bg)}>
                      <Text style={[styles.bgChipText, form.blood_group === bg && styles.bgChipTextActive]}>{bg}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </ScrollView>
            </>
          )}
          <TouchableOpacity style={[styles.button, loading && styles.buttonDisabled]} onPress={handleRegister} disabled={loading}>
            <Text style={styles.buttonText}>{loading ? 'Creating account...' : 'Create Account'}</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { padding: 24 },
  title: { fontSize: 26, fontWeight: 'bold', color: Colors.text, marginBottom: 6 },
  subtitle: { fontSize: 14, color: Colors.textSecondary, marginBottom: 24, textTransform: 'capitalize' },
  label: { fontSize: 13, fontWeight: '600', color: Colors.text, marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: Colors.surface, borderWidth: 1.5, borderColor: Colors.border, borderRadius: 10, padding: 14, fontSize: 15, color: Colors.text },
  button: { backgroundColor: Colors.primary, borderRadius: 10, padding: 16, alignItems: 'center', marginTop: 24, marginBottom: 16 },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  bgChip: { borderWidth: 1.5, borderColor: Colors.border, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 8, backgroundColor: Colors.surface },
  bgChipActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  bgChipText: { color: Colors.text, fontWeight: '600' },
  bgChipTextActive: { color: '#fff' },
});
