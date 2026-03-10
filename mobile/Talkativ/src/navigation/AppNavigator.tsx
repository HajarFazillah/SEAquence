import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
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
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Main" component={MainTabs} />
        <Stack.Screen name="Profiles" component={ProfilesScreen} />
        <Stack.Screen name="CreateProfileStep1" component={CreateProfileStep1Screen} />
        <Stack.Screen name="CreateProfileStep2" component={CreateProfileStep2Screen} />
        <Stack.Screen name="Chat" component={ChatScreen} />
        <Stack.Screen name="RealtimeSession" component={RealtimeSessionScreen} />
        <Stack.Screen name="Feedback" component={FeedbackScreen} />
        <Stack.Screen name="Analytics" component={AnalyticsScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};