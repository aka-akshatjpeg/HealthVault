import { Tabs } from 'expo-router';
import { View, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Colors } from '@/constants';
import { HealthVaultAILogo } from '@/components/AILogo';

export default function PatientLayout() {
  const insets = useSafeAreaInsets();
  
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: Colors.primaryLight,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarStyle: { 
          backgroundColor: 'rgba(255,255,255,0.95)', 
          borderTopWidth: 0, 
          elevation: 10,
          shadowColor: '#163152',
          shadowOffset: { width: 0, height: -4 },
          shadowOpacity: 0.05,
          shadowRadius: 10,
          height: 65 + insets.bottom,
          paddingBottom: insets.bottom + 8,
          paddingTop: 12,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
        },
        headerStyle: { backgroundColor: Colors.surface, shadowOpacity: 0, elevation: 0, borderBottomWidth: 1, borderBottomColor: Colors.border },
        headerTintColor: Colors.primary,
        headerTitleStyle: { fontWeight: '700', fontSize: 17 },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          headerShown: false,
          title: 'Home',
          tabBarIcon: ({ color, size, focused }) => <Ionicons name={focused ? "home" : "home-outline"} size={size} color={color} />
        }}
      />
      <Tabs.Screen
        name="records"
        options={{ 
          title: 'Records', 
          tabBarIcon: ({ color, size, focused }) => <Ionicons name={focused ? "document-text" : "document-text-outline"} size={size} color={color} /> 
        }}
      />
      <Tabs.Screen
        name="health-id"
        options={{ 
          title: 'My ID', 
          headerTitle: 'Health ID',
          tabBarIcon: ({ color, size, focused }) => <Ionicons name={focused ? "qr-code" : "qr-code-outline"} size={size} color={color} /> 
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{ 
          title: 'Alerts', 
          tabBarIcon: ({ color, size, focused }) => <Ionicons name={focused ? "notifications" : "notifications-outline"} size={size} color={color} /> 
        }}
      />
      <Tabs.Screen
        name="settings"
        options={{ 
          title: 'Profile', 
          headerTitle: 'Profile & Settings',
          tabBarIcon: ({ color, size, focused }) => <Ionicons name={focused ? "person" : "person-outline"} size={size} color={color} /> 
        }}
      />
      <Tabs.Screen
        name="ai-assistant"
        options={{ 
          title: 'AI', 
          headerTitle: 'AI Assistant',
          tabBarIcon: ({ color, size, focused }) => (
            <HealthVaultAILogo width={size * 1.1} height={size * 1.1} style={{ opacity: focused ? 1 : 0.6 }} />
          )
        }}
      />
      {/* Hidden from tab bar but still navigable */}
      <Tabs.Screen name="timeline" options={{ href: null, title: 'Health Timeline' }} />
      <Tabs.Screen name="consent" options={{ href: null, title: 'Access Requests' }} />
      <Tabs.Screen name="access-history" options={{ href: null, title: 'Audit Log' }} />
      <Tabs.Screen name="lab-report" options={{ href: null, title: 'Report Detail' }} />
    </Tabs>
  );
}
