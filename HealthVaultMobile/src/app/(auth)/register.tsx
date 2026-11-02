import { useEffect } from 'react';
import { router } from 'expo-router';

/**
 * Mobile self-registration via email/password is disabled.
 * Patients are created automatically on their first verified Firebase
 * phone sign-in.  This file is kept to avoid broken route references.
 */
export default function RegisterScreen() {
  useEffect(() => {
    router.replace('/(auth)/login');
  }, []);
  return null;
}
