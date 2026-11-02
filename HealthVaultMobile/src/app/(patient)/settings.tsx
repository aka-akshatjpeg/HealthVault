import React from 'react';
import { View, Text, ScrollView, StyleSheet, SafeAreaView, TouchableOpacity } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAuthStore } from '@/store/authStore';
import { patientService } from '@/services/patient.service';
import { LoadingScreen } from '@/components/LoadingScreen';
import { Logo } from '@/components/Logo';
import { Colors } from '@/constants';

export default function SettingsScreen() {
  const logout = useAuthStore((s) => s.logout);
  const { data, isLoading } = useQuery({ queryKey: ['settings'], queryFn: patientService.getSettings });

  if (isLoading) return <LoadingScreen message="Loading profile..." />;
  const { patient } = data || {};
  const firstName = patient?.full_name?.split(' ')[0] || 'Patient';

  const handleLogout = async () => {
    await logout();
    router.replace('/(auth)/portal-select');
  };

  const NavRow = ({ icon, label, onPress }: { icon: any, label: string, onPress?: () => void }) => (
    <TouchableOpacity style={styles.navRow} onPress={onPress}>
      <View style={styles.navIconBox}>
        <Ionicons name={icon} size={20} color={Colors.primary} />
      </View>
      <Text style={styles.navText}>{label}</Text>
      <Ionicons name="chevron-forward" size={20} color={Colors.textMuted} />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        
        {/* Top Profile Card */}
        <View style={styles.profileCard}>
          <View style={styles.avatarLarge}>
            <Text style={styles.avatarLargeText}>{firstName[0]}</Text>
          </View>
          <Text style={styles.profileName}>{patient?.full_name}</Text>
          <Text style={styles.profileId}>HV-ID: {patient?.hv_id || 'Not Assigned'}</Text>
          <TouchableOpacity style={styles.editBtn}>
            <Text style={styles.editBtnText}>Edit Profile</Text>
          </TouchableOpacity>
        </View>

        {/* Settings Sections */}
        <View style={styles.sectionBlock}>
          <Text style={styles.sectionHeader}>Account</Text>
          <View style={styles.cardBlock}>
            <NavRow icon="person-outline" label="Personal Information" />
            <NavRow icon="medkit-outline" label="Emergency Information" />
            <NavRow icon="card-outline" label="Insurance Details" />
            <NavRow icon="people-outline" label="Family Members" />
          </View>
        </View>

        <View style={styles.sectionBlock}>
          <Text style={styles.sectionHeader}>Security & Data</Text>
          <View style={styles.cardBlock}>
            <NavRow icon="time-outline" label="Access History & Audit Log" onPress={() => router.push('/(patient)/access-history')} />
            <NavRow icon="link-outline" label="Linked Accounts (Aadhaar)" />
            <NavRow icon="lock-closed-outline" label="Privacy & Security" />
          </View>
        </View>

        <View style={styles.sectionBlock}>
          <Text style={styles.sectionHeader}>Support</Text>
          <View style={styles.cardBlock}>
            <NavRow icon="help-circle-outline" label="Help & Support" />
            <NavRow icon="information-circle-outline" label="About HealthVault" />
          </View>
        </View>

        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={20} color={Colors.error} />
          <Text style={styles.logoutText}>Sign Out</Text>
        </TouchableOpacity>

        <View style={styles.branding}>
          <Logo width={100} height={80} style={{ alignSelf: 'center', opacity: 0.8 }} />
          <Text style={styles.version}>Version 1.0.0</Text>
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: 20, paddingBottom: 40 },
  profileCard: { backgroundColor: Colors.surface, borderRadius: 24, padding: 24, alignItems: 'center', marginBottom: 24, borderWidth: 1, borderColor: Colors.border, shadowColor: '#163152', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.03, shadowRadius: 10, elevation: 2 },
  avatarLarge: { width: 80, height: 80, borderRadius: 40, backgroundColor: Colors.primaryLight, alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  avatarLargeText: { color: '#fff', fontSize: 32, fontWeight: '700' },
  profileName: { fontSize: 20, fontWeight: '700', color: Colors.primary, marginBottom: 4 },
  profileId: { fontSize: 14, color: Colors.textSecondary, marginBottom: 16 },
  editBtn: { backgroundColor: Colors.surfaceVariant, paddingHorizontal: 20, paddingVertical: 10, borderRadius: 20 },
  editBtnText: { color: Colors.primary, fontWeight: '600', fontSize: 13 },
  sectionBlock: { marginBottom: 24 },
  sectionHeader: { fontSize: 13, fontWeight: '700', color: Colors.textSecondary, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8, marginLeft: 8 },
  cardBlock: { backgroundColor: Colors.surface, borderRadius: 20, borderWidth: 1, borderColor: Colors.border, overflow: 'hidden' },
  navRow: { flexDirection: 'row', alignItems: 'center', padding: 16, borderBottomWidth: 1, borderBottomColor: Colors.surfaceVariant },
  navIconBox: { width: 36, height: 36, borderRadius: 10, backgroundColor: Colors.surfaceVariant, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  navText: { flex: 1, fontSize: 15, fontWeight: '500', color: Colors.text },
  logoutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: Colors.error + '10', borderRadius: 16, padding: 16, marginTop: 8 },
  logoutText: { color: Colors.error, fontWeight: '700', fontSize: 16, marginLeft: 8 },
  branding: { marginTop: 40, alignItems: 'center' },
  version: { color: Colors.textMuted, fontSize: 12, marginTop: 4 },
});
