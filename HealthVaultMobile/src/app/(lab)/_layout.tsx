import { Stack } from 'expo-router';
import { Colors } from '@/constants';

export default function LabLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: Colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: 'bold' },
      }}
    >
      <Stack.Screen name="dashboard" options={{ title: 'Lab Portal' }} />
    </Stack>
  );
}
