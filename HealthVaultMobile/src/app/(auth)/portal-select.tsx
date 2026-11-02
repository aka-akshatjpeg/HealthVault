import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Dimensions, Animated, SafeAreaView } from 'react-native';
import { router } from 'expo-router';
import { Colors } from '@/constants';
import { Logo } from '@/components/Logo';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const { width, height } = Dimensions.get('window');

export default function OnboardingScreen() {
  const [step, setStep] = useState(0);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const insets = useSafeAreaInsets();

  useEffect(() => {
    if (step === 0) {
      const timer = setTimeout(() => {
        Animated.timing(fadeAnim, {
          toValue: 0,
          duration: 400,
          useNativeDriver: true,
        }).start(() => {
          setStep(1);
          Animated.timing(fadeAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }).start();
        });
      }, 2500);
      return () => clearTimeout(timer);
    }
  }, [step]);

  const goToLogin = () => {
    router.push('/(auth)/login');
  };

  return (
    <View style={styles.container}>
      <Animated.View style={[styles.fullScreen, { opacity: fadeAnim }]}>
        {step === 0 ? (
          <LinearGradient
            colors={['#ffffff', '#f0f7f9', '#d4e8ee']}
            style={styles.fullScreen}
          >
            {/* Abstract Background Shapes */}
            <View style={[styles.abstractShape, styles.shape1]} />
            <View style={[styles.abstractShape, styles.shape2]} />
            
            <View style={styles.splashContent}>
              <Logo width={180} height={180} />
              <Text style={styles.tagline}>YOUR HEALTH. ALWAYS WITH YOU.</Text>
            </View>

            <View style={[styles.splashFooter, { paddingBottom: insets.bottom + 40 }]}>
              <Text style={styles.splashText}>
                A secure, unified home{'\n'}for your health journey.
              </Text>
              <View style={styles.indicatorContainer}>
                <View style={[styles.dot, styles.dotActive]} />
                <View style={styles.dot} />
              </View>
            </View>
          </LinearGradient>
        ) : (
          <View style={styles.fullScreen}>
            <LinearGradient
              colors={['#F5F9FC', '#ffffff']}
              style={[styles.fullScreen, { paddingTop: insets.top + 20, paddingBottom: insets.bottom + 20, paddingHorizontal: 24 }]}
            >
              <View style={styles.topBar}>
                <TouchableOpacity onPress={goToLogin}>
                  <Text style={styles.skipText}>Skip</Text>
                </TouchableOpacity>
              </View>

              <Text style={styles.heading}>Your health{'\n'}in one place.</Text>
              <Text style={styles.subheading}>
                All your reports, appointments, medications and more — secure, private and always with you.
              </Text>

              <View style={styles.visualContainer}>
                <View style={[styles.abstractShape, styles.shape3]} />
                
                {/* Floating Medical Cards */}
                <View style={[styles.floatCard, styles.float1]}>
                  <View style={styles.iconCircle}><Ionicons name="document-text" size={20} color={Colors.teal} /></View>
                  <Text style={styles.floatText}>Medical Reports</Text>
                </View>
                
                <View style={[styles.floatCard, styles.float2]}>
                  <View style={styles.iconCircle}><Ionicons name="calendar" size={20} color={Colors.info} /></View>
                  <Text style={styles.floatText}>Appointments</Text>
                </View>

                <View style={[styles.floatCard, styles.float3]}>
                  <View style={styles.iconCircle}><Ionicons name="medkit" size={20} color={Colors.primaryLight} /></View>
                  <Text style={styles.floatText}>Prescriptions</Text>
                </View>
              </View>

              <View style={styles.indicatorContainer2}>
                <View style={styles.dot} />
                <View style={[styles.dot, styles.dotActive]} />
              </View>

              <View style={styles.actionContainer}>
                <TouchableOpacity style={styles.primaryButton} onPress={goToLogin}>
                  <Text style={styles.primaryButtonText}>Get Started  →</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.secondaryButton} onPress={goToLogin}>
                  <Text style={styles.secondaryButtonText}>I already have an account</Text>
                </TouchableOpacity>
              </View>
            </LinearGradient>
          </View>
        )}
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  fullScreen: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  abstractShape: {
    position: 'absolute',
    borderRadius: 500,
    backgroundColor: Colors.tealLight,
    opacity: 0.1,
  },
  shape1: {
    width: 600, height: 600,
    bottom: -200, right: -150,
  },
  shape2: {
    width: 400, height: 400,
    bottom: -100, left: -200,
    backgroundColor: Colors.primaryLight,
    opacity: 0.08,
  },
  shape3: {
    width: 300, height: 300,
    top: '10%', right: -50,
    backgroundColor: Colors.teal,
    opacity: 0.08,
  },
  splashContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tagline: {
    marginTop: 12,
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textSecondary,
    letterSpacing: 2,
  },
  splashFooter: {
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  splashText: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  indicatorContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  indicatorContainer2: {
    flexDirection: 'row',
    gap: 8,
    alignSelf: 'center',
    marginBottom: 32,
  },
  dot: {
    width: 24,
    height: 4,
    borderRadius: 2,
    backgroundColor: Colors.border,
  },
  dotActive: {
    width: 32,
    backgroundColor: Colors.teal,
  },
  topBar: {
    alignItems: 'flex-end',
    marginBottom: 20,
  },
  skipText: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  heading: {
    fontSize: 34,
    fontWeight: '800',
    color: Colors.primary,
    lineHeight: 42,
    marginBottom: 16,
  },
  subheading: {
    fontSize: 16,
    color: Colors.textSecondary,
    lineHeight: 24,
    marginBottom: 40,
  },
  visualContainer: {
    flex: 1,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  floatCard: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    padding: 16,
    width: 140,
    height: 140,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.06,
    shadowRadius: 24,
    elevation: 8,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.8)',
  },
  float1: {
    top: '15%',
    left: '10%',
    transform: [{ rotate: '-8deg' }],
    zIndex: 2,
  },
  float2: {
    top: '30%',
    right: '5%',
    transform: [{ rotate: '12deg' }],
    zIndex: 1,
  },
  float3: {
    bottom: '15%',
    left: '25%',
    transform: [{ rotate: '4deg' }],
    zIndex: 3,
  },
  iconCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.surfaceVariant,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  floatText: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.text,
    textAlign: 'center',
  },
  actionContainer: {
    gap: 12,
  },
  primaryButton: {
    backgroundColor: Colors.primary,
    height: 54,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  secondaryButton: {
    backgroundColor: Colors.surfaceVariant,
    height: 54,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryButtonText: {
    color: Colors.primary,
    fontSize: 15,
    fontWeight: '700',
  },
});
