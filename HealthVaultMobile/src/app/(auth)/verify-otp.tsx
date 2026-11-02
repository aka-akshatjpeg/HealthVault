import { useEffect } from 'react';
import { router } from 'expo-router';

/**
 * This screen is intentionally disabled.
 *
 * The demo email/password + OTP flow has been removed. All sign-in now
 * goes through Firebase (Phone OTP, Google, Apple) on the login screen.
 *
 * The file is kept to avoid broken route references; it immediately
 * redirects to the login screen. It can be deleted once all deep-links
 * to /(auth)/verify-otp have been confirmed absent.
 */
export default function VerifyOTPScreen() {
  useEffect(() => {
    router.replace('/(auth)/login');
  }, []);

  return null;
}
