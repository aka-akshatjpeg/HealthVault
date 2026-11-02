import React from 'react';
import { View, Text, ScrollView, StyleSheet, SafeAreaView, RefreshControl } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { patientService } from '@/services/patient.service';
import { Card } from '@/components/Card';
import { LoadingScreen } from '@/components/LoadingScreen';
import { Colors } from '@/constants';

export default function AccessHistoryScreen() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['access-history'],
    queryFn: patientService.getAccessHistory,
  });
  if (isLoading) return <LoadingScreen message="Loading access history..." />;
  const { audit_events = [], access_requests = [] } = data || {};

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll} refreshControl={<RefreshControl refreshing={isFetching} onRefresh={() => { void refetch(); }} tintColor={Colors.primary} />}>
        <Text style={styles.section}>Access Requests</Text>
        {access_requests.length === 0 ? <Text style={styles.empty}>No access requests yet.</Text> :
          access_requests.map((r: any) => (
            <Card key={r.id}>
              <View style={styles.row}>
                <Text style={styles.actor}>{r.provider_name}</Text>
                <View style={[styles.badge, { backgroundColor: r.status === 'approved' ? '#dcfce7' : r.status === 'denied' || r.status === 'revoked' ? '#fee2e2' : '#f1f5f9' }]}>
                  <Text style={[styles.badgeText, { color: r.status === 'approved' ? Colors.success : r.status === 'denied' || r.status === 'revoked' ? Colors.error : Colors.textMuted }]}>{r.status}</Text>
                </View>
              </View>
              <Text style={styles.meta}>{r.purpose}</Text>
              {r.approved_categories?.length > 0 && <Text style={styles.cats}>{r.approved_categories.join(', ')}</Text>}
            </Card>
          ))
        }
        <Text style={styles.section}>Audit Log ({audit_events.length})</Text>
        {audit_events.map((e: any) => (
          <Card key={e.id}>
            <View style={styles.row}>
              <Text style={styles.actor}>{e.actor_name}</Text>
              <Text style={styles.action}>{e.action}</Text>
            </View>
            <Text style={styles.meta}>{e.resource_type}{e.resource_description ? ` • ${e.resource_description}` : ''}</Text>
            {e.actor_organization && <Text style={styles.org}>{e.actor_organization}</Text>}
            <Text style={styles.time}>{new Date(e.timestamp).toLocaleString('en-IN')}</Text>
          </Card>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: 16 },
  section: { fontSize: 16, fontWeight: '700', color: Colors.text, marginBottom: 10, marginTop: 6 },
  empty: { color: Colors.textMuted, textAlign: 'center', marginVertical: 16 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  actor: { fontSize: 14, fontWeight: '700', color: Colors.text, flex: 1, marginRight: 8 },
  action: { fontSize: 12, fontWeight: '700', color: Colors.teal, textTransform: 'uppercase' },
  meta: { fontSize: 12, color: Colors.textSecondary },
  cats: { fontSize: 12, color: Colors.teal, marginTop: 2 },
  org: { fontSize: 11, color: Colors.textMuted, marginTop: 2 },
  time: { fontSize: 11, color: Colors.textMuted, marginTop: 4 },
  badge: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  badgeText: { fontSize: 11, fontWeight: '700' },
});
