import React from 'react';
import { View, Text, StyleSheet, SafeAreaView, ScrollView, TouchableOpacity, Share } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import QRCode from 'react-native-qrcode-svg';
import { Ionicons } from '@expo/vector-icons';
import { patientService } from '@/services/patient.service';
import { LoadingScreen } from '@/components/LoadingScreen';
import { Colors, API_BASE_URL } from '@/constants';
import { Logo } from '@/components/Logo';

export default function HealthIdScreen() {
  const { data, isLoading } = useQuery({ queryKey: ['health-id'], queryFn: patientService.getHealthId });
  if (isLoading) return <LoadingScreen message="Loading your Health ID..." />;
  const { hv_id, patient_name, blood_group } = data || {};
  const qrValue = hv_id ? `${API_BASE_URL}/patient/health-id/public?id=${hv_id}` : 'healthvault';

  const handleShare = async () => {
    await Share.share({ message: `My HealthVault ID: ${hv_id}\nScan or visit: ${qrValue}` });
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.idCard}>
          <View style={styles.cardHeader}>
            <Logo width={100} height={30} variant="compact" />
            <Ionicons name="shield-checkmark" size={24} color={Colors.tealLight} />
          </View>
          <View style={styles.cardBody}>
            <Text style={styles.name}>{patient_name}</Text>
            <Text style={styles.hvId}>{hv_id}</Text>
            {blood_group && <Text style={styles.bloodGroup}>Blood Group: <Text style={styles.bloodGroupValue}>{blood_group}</Text></Text>}
          </View>
          <View style={styles.qrContainer}>
            {hv_id ? <QRCode value={qrValue} size={150} color={Colors.primary} backgroundColor="transparent" /> : <Text style={styles.noQr}>QR not available</Text>}
          </View>
          <Text style={styles.qrHint}>Scan to verify identity & access emergency profile</Text>
        </View>

        <TouchableOpacity style={styles.shareBtn} onPress={handleShare}>
          <Ionicons name="share-outline" size={20} color="#fff" />
          <Text style={styles.shareBtnText}>Share Health ID</Text>
        </TouchableOpacity>

        <View style={styles.emergencyInfoBox}>
          <View style={styles.emergencyHeader}>
            <View style={styles.emergencyIconBox}>
              <Ionicons name="medkit" size={20} color={Colors.error} />
            </View>
            <Text style={styles.emergencyTitle}>Emergency Profile Linked</Text>
          </View>
          <Text style={styles.emergencyText}>First responders can scan your QR code to instantly view your emergency profile (blood type, critical allergies, emergency contacts) without requiring login.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scroll: { padding: 20 },
  idCard: { backgroundColor: Colors.primary, borderRadius: 24, padding: 24, paddingBottom: 28, shadowColor: Colors.primary, shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.3, shadowRadius: 20, elevation: 8, marginBottom: 24 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  cardBody: { marginBottom: 24, alignItems: 'center' },
  name: { color: '#fff', fontSize: 26, fontWeight: '700', marginBottom: 6 },
  hvId: { color: Colors.tealLight, fontSize: 18, fontWeight: '600', letterSpacing: 2, marginBottom: 12 },
  bloodGroup: { color: 'rgba(255,255,255,0.7)', fontSize: 14, backgroundColor: 'rgba(255,255,255,0.1)', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12, overflow: 'hidden' },
  bloodGroupValue: { color: '#fff', fontWeight: '700' },
  qrContainer: { alignSelf: 'center', backgroundColor: '#fff', borderRadius: 20, padding: 16, marginBottom: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.1, shadowRadius: 10, elevation: 4 },
  noQr: { color: Colors.textMuted, fontSize: 14 },
  qrHint: { textAlign: 'center', color: 'rgba(255,255,255,0.6)', fontSize: 12, fontWeight: '500' },
  shareBtn: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', backgroundColor: Colors.teal, borderRadius: 16, padding: 18, marginBottom: 24, shadowColor: Colors.teal, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8, elevation: 3 },
  shareBtnText: { color: '#fff', fontWeight: '700', fontSize: 16, marginLeft: 8 },
  emergencyInfoBox: { backgroundColor: Colors.surface, borderRadius: 20, padding: 20, borderWidth: 1, borderColor: Colors.border },
  emergencyHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  emergencyIconBox: { width: 40, height: 40, borderRadius: 12, backgroundColor: Colors.error + '15', alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  emergencyTitle: { fontSize: 16, fontWeight: '700', color: Colors.text },
  emergencyText: { fontSize: 13, color: Colors.textSecondary, lineHeight: 20 },
});
