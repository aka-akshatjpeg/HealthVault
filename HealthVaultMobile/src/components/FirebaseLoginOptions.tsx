import React, { useEffect, useState } from 'react';
import { Alert, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { AppleAuth, AppleButton } from 'expo-apple-sign-in';
import { toFirebaseAppleCredential } from 'expo-apple-sign-in/firebase';
import {
  AppleAuthProvider, getAuth, GoogleAuthProvider, signInWithCredential, signInWithPhoneNumber,
} from '@react-native-firebase/auth';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import { authService } from '@/services/auth.service';
import { useAuthStore } from '@/store/authStore';
import { Colors } from '@/constants';

const GOOGLE_WEB_CLIENT_ID = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID || '';
const APPLE_SERVICE_ID = process.env.EXPO_PUBLIC_FIREBASE_APPLE_SERVICE_ID || '';
const APPLE_REDIRECT_URI = process.env.EXPO_PUBLIC_FIREBASE_APPLE_REDIRECT_URI || '';

export function FirebaseLoginOptions() {
  const [busy, setBusy] = useState(false);
  const [phoneOpen, setPhoneOpen] = useState(false);
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [linkExisting, setLinkExisting] = useState(false);
  const [accountEmail, setAccountEmail] = useState('');
  const [accountPassword, setAccountPassword] = useState('');
  const [confirmation, setConfirmation] = useState<any>(null);
  const [pendingIdToken, setPendingIdToken] = useState('');
  const [profileName, setProfileName] = useState('');
  const [needsProfile, setNeedsProfile] = useState(false);
  const setUser = useAuthStore((state) => state.setUser);

  useEffect(() => {
    if (GOOGLE_WEB_CLIENT_ID) GoogleSignin.configure({ webClientId: GOOGLE_WEB_CLIENT_ID });
    if (APPLE_SERVICE_ID && APPLE_REDIRECT_URI) {
      AppleAuth.configure({ clientId: APPLE_SERVICE_ID, redirectUri: APPLE_REDIRECT_URI });
    }
  }, []);

  const goToDashboard = (role: string) => {
    if (role === 'doctor') router.replace('/(doctor)/dashboard');
    else if (role === 'lab') router.replace('/(lab)/dashboard');
    else router.replace('/(patient)/dashboard');
  };

  const finishHealthVaultLogin = async (firebaseUser: any) => {
    const idToken = await firebaseUser.getIdToken(true);
    try {
      const result = await authService.firebaseLogin(idToken);
      setUser(result.user);
      goToDashboard(result.role);
    } catch (error: any) {
      if (error.response?.status === 422 && error.response?.data?.error === 'profile_required') {
        setPendingIdToken(idToken);
        setProfileName(firebaseUser.displayName || '');
        setNeedsProfile(true);
        return;
      }
      throw error;
    }
  };

  const showError = (error: any) => {
    Alert.alert('Sign-in failed', error?.response?.data?.error || error?.message || 'Please try again.');
  };

  const withBusy = async (action: () => Promise<void>) => {
    if (busy) return;
    setBusy(true);
    try { await action(); } catch (error: any) { showError(error); }
    finally { setBusy(false); }
  };

  const handleGoogle = () => withBusy(async () => {
    if (!GOOGLE_WEB_CLIENT_ID) throw new Error('Set EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID and rebuild the app.');
    await GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
    const response: any = await GoogleSignin.signIn();
    if (response?.type === 'cancelled') return;
    const idToken = response?.data?.idToken || response?.idToken;
    if (!idToken) throw new Error('Google did not return an ID token.');
    const credential = GoogleAuthProvider.credential(idToken);
    const result = await signInWithCredential(getAuth(), credential);
    await finishHealthVaultLogin(result.user);
  });

  const handleAppleSuccess = (apple: any) => withBusy(async () => {
    const { token, rawNonce } = toFirebaseAppleCredential(apple);
    const credential = AppleAuthProvider.credential(token, rawNonce);
    const result = await signInWithCredential(getAuth(), credential);
    await finishHealthVaultLogin(result.user);
  });

  const handleSendCode = () => withBusy(async () => {
    if (linkExisting && (!accountEmail.trim() || !accountPassword)) {
      throw new Error('Enter your current HealthVault email and password before verifying your phone.');
    }
    const normalizedPhone = phone.trim().replace(/[\s()-]/g, '');
    if (!/^\+[1-9]\d{7,14}$/.test(normalizedPhone)) {
      throw new Error('Enter your phone in international format, such as +91 98765 43210.');
    }
    setConfirmation(await signInWithPhoneNumber(getAuth(), normalizedPhone));
    Alert.alert('Code sent', 'Enter the verification code sent to your phone. SMS rates may apply.');
  });

  const handleVerifyCode = () => withBusy(async () => {
    if (!confirmation) throw new Error('Request a verification code first.');
    const result = await confirmation.confirm(code.trim());
    if (linkExisting) {
      const idToken = await result.user.getIdToken(true);
      const linked = await authService.linkExistingAccount(idToken, accountEmail.trim(), accountPassword);
      setAccountPassword('');
      setUser(linked.user);
      goToDashboard(linked.role);
    } else {
      await finishHealthVaultLogin(result.user);
    }
  });

  const handleCompleteProfile = () => withBusy(async () => {
    if (!pendingIdToken) throw new Error('Please sign in again to complete your profile.');
    const result = await authService.firebaseLogin(pendingIdToken, {
      full_name: profileName.trim(),
    });
    setUser(result.user);
    goToDashboard(result.role);
  });

  return (
    <View style={styles.container}>
      <View style={styles.divider}>
        <View style={styles.line} />
        <Text style={styles.dividerText}>or continue with</Text>
        <View style={styles.line} />
      </View>
      {Platform.OS === 'web' ? (
        <Text style={styles.webNote}>Use the HealthVault website to sign in with Google, Apple, or phone OTP.</Text>
      ) : (
        <>
          <TouchableOpacity style={styles.providerButton} disabled={busy} onPress={handleGoogle}>
            <Ionicons name="logo-google" size={20} color="#DB4437" />
            <Text style={styles.providerText}>Continue with Google</Text>
          </TouchableOpacity>
          <View style={styles.appleButton}>
            <AppleButton onSuccess={handleAppleSuccess} onCancel={() => {}} onError={(error: any) => showError(error)} />
          </View>
          <TouchableOpacity style={styles.phoneToggle} onPress={() => setPhoneOpen((open) => !open)}>
            <Ionicons name="phone-portrait-outline" size={19} color={Colors.primary} />
            <Text style={styles.phoneToggleText}>{phoneOpen ? 'Hide phone sign-in' : 'Sign in with phone OTP'}</Text>
          </TouchableOpacity>
          {phoneOpen && (
            <View style={styles.phonePanel}>
              <TouchableOpacity onPress={() => setLinkExisting((value) => !value)}>
                <Text style={styles.resendText}>
                  {linkExisting ? 'Create a new patient account instead' : 'Already have a HealthVault account? Link it'}
                </Text>
              </TouchableOpacity>
              {linkExisting && (
                <>
                  <TextInput value={accountEmail} onChangeText={setAccountEmail}
                    placeholder="Existing HealthVault email" autoCapitalize="none" keyboardType="email-address"
                    autoComplete="email" style={styles.input} />
                  <TextInput value={accountPassword} onChangeText={setAccountPassword}
                    placeholder="Current HealthVault password" secureTextEntry autoComplete="current-password"
                    style={styles.input} />
                  <Text style={styles.webNote}>Your password is checked by HealthVault only after Firebase verifies your phone.</Text>
                </>
              )}
              <TextInput value={phone} onChangeText={setPhone}
                placeholder="Phone number, e.g. +91 98765 43210" keyboardType="phone-pad"
                autoComplete="tel" style={styles.input} />
              {!confirmation ? (
                <TouchableOpacity style={styles.actionButton} disabled={busy} onPress={handleSendCode}>
                  <Text style={styles.actionText}>{busy ? 'Sending…' : 'Send verification code'}</Text>
                </TouchableOpacity>
              ) : (
                <>
                  <TextInput value={code} onChangeText={setCode} placeholder="6-digit verification code"
                    keyboardType="number-pad" autoComplete="one-time-code" maxLength={6} style={styles.input} />
                  <TouchableOpacity style={styles.actionButton} disabled={busy} onPress={handleVerifyCode}>
                    <Text style={styles.actionText}>{busy ? 'Verifying…' : 'Verify and sign in'}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={() => { setConfirmation(null); setCode(''); }}>
                    <Text style={styles.resendText}>Use a different phone number</Text>
                  </TouchableOpacity>
                </>
              )}
            </View>
          )}
          {needsProfile && (
            <View style={styles.phonePanel}>
              <Text style={styles.profileTitle}>Complete your patient profile</Text>
              <TextInput value={profileName} onChangeText={setProfileName} placeholder="Full name"
                autoComplete="name" style={styles.input} />
              <TouchableOpacity style={styles.actionButton} disabled={busy} onPress={handleCompleteProfile}>
                <Text style={styles.actionText}>{busy ? 'Finishing…' : 'Continue'}</Text>
              </TouchableOpacity>
            </View>
          )}
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginTop: 10 },
  divider: { flexDirection: 'row', alignItems: 'center', marginBottom: 18 },
  line: { flex: 1, height: 1, backgroundColor: Colors.border },
  dividerText: { marginHorizontal: 14, fontSize: 13, color: Colors.textMuted },
  providerButton: {
    minHeight: 50, borderWidth: 1, borderColor: Colors.border, borderRadius: 12, backgroundColor: '#fff',
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 10,
  },
  providerText: { color: Colors.text, fontSize: 14, fontWeight: '600' },
  appleButton: { height: 50, marginBottom: 10 },
  phoneToggle: { minHeight: 46, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  phoneToggleText: { color: Colors.primary, fontSize: 14, fontWeight: '600' },
  phonePanel: { backgroundColor: Colors.surfaceVariant, borderRadius: 12, padding: 14, marginTop: 12 },
  input: { minHeight: 48, borderWidth: 1, borderColor: Colors.border, borderRadius: 10, backgroundColor: '#fff', paddingHorizontal: 12, marginBottom: 10, color: Colors.text },
  actionButton: { minHeight: 48, borderRadius: 10, backgroundColor: Colors.primary, justifyContent: 'center', alignItems: 'center', marginBottom: 8 },
  actionText: { color: '#fff', fontWeight: '700' },
  resendText: { textAlign: 'center', color: Colors.primary, paddingVertical: 8, fontWeight: '600' },
  profileTitle: { fontWeight: '700', color: Colors.text, marginBottom: 10 },
  webNote: { textAlign: 'center', color: Colors.textMuted, paddingVertical: 12 },
});
