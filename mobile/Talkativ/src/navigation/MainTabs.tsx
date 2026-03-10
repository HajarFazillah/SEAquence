import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';
import { HomeScreen } from '../screens/HomeScreen';
import AvatarScreen from '../screens/AvatarScreen';
import RealtimeScreen from '../screens/RealtimeScreen';
import { MyProfileScreen } from '../screens/MyProfileScreen';

const Tab = createBottomTabNavigator();

// Simple icon using emoji/text as placeholder (replace with real icons later)
const TabIcon = ({ emoji, focused }: { emoji: string; focused: boolean }) => (
  <Text style={{ fontSize: 22, opacity: focused ? 1 : 0.4 }}>{emoji}</Text>
);

export const MainTabs: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: '#6C3BFF',
        tabBarInactiveTintColor: '#B0B0C5',
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#E8E8F0',
          height: 64,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '500',
        },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon emoji="🏠" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Avatar"
        component={AvatarScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon emoji="🌙" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="Real-time"
        component={RealtimeScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon emoji="🎵" focused={focused} />,
        }}
      />
      <Tab.Screen
        name="My Profile"
        component={MyProfileScreen}
        options={{
          tabBarIcon: ({ focused }) => <TabIcon emoji="👤" focused={focused} />,
        }}
      />
    </Tab.Navigator>
  );
};
