import React from 'react';
import {
  View, Text, ScrollView, StyleSheet, SafeAreaView,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { Colors } from '@/constants';
import { Logo } from '@/components/Logo';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { FirebaseLoginOptions } from '@/components/FirebaseLoginOptions';

/**
 * Login screen — Firebase-only.
 *
 * All authentication goes through Firebase (Phone OTP, Google, Apple).
 * The demo email/password + OTP flow has been removed.
 * The backend verifies Firebase ID tokens at POST /api/v1/auth/firebase-login.
 */
export default function LoginScreen() {
  const insets = useSafeAreaInsets();

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView
          contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + 40 }]}
          keyboardShouldPersistTaps="handled"
        >
          {/* Header */}
          <View style={styles.header}>
            <Logo width={120} height={100} />
            <Text style={styles.tagline}>YOUR HEALTH. ALWAYS WITH YOU.</Text>
          </View>

          <Text style={styles.title}>Sign In</Text>
          <Text style={styles.subtitle}>
            Use your phone number, Google, or Apple to sign in securely.
          </Text>

          <FirebaseLoginOptions />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#ffffff' },
  content: { paddingHorizontal: 24, paddingTop: 40 },
  header: { alignItems: 'center', marginBottom: 40 },
  tagline: {
    marginTop: 8, fontSize: 10, fontWeight: '700',
    color: Colors.textMuted, letterSpacing: 1.5,
  },
  title: {
    fontSize: 28, fontWeight: '800', color: Colors.primary,
    textAlign: 'center', marginBottom: 10,
  },
  subtitle: {
    fontSize: 15, color: Colors.textSecondary, textAlign: 'center',
    lineHeight: 22, marginBottom: 32, paddingHorizontal: 10,
  },
});
