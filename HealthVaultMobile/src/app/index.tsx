import { Redirect } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { LoadingScreen } from '@/components/LoadingScreen';

/**
 * Initial route ("/").
 * Waits for the stored session to load, then declaratively redirects to the
 * portal selector (logged out) or the role-specific dashboard (logged in).
 * <Redirect> only navigates once the navigator is mounted and ready.
 */
export default function Index() {
  const user = useAuthStore((s) => s.user);
  const isLoading = useAuthStore((s) => s.isLoading);

  if (isLoading) return <LoadingScreen message="Starting HealthVault..." />;

  switch (user?.role) {
    case 'patient':
      return <Redirect href="/(patient)/dashboard" />;
    case 'doctor':
      return <Redirect href="/(doctor)/dashboard" />;
    case 'lab':
      return <Redirect href="/(lab)/dashboard" />;
    default:
      return <Redirect href="/(auth)/portal-select" />;
  }
}
