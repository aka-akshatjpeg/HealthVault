import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, SafeAreaView, Alert } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { authService } from '@/services/auth.service';
import { describeApiError } from '@/services/networkDiagnostics';
import { useAuthStore } from '@/store/authStore';
import { Colors } from '@/constants';
import { Logo } from '@/components/Logo';

export default function VerifyOTPScreen() {
  const { userId } = useLocalSearchParams<{ userId: string }>();
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const setUser = useAuthStore((s) => s.setUser);
  const clearPending = useAuthStore((s) => s.clearPending);

  const handleVerify = async () => {
    if (otp.length !== 6) {
      Alert.alert('Invalid', 'Please enter the 6-digit OTP.');
      return;
    }
    setLoading(true);
    try {
      const res = await authService.verifyOtp(userId ?? '', otp);
      clearPending();
      setUser(res.user);
      if (res.role === 'patient') router.replace('/(patient)/dashboard');
      else if (res.role === 'doctor') router.replace('/(doctor)/dashboard');
      else if (res.role === 'lab') router.replace('/(lab)/dashboard');
    } catch (err: any) {
      Alert.alert('Error', describeApiError(err, 'OTP verification failed.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Logo width={120} height={100} />
          <Text style={styles.tagline}>YOUR HEALTH. ALWAYS WITH YOU.</Text>
        </View>

        <Text style={styles.title}>Verification</Text>
        <Text style={styles.subtitle}>Enter the 6-digit code sent to your registered email</Text>
        <TextInput
          style={styles.otpInput} value={otp} onChangeText={(t) => setOtp(t.replace(/\D/g, '').slice(0, 6))}
          placeholder="••••••" placeholderTextColor={Colors.textMuted} keyboardType="number-pad" maxLength={6}
          textAlign="center"
        />
        <TouchableOpacity
          style={[styles.button, (loading || otp.length < 6) && styles.buttonDisabled]}
          onPress={handleVerify} disabled={loading || otp.length < 6}
        >
          <Text style={styles.buttonText}>{loading ? 'Verifying...' : 'Verify  →'}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => router.back()} style={{ marginTop: 12 }}>
          <Text style={styles.back}>← Back to Sign In</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#ffffff' },
  content: { flex: 1, paddingHorizontal: 24, paddingTop: 40 },
  header: { alignItems: 'center', marginBottom: 40 },
  tagline: { marginTop: 8, fontSize: 10, fontWeight: '700', color: Colors.textMuted, letterSpacing: 1.5 },
  title: { fontSize: 32, fontWeight: '800', color: Colors.primary, marginBottom: 12, textAlign: 'center' },
  subtitle: { fontSize: 15, color: Colors.textSecondary, textAlign: 'center', marginBottom: 40, lineHeight: 22, paddingHorizontal: 20 },
  otpInput: {
    alignSelf: 'center',
    width: '100%',
    backgroundColor: Colors.surfaceVariant, 
    borderRadius: 16, 
    padding: 16, 
    marginBottom: 32, 
    color: Colors.text,
    fontSize: 28, 
    letterSpacing: 12,
    fontWeight: '700'
  },
  button: { 
    backgroundColor: Colors.primary, 
    borderRadius: 16, 
    height: 54, 
    justifyContent: 'center', 
    alignItems: 'center', 
    marginBottom: 16,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
  },
  buttonDisabled: { opacity: 0.6, shadowOpacity: 0 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  back: { color: Colors.textSecondary, fontSize: 15, textAlign: 'center', fontWeight: '600' },
});
