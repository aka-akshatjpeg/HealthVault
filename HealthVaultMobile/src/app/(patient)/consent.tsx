import React from 'react';
import { View, Text, ScrollView, StyleSheet, SafeAreaView, TouchableOpacity, Alert, RefreshControl } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { patientService } from '@/services/patient.service';
import { LoadingScreen } from '@/components/LoadingScreen';
import { Colors } from '@/constants';

export default function ConsentScreen() {
  const qc = useQueryClient();
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['consent'],
    queryFn: patientService.getConsentRequests,
  });
  const approveMut = useMutation({
    mutationFn: ({ id, cats }: { id: string; cats: string[] }) => patientService.approveConsent(id, cats),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['consent'] }); qc.invalidateQueries({ queryKey: ['dashboard'] }); },
  });
  const denyMut = useMutation({
    mutationFn: (id: string) => patientService.denyConsent(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['consent'] }); qc.invalidateQueries({ queryKey: ['dashboard'] }); },
  });

  if (isLoading) return <LoadingScreen message="Loading consent requests..." />;
  const { pending = [], history = [] } = data || {};

  const handleApprove = (req: any) => {
    const cats: string[] = req.requested_categories;
    if (cats.length === 0) return;
    Alert.alert(
      'Approve Access',
      `Allow Dr. ${req.provider_name} to access: ${cats.join(', ')}\n\nAccess expires in ${req.duration_hours}h.`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Approve All', onPress: () => approveMut.mutate({ id: req.id, cats }), style: 'default' },
      ]
    );
  };

  const handleDeny = (req: any) => {
    Alert.alert('Deny Access', `Deny ${req.provider_name}'s request?`, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Deny', onPress: () => denyMut.mutate(req.id), style: 'destructive' },
    ]);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} refreshControl={<RefreshControl refreshing={isFetching} onRefresh={refetch} tintColor={Colors.teal} />}>
        
        {/* Pending Requests */}
        <Text style={styles.sectionHeader}>Pending Requests</Text>
        {pending.length === 0 ? <Text style={styles.empty}>No pending requests.</Text> : pending.map((req: any) => (
          <View key={req.id} style={styles.card}>
            <View style={styles.reqHeader}>
              <View style={styles.doctorAvatar}>
                <Text style={styles.doctorInitials}>{req.provider_name?.charAt(0) || 'D'}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.doctorName}>Dr. {req.provider_name}</Text>
                {req.provider_org && <Text style={styles.meta}>{req.provider_org} • {req.provider_specialty}</Text>}
              </View>
            </View>
            <View style={styles.detailBox}>
              <Text style={styles.purpose}><Text style={{ fontWeight: '600' }}>Purpose:</Text> {req.purpose}</Text>
              <Text style={styles.cats}><Text style={{ fontWeight: '600' }}>Requested:</Text> {req.requested_categories.join(', ')}</Text>
              <Text style={styles.duration}><Ionicons name="time-outline" size={14} /> Expires in {req.duration_hours}h</Text>
            </View>
            <View style={styles.btnRow}>
              <TouchableOpacity style={[styles.btn, styles.btnDeny]} onPress={() => handleDeny(req)}>
                <Text style={styles.btnDenyText}>Deny</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.btn, styles.btnApprove]} onPress={() => handleApprove(req)}>
                <Text style={styles.btnApproveText}>Approve</Text>
              </TouchableOpacity>
            </View>
          </View>
        ))}

        {/* Request History */}
        {history.length > 0 && (
          <View style={{ marginTop: 20 }}>
            <Text style={styles.sectionHeader}>History</Text>
            {history.map((req: any) => (
              <View key={req.id} style={styles.historyCard}>
                <View style={[styles.historyIcon, { backgroundColor: req.status === 'approved' ? Colors.success + '15' : Colors.error + '15' }]}>
                  <Ionicons name={req.status === 'approved' ? 'checkmark' : 'close'} size={20} color={req.status === 'approved' ? Colors.success : Colors.error} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.historyName}>Dr. {req.provider_name}</Text>
                  <Text style={styles.historyMeta}>{req.purpose}</Text>
                </View>
                <Text style={[styles.historyStatus, { color: req.status === 'approved' ? Colors.success : Colors.error }]}>
                  {req.status.toUpperCase()}
                </Text>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: 20, paddingBottom: 40 },
  sectionHeader: { fontSize: 13, fontWeight: '700', color: Colors.textSecondary, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12, marginLeft: 4 },
  empty: { color: Colors.textMuted, textAlign: 'center', marginVertical: 30, fontSize: 15 },
  card: { backgroundColor: Colors.surface, borderRadius: 24, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: Colors.border, shadowColor: '#163152', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.04, shadowRadius: 12, elevation: 2 },
  reqHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  doctorAvatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: Colors.primaryLight, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  doctorInitials: { color: '#fff', fontSize: 18, fontWeight: '700' },
  doctorName: { fontSize: 16, fontWeight: '700', color: Colors.primary, marginBottom: 4 },
  meta: { fontSize: 12, color: Colors.textSecondary },
  detailBox: { backgroundColor: Colors.surfaceVariant, padding: 14, borderRadius: 16, marginBottom: 16 },
  purpose: { fontSize: 13, color: Colors.text, marginBottom: 6, lineHeight: 18 },
  cats: { fontSize: 13, color: Colors.teal, marginBottom: 8 },
  duration: { fontSize: 12, color: Colors.textSecondary },
  btnRow: { flexDirection: 'row', gap: 12 },
  btn: { flex: 1, borderRadius: 16, paddingVertical: 14, alignItems: 'center' },
  btnDeny: { backgroundColor: Colors.error + '10' },
  btnDenyText: { color: Colors.error, fontWeight: '600', fontSize: 14 },
  btnApprove: { backgroundColor: Colors.primaryLight },
  btnApproveText: { color: '#fff', fontWeight: '600', fontSize: 14 },
  historyCard: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.surface, borderRadius: 20, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: Colors.border },
  historyIcon: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  historyName: { fontSize: 15, fontWeight: '600', color: Colors.primary, marginBottom: 4 },
  historyMeta: { fontSize: 12, color: Colors.textSecondary },
  historyStatus: { fontSize: 11, fontWeight: '700', letterSpacing: 0.5 },
});
