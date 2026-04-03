import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Home, Moon, Mic, User } from 'lucide-react-native';
import { HomeScreen } from '../screens/HomeScreen';
import AvatarScreen from '../screens/AvatarScreen';
import RealtimeScreen from '../screens/RealtimeScreen';
import { MyProfileScreen } from '../screens/MyProfileScreen';

const Tab = createBottomTabNavigator();

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
          tabBarLabel: '홈',
          tabBarIcon: ({ color, size }) => <Home size={size} color={color} />,
        }}
      />
      <Tab.Screen
        name="Avatar"
        component={AvatarScreen}
        options={{
          tabBarLabel: '아바타',
          tabBarIcon: ({ color, size }) => <Moon size={size} color={color} />,
        }}
      />
      <Tab.Screen
        name="Real-time"
        component={RealtimeScreen}
        options={{
          tabBarLabel: '실시간',
          tabBarIcon: ({ color, size }) => <Mic size={size} color={color} />,
        }}
      />
      <Tab.Screen
        name="My Profile"
        component={MyProfileScreen}
        options={{
          tabBarLabel: '프로필',
          tabBarIcon: ({ color, size }) => <User size={size} color={color} />,
        }}
      />
    </Tab.Navigator>
  );
};
