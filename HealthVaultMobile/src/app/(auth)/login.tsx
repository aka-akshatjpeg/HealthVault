import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, SafeAreaView, Alert, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { router } from 'expo-router';
import { authService } from '@/services/auth.service';
import { describeApiError } from '@/services/networkDiagnostics';
import { useAuthStore } from '@/store/authStore';
import { Colors } from '@/constants';
import { Logo } from '@/components/Logo';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

type Tab = 'login' | 'register';

export default function UnifiedAuthScreen() {
  const [tab, setTab] = useState<Tab>('login');
  
  // Login State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  // Register State
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '' });
  
  const [loading, setLoading] = useState(false);
  
  const setPending = useAuthStore((s) => s.setPending);
  const setUser = useAuthStore((s) => s.setUser);
  const insets = useSafeAreaInsets();

  const updateForm = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }));

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Required', 'Please enter your email and password.');
      return;
    }
    setLoading(true);
    try {
      const res = await authService.login(email.trim().toLowerCase(), password);
      setPending(res.user_id, res.role);
      Alert.alert(
        'OTP Sent',
        `Demo OTP: ${res.otp_code}\n\n(In production this would be sent to your email/phone)`,
        [{ text: 'Continue', onPress: () => router.push({ pathname: '/(auth)/verify-otp', params: { userId: res.user_id } }) }]
      );
    } catch (err: any) {
      Alert.alert('Error', describeApiError(err, 'Login failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    if (!form.full_name || !form.email || !form.password) {
      Alert.alert('Required', 'Please fill in all required fields.');
      return;
    }
    if (form.password !== form.confirm_password) {
      Alert.alert('Error', 'Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      const res = await authService.register({ ...form, role: 'patient' });
      setUser(res.user);
      router.replace('/(patient)/dashboard');
    } catch (err: any) {
      Alert.alert('Error', describeApiError(err, 'Registration failed.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 40 }]} keyboardShouldPersistTaps="handled">
          
          {/* Header */}
          <View style={styles.header}>
            <Logo width={120} height={100} />
            <Text style={styles.tagline}>YOUR HEALTH. ALWAYS WITH YOU.</Text>
          </View>

          {/* Segmented Control */}
          <View style={styles.segmentContainer}>
            <TouchableOpacity 
              style={[styles.segment, tab === 'login' && styles.segmentActive]} 
              onPress={() => setTab('login')}
            >
              <Text style={[styles.segmentText, tab === 'login' && styles.segmentTextActive]}>Sign In</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.segment, tab === 'register' && styles.segmentActive]} 
              onPress={() => setTab('register')}
            >
              <Text style={[styles.segmentText, tab === 'register' && styles.segmentTextActive]}>Create Account</Text>
            </TouchableOpacity>
          </View>

          {/* Form Area */}
          <View style={styles.formContainer}>
            {tab === 'login' ? (
              // ---------------- LOGIN FORM ----------------
              <>
                <View style={styles.inputWrapper}>
                  <Ionicons name="mail-outline" size={20} color={Colors.textMuted} style={styles.inputIcon} />
                  <TextInput
                    style={styles.input} value={email} onChangeText={setEmail}
                    placeholder="Email or Phone Number" keyboardType="email-address"
                    autoCapitalize="none" autoCorrect={false} placeholderTextColor={Colors.textMuted}
                  />
                </View>

                <View style={styles.inputWrapper}>
                  <Ionicons name="lock-closed-outline" size={20} color={Colors.textMuted} style={styles.inputIcon} />
                  <TextInput
                    style={styles.input} value={password} onChangeText={setPassword}
                    placeholder="Password" secureTextEntry={!showPassword} placeholderTextColor={Colors.textMuted}
                  />
                  <TouchableOpacity style={styles.eyeIcon} onPress={() => setShowPassword(!showPassword)}>
                    <Ionicons name={showPassword ? "eye-outline" : "eye-off-outline"} size={20} color={Colors.textMuted} />
                  </TouchableOpacity>
                </View>

                <TouchableOpacity style={styles.forgotBtn}>
                  <Text style={styles.forgotText}>Forgot Password?</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.button, loading && styles.buttonDisabled]}
                  onPress={handleLogin} disabled={loading}
                >
                  <Text style={styles.buttonText}>{loading ? 'Signing in...' : 'Sign In  →'}</Text>
                </TouchableOpacity>
              </>
            ) : (
              // ---------------- REGISTER FORM ----------------
              <>
                <View style={styles.inputWrapper}>
                  <Ionicons name="person-outline" size={20} color={Colors.textMuted} style={styles.inputIcon} />
                  <TextInput
                    style={styles.input} value={form.full_name} onChangeText={(v) => updateForm('full_name', v)}
                    placeholder="Full Name" autoCapitalize="words" placeholderTextColor={Colors.textMuted}
                  />
                </View>
                <View style={styles.inputWrapper}>
                  <Ionicons name="mail-outline" size={20} color={Colors.textMuted} style={styles.inputIcon} />
                  <TextInput
                    style={styles.input} value={form.email} onChangeText={(v) => updateForm('email', v)}
                    placeholder="Email Address" keyboardType="email-address" autoCapitalize="none" placeholderTextColor={Colors.textMuted}
                  />
                </View>

                <View style={styles.inputWrapper}>
                  <Ionicons name="lock-closed-outline" size={20} color={Colors.textMuted} style={styles.inputIcon} />
                  <TextInput
                    style={styles.input} value={form.password} onChangeText={(v) => updateForm('password', v)}
                    placeholder="Create Password" secureTextEntry={!showPassword} placeholderTextColor={Colors.textMuted}
                  />
                  <TouchableOpacity style={styles.eyeIcon} onPress={() => setShowPassword(!showPassword)}>
                    <Ionicons name={showPassword ? "eye-outline" : "eye-off-outline"} size={20} color={Colors.textMuted} />
                  </TouchableOpacity>
                </View>

                <View style={styles.inputWrapper}>
                  <Ionicons name="shield-checkmark-outline" size={20} color={Colors.textMuted} style={styles.inputIcon} />
                  <TextInput
                    style={styles.input} value={form.confirm_password} onChangeText={(v) => updateForm('confirm_password', v)}
                    placeholder="Confirm Password" secureTextEntry={!showPassword} placeholderTextColor={Colors.textMuted}
                  />
                </View>

                <TouchableOpacity
                  style={[styles.button, loading && styles.buttonDisabled]}
                  onPress={handleRegister} disabled={loading}
                >
                  <Text style={styles.buttonText}>{loading ? 'Creating...' : 'Create Account  →'}</Text>
                </TouchableOpacity>
              </>
            )}

            {/* Social Login Separator */}
            <View style={styles.dividerRow}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or continue with</Text>
              <View style={styles.dividerLine} />
            </View>

            {/* Social Icons */}
            <View style={styles.socialRow}>
              <TouchableOpacity style={styles.socialBtn}>
                <Ionicons name="logo-google" size={22} color="#DB4437" />
              </TouchableOpacity>
              <TouchableOpacity style={styles.socialBtn}>
                <Ionicons name="logo-apple" size={22} color="#000" />
              </TouchableOpacity>
              <TouchableOpacity style={styles.socialBtn}>
                <Ionicons name="finger-print" size={24} color={Colors.primary} />
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#ffffff' },
  content: { paddingHorizontal: 24, paddingTop: 40 },
  header: { alignItems: 'center', marginBottom: 40 },
  tagline: { marginTop: 8, fontSize: 10, fontWeight: '700', color: Colors.textMuted, letterSpacing: 1.5 },
  segmentContainer: {
    flexDirection: 'row',
    backgroundColor: Colors.surfaceVariant,
    borderRadius: 14,
    padding: 4,
    marginBottom: 32,
  },
  segment: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 10,
  },
  segmentActive: {
    backgroundColor: '#ffffff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  segmentText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  segmentTextActive: {
    color: Colors.primary,
  },
  formContainer: {
    flex: 1,
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.surfaceVariant,
    borderRadius: 14,
    marginBottom: 16,
    paddingHorizontal: 16,
    height: 52,
  },
  inputIcon: {
    marginRight: 12,
  },
  eyeIcon: {
    padding: 4,
  },
  input: {
    flex: 1,
    fontSize: 15,
    color: Colors.text,
    height: '100%',
  },
  forgotBtn: {
    alignSelf: 'flex-end',
    marginBottom: 24,
  },
  forgotText: {
    color: Colors.textSecondary,
    fontSize: 13,
    fontWeight: '600',
  },
  button: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 32,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.border,
  },
  dividerText: {
    marginHorizontal: 16,
    fontSize: 13,
    color: Colors.textMuted,
  },
  socialRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 20,
  },
  socialBtn: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.03,
    shadowRadius: 6,
    elevation: 1,
  },
});
