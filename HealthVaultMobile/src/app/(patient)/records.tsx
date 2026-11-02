import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, TouchableOpacity, SafeAreaView, RefreshControl } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { patientService } from '@/services/patient.service';
import { LoadingScreen } from '@/components/LoadingScreen';
import { Colors } from '@/constants';

const TABS = ['Lab Reports', 'Medications', 'Conditions', 'Allergies', 'Vaccinations', 'Procedures'] as const;
type Tab = typeof TABS[number];

export default function RecordsScreen() {
  const { tab } = useLocalSearchParams<{ tab: string }>();
  const [activeTab, setActiveTab] = useState<Tab>((tab as Tab) || 'Lab Reports');

  useEffect(() => {
    if (tab && TABS.includes(tab as Tab)) {
      setActiveTab(tab as Tab);
    }
  }, [tab]);

  const labQ = useQuery({ queryKey: ['lab-reports'], queryFn: patientService.getLabReports, enabled: activeTab === 'Lab Reports' });
  const medQ = useQuery({ queryKey: ['medications'], queryFn: patientService.getMedications, enabled: activeTab === 'Medications' });
  const conQ = useQuery({ queryKey: ['conditions'], queryFn: patientService.getConditions, enabled: activeTab === 'Conditions' });
  const algQ = useQuery({ queryKey: ['allergies'], queryFn: patientService.getAllergies, enabled: activeTab === 'Allergies' });
  const vacQ = useQuery({ queryKey: ['vaccinations'], queryFn: patientService.getVaccinations, enabled: activeTab === 'Vaccinations' });
  const proQ = useQuery({ queryKey: ['procedures'], queryFn: patientService.getProcedures, enabled: activeTab === 'Procedures' });

  const queries: Record<Tab, any> = {
    'Lab Reports': labQ, 'Medications': medQ, 'Conditions': conQ, 'Allergies': algQ, 'Vaccinations': vacQ, 'Procedures': proQ,
  };
  const active = queries[activeTab];

  const renderContent = () => {
    if (active.isLoading) return <LoadingScreen message={`Loading ${activeTab}...`} />;
    if (active.error) return <Text style={styles.empty}>Failed to load. Pull to refresh.</Text>;

    if (activeTab === 'Lab Reports') {
      const reports = active.data?.reports || [];
      if (!reports.length) return <Text style={styles.empty}>No lab reports yet.</Text>;
      return reports.map((r: any) => (
        <TouchableOpacity key={r.id} onPress={() => router.push({ pathname: '/(patient)/lab-report', params: { id: r.id } })}>
          <View style={styles.card}>
            <View style={[styles.iconBox, { backgroundColor: Colors.info + '15' }]}>
              <Ionicons name="document-text" size={24} color={Colors.info} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.itemTitle}>{r.report_name}</Text>
              <Text style={styles.itemMeta}>{r.report_date} • {r.laboratory}</Text>
            </View>
            {r.abnormal_count > 0 && <View style={styles.badge}><Text style={styles.badgeText}>{r.abnormal_count} ⚠</Text></View>}
            <Ionicons name="chevron-forward" size={20} color={Colors.textMuted} style={{ marginLeft: 8 }} />
          </View>
        </TouchableOpacity>
      ));
    }
    if (activeTab === 'Medications') {
      const { active: meds = [], past = [] } = active.data || {};
      if (!meds.length && !past.length) return <Text style={styles.empty}>No medications recorded.</Text>;
      return [
        meds.length > 0 && <Text key="ah" style={styles.groupLabel}>Current</Text>,
        ...meds.map((m: any) => (
          <View key={m.id} style={styles.card}>
            <View style={[styles.iconBox, { backgroundColor: Colors.success + '15' }]}>
              <Ionicons name="medical" size={24} color={Colors.success} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.itemTitle}>{m.medicine_name} {m.dosage}</Text>
              <Text style={styles.itemMeta}>{m.frequency}</Text>
            </View>
          </View>
        )),
        past.length > 0 && <Text key="ph" style={styles.groupLabel}>Past</Text>,
        ...past.map((m: any) => (
          <View key={m.id} style={[styles.card, { opacity: 0.7 }]}>
            <View style={[styles.iconBox, { backgroundColor: Colors.textMuted + '20' }]}>
              <Ionicons name="medical" size={24} color={Colors.textMuted} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[styles.itemTitle, { color: Colors.textSecondary }]}>{m.medicine_name} {m.dosage}</Text>
              <Text style={styles.itemMeta}>Ended {m.end_date || '—'}</Text>
            </View>
          </View>
        )),
      ];
    }
    if (activeTab === 'Conditions') {
      const conditions = active.data?.conditions || [];
      if (!conditions.length) return <Text style={styles.empty}>No ongoing or previous conditions recorded.</Text>;
      return conditions.map((c: any) => (
        <View key={c.id} style={styles.card}>
          <View style={[styles.iconBox, { backgroundColor: Colors.primary + '15' }]}>
            <Ionicons name="fitness" size={24} color={Colors.primary} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.itemTitle}>{c.condition_name}</Text>
            <Text style={styles.itemMeta}>{c.severity ? `Severity: ${c.severity}` : ''} {c.diagnosis_date ? `• Diagnosed: ${c.diagnosis_date}` : ''}</Text>
          </View>
          <View style={[styles.badge, { backgroundColor: c.status === 'active' ? Colors.success + '15' : Colors.surfaceVariant }]}>
            <Text style={[styles.badgeText, { color: c.status === 'active' ? Colors.success : Colors.textMuted }]}>{c.status}</Text>
          </View>
        </View>
      ));
    }
    if (activeTab === 'Allergies') {
      const allergies = active.data?.allergies || [];
      if (!allergies.length) return <Text style={styles.empty}>No allergies recorded.</Text>;
      const severityColors: Record<string, string> = { 'life-threatening': Colors.error, severe: Colors.warning, moderate: Colors.warning, mild: Colors.success };
      return allergies.map((a: any) => (
        <View key={a.id} style={styles.card}>
          <View style={[styles.iconBox, { backgroundColor: Colors.error + '15' }]}>
            <Ionicons name="warning" size={24} color={Colors.error} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.itemTitle}>{a.allergen}</Text>
            {a.reaction && <Text style={styles.itemMeta}>Reaction: {a.reaction}</Text>}
          </View>
          {a.severity && <View style={[styles.badge, { backgroundColor: Colors.error + '15' }]}><Text style={[styles.badgeText, { color: severityColors[a.severity] || Colors.error }]}>{a.severity}</Text></View>}
        </View>
      ));
    }
    if (activeTab === 'Vaccinations') {
      const imms = active.data?.immunizations || [];
      if (!imms.length) return <Text style={styles.empty}>No vaccinations recorded.</Text>;
      return imms.map((i: any) => (
        <View key={i.id} style={styles.card}>
          <View style={[styles.iconBox, { backgroundColor: Colors.teal + '15' }]}>
            <Ionicons name="shield-checkmark" size={24} color={Colors.teal} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.itemTitle}>{i.vaccine_name} {i.dose_number || ''}</Text>
            <Text style={styles.itemMeta}>{i.vaccination_date} • {i.provider || 'Unknown provider'}</Text>
            {i.next_dose_date && <Text style={[styles.itemMeta, { color: Colors.teal, fontWeight: '500', marginTop: 2 }]}>Next dose: {i.next_dose_date}</Text>}
          </View>
        </View>
      ));
    }
    if (activeTab === 'Procedures') {
      const procedures = active.data?.procedures || [];
      if (!procedures.length) return <Text style={styles.empty}>No previous surgeries or procedures recorded.</Text>;
      return procedures.map((p: any) => (
        <View key={p.id} style={styles.card}>
          <View style={[styles.iconBox, { backgroundColor: Colors.warning + '15' }]}>
            <Ionicons name="body" size={24} color={Colors.warning} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.itemTitle}>{p.procedure_name}</Text>
            <Text style={styles.itemMeta}>{p.procedure_date} • {p.hospital || 'Unknown facility'}</Text>
            {p.surgeon && <Text style={styles.itemMeta}>Surgeon: Dr. {p.surgeon}</Text>}
            {p.outcome && <Text style={[styles.itemMeta, { color: Colors.primary, fontWeight: '500', marginTop: 2 }]}>{p.outcome}</Text>}
          </View>
        </View>
      ));
    }
    return null;
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabBar} contentContainerStyle={styles.tabBarContent}>
        {TABS.map((tab) => (
          <TouchableOpacity key={tab} style={[styles.tab, activeTab === tab && styles.tabActive]} onPress={() => setActiveTab(tab)}>
            <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>{tab === 'Procedures' ? 'Surgeries & Procedures' : tab}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      <ScrollView contentContainerStyle={styles.scroll} refreshControl={<RefreshControl refreshing={active.isFetching} onRefresh={active.refetch} tintColor={Colors.teal} />}>
        {renderContent()}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  tabBar: { flexGrow: 0, backgroundColor: Colors.surface, borderBottomWidth: 1, borderBottomColor: Colors.border },
  tabBarContent: { paddingHorizontal: 16, paddingVertical: 12, gap: 10 },
  tab: { paddingHorizontal: 18, paddingVertical: 10, borderRadius: 24, backgroundColor: Colors.background },
  tabActive: { backgroundColor: Colors.teal },
  tabText: { fontSize: 13, color: Colors.textSecondary, fontWeight: '600' },
  tabTextActive: { color: '#fff' },
  scroll: { padding: 16, paddingBottom: 40 },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.surface, borderRadius: 20, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: Colors.border, shadowColor: '#163152', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.04, shadowRadius: 12, elevation: 2 },
  iconBox: { width: 48, height: 48, borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  itemTitle: { fontSize: 16, fontWeight: '700', color: Colors.primary, marginBottom: 4 },
  itemMeta: { fontSize: 13, color: Colors.textSecondary },
  empty: { textAlign: 'center', color: Colors.textMuted, marginTop: 40, fontSize: 15 },
  badge: { borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4 },
  badgeText: { fontSize: 12, fontWeight: '700' },
  groupLabel: { fontSize: 14, fontWeight: '700', color: Colors.primary, marginBottom: 12, marginTop: 8 },
});
