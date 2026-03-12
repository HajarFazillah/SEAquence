import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ActivityIndicator, View } from 'react-native';
import { LoginScreen } from '../screens/LoginScreen';
import { MainTabs } from './MainTabs';
import ProfilesScreen from '../screens/ProfilesScreen';
import CreateProfileStep1Screen from '../screens/CreateProfileStep1Screen';
import CreateProfileStep2Screen from '../screens/CreateProfileStep2Screen';
import ChatScreen from '../screens/ChatScreen';
import RealtimeSessionScreen from '../screens/RealtimeSessionScreen';
import FeedbackScreen from '../screens/FeedbackScreen';
import AnalyticsScreen from '../screens/AnalyticsScreen';

const Stack = createNativeStackNavigator();

export const AppNavigator: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      const token = await AsyncStorage.getItem('auth_token');
      setIsAuthenticated(!!token);
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#6C3BFF" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <Stack.Screen name="Login">
            {() => <LoginScreen onLogin={() => setIsAuthenticated(true)} />}
          </Stack.Screen>
        ) : (
          <>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen name="Profiles" component={ProfilesScreen} />
            <Stack.Screen name="CreateProfileStep1" component={CreateProfileStep1Screen} />
            <Stack.Screen name="CreateProfileStep2" component={CreateProfileStep2Screen} />
            <Stack.Screen name="Chat" component={ChatScreen} />
            <Stack.Screen name="RealtimeSession" component={RealtimeSessionScreen} />
            <Stack.Screen name="Feedback" component={FeedbackScreen} />
            <Stack.Screen name="Analytics" component={AnalyticsScreen} />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};