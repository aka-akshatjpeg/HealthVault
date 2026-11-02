import React from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, RefreshControl, TextInput, Platform } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery } from '@tanstack/react-query';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { patientService } from '@/services/patient.service';
import { LoadingScreen } from '@/components/LoadingScreen';
import { ErrorView } from '@/components/ErrorView';
import { Colors } from '@/constants';

export default function DashboardScreen() {
  const insets = useSafeAreaInsets();
  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ['dashboard'],
    queryFn: patientService.getDashboard,
  });

  if (isLoading) return <LoadingScreen message="Loading dashboard..." />;
  if (error) return <ErrorView message="Could not load dashboard." onRetry={refetch} />;

  const { patient, stats, recent_reports, recent_encounters } = data!;
  const firstName = patient.full_name?.split(' ')[0] || 'Patient';

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        contentContainerStyle={[styles.scroll, { paddingBottom: insets.bottom + 120 }]}
        refreshControl={<RefreshControl refreshing={isFetching} onRefresh={refetch} tintColor={Colors.teal} />}
        showsVerticalScrollIndicator={false}
      >
        {/* Header Section */}
        <View style={styles.headerRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.greeting}>Good Morning, {firstName} 👋</Text>
            <Text style={styles.subtitle}>Your health journey, organized, secure and always with you.</Text>
          </View>
          <View style={styles.headerIcons}>
            <TouchableOpacity onPress={() => router.push('/(patient)/notifications')} style={styles.iconBtn}>
              <Ionicons name="notifications-outline" size={22} color={Colors.text} />
              {stats.unread_notifications > 0 && <View style={styles.badge} />}
            </TouchableOpacity>
            <TouchableOpacity onPress={() => router.push('/(patient)/settings')} style={styles.avatar}>
              <Text style={styles.avatarText}>{firstName[0]}</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <View style={styles.searchInputWrapper}>
            <Ionicons name="search-outline" size={20} color={Colors.textMuted} style={styles.searchIcon} />
            <TextInput
              style={styles.searchInput}
              placeholder="Search reports, doctors..."
              placeholderTextColor={Colors.textMuted}
              readOnly
            />
          </View>
          <TouchableOpacity style={styles.filterBtn}>
            <Ionicons name="options-outline" size={22} color={Colors.surface} />
          </TouchableOpacity>
        </View>

        {/* Quick Actions */}
        <View style={[styles.quickRow, { flexWrap: 'wrap', rowGap: 24 }]}>
          <QuickAction icon="document-text" label="Reports" path={{ pathname: '/(patient)/records', params: { tab: 'Lab Reports' } }} color={Colors.info} />
          <QuickAction icon="calendar" label="Timeline" path="/(patient)/timeline" color={Colors.warning} />
          <QuickAction icon="medical" label="Medications" path={{ pathname: '/(patient)/records', params: { tab: 'Medications' } }} color={Colors.success} />
          <QuickAction icon="shield-checkmark" label="Vaccines" path={{ pathname: '/(patient)/records', params: { tab: 'Vaccinations' } }} color={Colors.teal} />
          <QuickAction icon="fitness" label="Conditions" path={{ pathname: '/(patient)/records', params: { tab: 'Conditions' } }} color={Colors.primary} />
          <QuickAction icon="warning" label="Allergies" path={{ pathname: '/(patient)/records', params: { tab: 'Allergies' } }} color={Colors.error} />
          <QuickAction icon="body" label="Surgeries & Procedures" path={{ pathname: '/(patient)/records', params: { tab: 'Procedures' } }} color={Colors.warning} />
          <View style={{ width: '23%' }} />
        </View>

        {/* Upcoming Schedule / Encounters */}
        {recent_encounters?.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Recent Encounters</Text>
              <TouchableOpacity><Text style={styles.seeAll}>See All</Text></TouchableOpacity>
            </View>
            <View style={styles.scheduleCard}>
              <View style={styles.scheduleTop}>
                <View style={styles.doctorAvatar}>
                  <Text style={styles.doctorInitials}>{recent_encounters[0].doctor_name?.[0] || 'D'}</Text>
                </View>
                <View style={styles.doctorInfo}>
                  <Text style={styles.doctorName} numberOfLines={1}>{recent_encounters[0].doctor_name}</Text>
                  <Text style={styles.doctorSpecialty} numberOfLines={1}>{recent_encounters[0].specialty || 'Consultation'}</Text>
                </View>
              </View>
              <View style={styles.scheduleBottom}>
                <View style={styles.timeInfo}>
                  <Ionicons name="calendar-outline" size={16} color="rgba(255,255,255,0.8)" />
                  <Text style={styles.timeText}>{recent_encounters[0].encounter_date}</Text>
                </View>
                <TouchableOpacity style={styles.detailBtn}>
                  <Text style={styles.detailBtnText}>See Detail</Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}

        {/* Recent Reports */}
        {recent_reports?.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Recent Lab Reports</Text>
              <TouchableOpacity onPress={() => router.push('/(patient)/records')}><Text style={styles.seeAll}>See All</Text></TouchableOpacity>
            </View>
            {recent_reports.map((r: any) => (
              <View key={r.id} style={styles.recordCard}>
                <View style={[styles.recordIconBox, { backgroundColor: Colors.surfaceVariant }]}>
                  <Ionicons name="flask" size={24} color={Colors.teal} />
                </View>
                <View style={styles.recordInfo}>
                  <Text style={styles.recordName} numberOfLines={1}>{r.report_name}</Text>
                  <Text style={styles.recordMeta} numberOfLines={1}>{r.report_date} • {r.laboratory}</Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={Colors.textMuted} />
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function QuickAction({ icon, label, path, color }: { icon: any; label: string; path: any; color: string }) {
  return (
    <TouchableOpacity style={styles.quickBtn} onPress={() => router.push(path)}>
      <View style={[styles.iconCircle, { backgroundColor: color + '15' }]}>
        <Ionicons name={icon} size={26} color={color} />
      </View>
      <Text style={styles.quickLabel} numberOfLines={2}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: 20 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28, marginTop: 10 },
  greeting: { fontSize: 24, fontWeight: '700', color: Colors.primary, marginBottom: 6 },
  subtitle: { fontSize: 14, color: Colors.textSecondary, lineHeight: 20, paddingRight: 20 },
  headerIcons: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconBtn: { padding: 10, backgroundColor: Colors.surface, borderRadius: 24, borderWidth: 1, borderColor: Colors.border },
  badge: { position: 'absolute', top: 10, right: 10, width: 8, height: 8, borderRadius: 4, backgroundColor: Colors.error },
  avatar: { width: 46, height: 46, borderRadius: 23, backgroundColor: Colors.primaryLight, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: '#fff', fontSize: 18, fontWeight: '700' },
  searchContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 32, gap: 12 },
  searchInputWrapper: { flex: 1, justifyContent: 'center' },
  searchInput: { backgroundColor: Colors.surface, borderRadius: 16, paddingVertical: Platform.OS === 'ios' ? 16 : 14, paddingLeft: 46, paddingRight: 16, fontSize: 15, color: Colors.text, borderWidth: 1, borderColor: Colors.border },
  searchIcon: { position: 'absolute', left: 16, zIndex: 1 },
  filterBtn: { backgroundColor: Colors.teal, padding: 14, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  quickRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 },
  quickBtn: { alignItems: 'center', width: '23%' },
  iconCircle: { width: 64, height: 64, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginBottom: 10 },
  quickLabel: { fontSize: 13, fontWeight: '600', color: Colors.textSecondary, textAlign: 'center' },
  section: { marginBottom: 32 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: Colors.primary },
  seeAll: { fontSize: 15, fontWeight: '600', color: Colors.teal },
  scheduleCard: { backgroundColor: Colors.teal, borderRadius: 24, padding: 20, shadowColor: Colors.teal, shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.2, shadowRadius: 12, elevation: 5 },
  scheduleTop: { flexDirection: 'row', alignItems: 'center', marginBottom: 20, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.15)', paddingBottom: 16 },
  doctorAvatar: { width: 50, height: 50, borderRadius: 25, backgroundColor: 'rgba(255,255,255,0.2)', alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  doctorInitials: { color: '#fff', fontSize: 18, fontWeight: '700' },
  doctorInfo: { flex: 1 },
  doctorName: { color: '#fff', fontSize: 17, fontWeight: '700', marginBottom: 4 },
  doctorSpecialty: { color: 'rgba(255,255,255,0.8)', fontSize: 14 },
  scheduleBottom: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  timeInfo: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  timeText: { color: '#fff', fontSize: 14, fontWeight: '500' },
  detailBtn: { backgroundColor: '#fff', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 20 },
  detailBtnText: { color: Colors.teal, fontSize: 14, fontWeight: '700' },
  recordCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.surface, borderRadius: 20, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: Colors.border },
  recordIconBox: { width: 50, height: 50, borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  recordInfo: { flex: 1, paddingRight: 10 },
  recordName: { fontSize: 16, fontWeight: '700', color: Colors.primary, marginBottom: 4 },
  recordMeta: { fontSize: 14, color: Colors.textSecondary },
});
