import { Stack } from 'expo-router';
import { Colors } from '@/constants';

export default function AuthLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        headerStyle: { backgroundColor: Colors.primary },
        headerTintColor: '#fff',
        headerTitleStyle: { fontWeight: 'bold' },
      }}
    >
      <Stack.Screen name="portal-select" options={{ title: 'Welcome' }} />
      <Stack.Screen name="login" options={{ title: 'Sign In' }} />
      <Stack.Screen name="verify-otp" options={{ title: 'Verify OTP' }} />
      <Stack.Screen name="register" options={{ title: 'Create Account' }} />
    </Stack>
  );
}
