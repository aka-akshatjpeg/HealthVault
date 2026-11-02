import React from 'react';
import { View, Text, ScrollView, StyleSheet, SafeAreaView, RefreshControl } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { patientService } from '@/services/patient.service';
import { Card } from '@/components/Card';
import { LoadingScreen } from '@/components/LoadingScreen';
import { Colors } from '@/constants';

const typeIcons: Record<string, string> = {
  access_request: '🔐', new_report: '🧪', new_consultation: '🩺',
  access_approved: '✅', default: '🔔',
};

export default function NotificationsScreen() {
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['notifications'],
    queryFn: patientService.getNotifications,
  });
  if (isLoading) return <LoadingScreen message="Loading notifications..." />;
  const notifications = data?.notifications || [];
  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={isFetching} onRefresh={() => { void refetch(); }} tintColor={Colors.primary} />}
      >
        {notifications.length === 0 ? (
          <Text style={styles.empty}>No notifications yet.</Text>
        ) : notifications.map((n: any) => (
          <Card key={n.id} style={!n.is_read ? styles.unread : undefined}>
            <View style={styles.row}>
              <Text style={styles.icon}>{typeIcons[n.notification_type] || typeIcons.default}</Text>
              <View style={{ flex: 1 }}>
                <Text style={styles.title}>{n.title}</Text>
                {n.message && <Text style={styles.message}>{n.message}</Text>}
                <Text style={styles.time}>{new Date(n.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</Text>
              </View>
              {!n.is_read && <View style={styles.dot} />}
            </View>
          </Card>
        ))}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: 16 },
  unread: { borderLeftWidth: 4, borderLeftColor: Colors.primary },
  row: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  icon: { fontSize: 24, marginTop: 2 },
  title: { fontSize: 15, fontWeight: '700', color: Colors.text, marginBottom: 4 },
  message: { fontSize: 13, color: Colors.textSecondary, lineHeight: 18, marginBottom: 4 },
  time: { fontSize: 11, color: Colors.textMuted },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: Colors.primary, marginTop: 6 },
  empty: { textAlign: 'center', color: Colors.textMuted, marginTop: 60, fontSize: 15 },
});
