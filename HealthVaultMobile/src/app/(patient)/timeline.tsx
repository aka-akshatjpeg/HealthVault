import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, SafeAreaView, TouchableOpacity, RefreshControl, Alert } from 'react-native';
import { router } from 'expo-router';
import { useQuery } from '@tanstack/react-query';
import { Ionicons } from '@expo/vector-icons';
import { patientService } from '@/services/patient.service';
import { LoadingScreen } from '@/components/LoadingScreen';
import { Colors } from '@/constants';

const typeColors: Record<string, string> = {
  lab: Colors.info, consultation: Colors.primary, hospitalization: Colors.error,
  procedure: Colors.warning, vaccination: Colors.success, imaging: Colors.teal,
};
const typeIcons: Record<string, any> = {
  lab: 'flask', consultation: 'medical', hospitalization: 'medkit', procedure: 'body', vaccination: 'shield-checkmark', imaging: 'scan',
};

export default function TimelineScreen() {
  const [filter, setFilter] = useState('all');
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['timeline', filter],
    queryFn: () => patientService.getTimeline(filter),
  });
  
  if (isLoading) return <LoadingScreen message="Building your timeline..." />;
  const items = data?.timeline || [];
  const filters = ['all', 'lab', 'consultation', 'vaccination', 'procedure', 'imaging'];
  
  const handleEventClick = (item: any) => {
    if (item.type === 'lab') {
      router.push({ pathname: '/(patient)/lab-report', params: { id: item.id } });
    } else if (item.type === 'vaccination') {
      router.push({ pathname: '/(patient)/records', params: { tab: 'Vaccinations' } });
    } else if (item.type === 'procedure') {
      router.push({ pathname: '/(patient)/records', params: { tab: 'Procedures' } });
    } else {
      Alert.alert(
        'Record Unavailable',
        'Detailed mobile records for this event type are not currently available.'
      );
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterBar} contentContainerStyle={styles.filterContent}>
        {filters.map((f) => (
          <TouchableOpacity key={f} style={[styles.chip, filter === f && styles.chipActive]} onPress={() => setFilter(f)}>
            <Text style={[styles.chipText, filter === f && styles.chipTextActive]}>{f === 'all' ? 'All Events' : f.charAt(0).toUpperCase() + f.slice(1)}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
      <ScrollView contentContainerStyle={styles.scroll} refreshControl={<RefreshControl refreshing={isFetching} onRefresh={refetch} tintColor={Colors.teal} />}>
        {items.length === 0 ? <Text style={styles.empty}>No events found.</Text> : items.map((item: any, index: number) => {
          const isLast = index === items.length - 1;
          const color = typeColors[item.type] || Colors.textMuted;
          return (
            <View key={`${item.id}-${index}`} style={styles.itemRow}>
              <View style={styles.timelineColumn}>
                <View style={[styles.dot, { backgroundColor: color + '20' }]}>
                  <Ionicons name={typeIcons[item.type] || 'document-text'} size={18} color={color} />
                </View>
                {!isLast && <View style={styles.line} />}
              </View>
              <View style={styles.cardWrapper}>
                <Text style={styles.date}>{item.date || 'Unknown date'}</Text>
                <TouchableOpacity activeOpacity={0.7} onPress={() => handleEventClick(item)}>
                  <View style={styles.card}>
                    <View style={{ flex: 1, paddingRight: 8 }}>
                      <Text style={styles.title}>{item.title}</Text>
                      <Text style={styles.summary}>{item.summary}</Text>
                      {item.source === 'provider' && (
                        <View style={styles.verifiedRow}>
                          <Ionicons name="checkmark-circle" size={14} color={Colors.success} style={{ marginRight: 4 }} />
                          <Text style={styles.verifiedText}>Provider Verified</Text>
                        </View>
                      )}
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={Colors.border} />
                  </View>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  filterBar: { flexGrow: 0, backgroundColor: Colors.surface, borderBottomWidth: 1, borderBottomColor: Colors.border },
  filterContent: { paddingHorizontal: 16, paddingVertical: 12, gap: 10 },
  chip: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 24, backgroundColor: Colors.background },
  chipActive: { backgroundColor: Colors.teal },
  chipText: { fontSize: 13, color: Colors.textSecondary, fontWeight: '600' },
  chipTextActive: { color: '#fff' },
  scroll: { padding: 20, paddingBottom: 40 },
  itemRow: { flexDirection: 'row', alignItems: 'flex-start' },
  timelineColumn: { width: 48, alignItems: 'center', height: '100%' },
  dot: { width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center' },
  line: { width: 2, backgroundColor: Colors.border, flex: 1, marginVertical: 4 },
  cardWrapper: { flex: 1, paddingBottom: 24, paddingLeft: 8 },
  date: { fontSize: 12, fontWeight: '700', color: Colors.textMuted, marginBottom: 8, letterSpacing: 0.5 },
  card: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.surface, borderRadius: 20, padding: 16, shadowColor: '#163152', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 1, borderWidth: 1, borderColor: Colors.border },
  title: { fontSize: 16, fontWeight: '700', color: Colors.primary, marginBottom: 6 },
  summary: { fontSize: 13, color: Colors.textSecondary, lineHeight: 18 },
  verifiedRow: { flexDirection: 'row', alignItems: 'center', marginTop: 12 },
  verifiedText: { fontSize: 12, color: Colors.success, fontWeight: '500' },
  empty: { textAlign: 'center', color: Colors.textMuted, marginTop: 60, fontSize: 15 },
});
