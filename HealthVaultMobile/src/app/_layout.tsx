import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { StatusBar } from 'expo-status-bar';
import { Colors } from '@/constants';

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 1000 * 60 * 2, retry: 1 } },
});

function RootLayoutNav() {
  const loadUser = useAuthStore((s) => s.loadUser);

  // Restore the stored session once. The initial route (index.tsx) waits for
  // isLoading to finish before redirecting by role.
  useEffect(() => {
    loadUser();
  }, [loadUser]);

  // The navigator must always be mounted so routing is never attempted before
  // the router is ready.
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="(auth)" />
      <Stack.Screen name="(patient)" />
      <Stack.Screen name="(doctor)" />
      <Stack.Screen name="(lab)" />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <StatusBar style="dark" />
      <RootLayoutNav />
    </QueryClientProvider>
  );
}
