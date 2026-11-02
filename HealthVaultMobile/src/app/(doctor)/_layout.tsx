import { Stack } from 'expo-router';
import { Colors } from '@/constants';

export default function DoctorLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: Colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: 'bold' },
      }}
    >
      <Stack.Screen name="dashboard" options={{ title: 'Doctor Portal' }} />
    </Stack>
  );
}
