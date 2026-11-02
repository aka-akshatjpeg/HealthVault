import React from 'react';
import { View, Text, ScrollView, StyleSheet, SafeAreaView } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { patientService } from '@/services/patient.service';
import { LoadingScreen } from '@/components/LoadingScreen';
import { Colors } from '@/constants';

export default function LabReportDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data, isLoading } = useQuery({
    queryKey: ['lab-report', id],
    queryFn: () => patientService.getLabReport(id ?? ''),
  });
  if (isLoading) return <LoadingScreen message="Loading report..." />;
  const { report, observations } = data || {};

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        
        {/* Report Header Card */}
        <View style={styles.headerCard}>
          <View style={styles.headerIconBox}>
            <Ionicons name="flask" size={24} color={Colors.primary} />
          </View>
          <Text style={styles.reportName}>{report?.report_name}</Text>
          <Text style={styles.meta}><Ionicons name="calendar-outline" size={14} /> {report?.report_date}</Text>
          <View style={styles.providerInfo}>
            <Text style={styles.meta}><Ionicons name="business-outline" size={14} /> {report?.laboratory || 'Laboratory'}</Text>
            {report?.ordering_doctor && <Text style={styles.meta}><Ionicons name="person-outline" size={14} /> Dr. {report.ordering_doctor}</Text>}
          </View>
          {report?.summary && (
            <View style={styles.summaryBox}>
              <Text style={styles.summaryTitle}>Summary</Text>
              <Text style={styles.summary}>{report.summary}</Text>
            </View>
          )}
        </View>

        {/* Results List */}
        {observations?.length > 0 && (
          <View style={styles.resultsContainer}>
            <Text style={styles.sectionTitle}>Test Parameters</Text>
            {observations.map((o: any, idx: number) => {
              const isLast = idx === observations.length - 1;
              const isAbnormal = o.is_abnormal;
              return (
                <View key={o.id} style={[styles.obsRow, !isLast && styles.obsRowBorder, isAbnormal && styles.obsRowAbnormal]}>
                  <View style={{ flex: 1, paddingRight: 10 }}>
                    <Text style={[styles.testName, isAbnormal && { color: Colors.warning }]}>{o.test_name}</Text>
                    {o.reference_range && <Text style={styles.range}>Range: {o.reference_range}</Text>}
                  </View>
                  <View style={styles.valueCol}>
                    <Text style={[styles.value, isAbnormal && { color: Colors.warning }]}>
                      {o.value} <Text style={styles.unit}>{o.unit}</Text>
                    </Text>
                    <View style={[styles.badge, isAbnormal ? styles.badgeAbnormal : styles.badgeNormal]}>
                      <Text style={[styles.badgeText, isAbnormal ? styles.badgeTextAbnormal : styles.badgeTextNormal]}>
                        {o.interpretation ? o.interpretation.toUpperCase() : (isAbnormal ? 'ABNORMAL' : 'NORMAL')}
                      </Text>
                    </View>
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: 20, paddingBottom: 40 },
  headerCard: { backgroundColor: Colors.surface, borderRadius: 24, padding: 24, alignItems: 'center', marginBottom: 24, borderWidth: 1, borderColor: Colors.border, shadowColor: '#163152', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.04, shadowRadius: 12, elevation: 2 },
  headerIconBox: { width: 60, height: 60, borderRadius: 30, backgroundColor: Colors.surfaceVariant, alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  reportName: { fontSize: 20, fontWeight: '700', color: Colors.primary, marginBottom: 8, textAlign: 'center' },
  meta: { fontSize: 13, color: Colors.textSecondary, marginBottom: 4 },
  providerInfo: { flexDirection: 'row', justifyContent: 'center', gap: 16, marginTop: 4 },
  summaryBox: { backgroundColor: Colors.surfaceVariant, padding: 16, borderRadius: 16, marginTop: 20, width: '100%' },
  summaryTitle: { fontSize: 12, fontWeight: '700', color: Colors.primary, textTransform: 'uppercase', marginBottom: 6 },
  summary: { fontSize: 14, color: Colors.text, lineHeight: 22 },
  resultsContainer: { backgroundColor: Colors.surface, borderRadius: 24, padding: 20, borderWidth: 1, borderColor: Colors.border, shadowColor: '#163152', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.02, shadowRadius: 10, elevation: 1 },
  sectionTitle: { fontSize: 14, fontWeight: '700', color: Colors.textSecondary, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 16, marginLeft: 4 },
  obsRow: { flexDirection: 'row', paddingVertical: 14, alignItems: 'center' },
  obsRowBorder: { borderBottomWidth: 1, borderBottomColor: Colors.surfaceVariant },
  obsRowAbnormal: { backgroundColor: '#fff7ed', borderRadius: 12, paddingHorizontal: 12, marginHorizontal: -12 },
  testName: { fontSize: 15, fontWeight: '600', color: Colors.text, marginBottom: 4 },
  range: { fontSize: 12, color: Colors.textMuted },
  valueCol: { alignItems: 'flex-end', justifyContent: 'center' },
  value: { fontSize: 17, fontWeight: '700', color: Colors.text, marginBottom: 4 },
  unit: { fontSize: 13, fontWeight: '500', color: Colors.textSecondary },
  badge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6 },
  badgeNormal: { backgroundColor: Colors.success + '15' },
  badgeAbnormal: { backgroundColor: Colors.warning + '15' },
  badgeText: { fontSize: 10, fontWeight: '700' },
  badgeTextNormal: { color: Colors.success },
  badgeTextAbnormal: { color: Colors.warning },
});
