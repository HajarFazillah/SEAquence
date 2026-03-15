import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

// Auth Screens
import { LoginScreen } from '../screens/LoginScreen';

// Main Tabs
import { MainTabs } from './MainTabs';

// Profile Flow
import ProfilesScreen from '../screens/ProfilesScreen';
import CreateProfileStep1Screen from '../screens/CreateProfileStep1Screen';
import CreateProfileStep2Screen from '../screens/CreateProfileStep2Screen';
import EditProfileScreen from '../screens/EditProfileScreen';
import EditInterestsScreen from '../screens/EditInterestsScreen';
import SavedVocabularyScreen from '../screens/SavedVocabularyScreen';

// Avatar Flow
import AvatarSelectionScreen from '../screens/AvatarSelectionScreen';
import AvatarCompatibilityScreen from '../screens/AvatarCompatibilityScreen';
import AvatarDetailScreen from '../screens/AvatarDetailScreen';
import CreateAvatarScreen from '../screens/CreateAvatarScreen';

// Situation Flow
import SituationSelectionScreen from '../screens/SituationSelectionScreen';
import CreateSituationScreen from '../screens/CreateSituationScreen';
import SpeechRecommendationScreen from '../screens/SpeechRecommendationScreen';

// Chat
import ChatScreen from '../screens/ChatScreen';

// Post-Chat Flow
import ConversationSummaryScreen from '../screens/ConversationSummaryScreen';
import AnalyticsScreen from '../screens/AnalyticsScreen';

// Realtime Session
import RealtimeSessionScreen from '../screens/RealtimeSessionScreen';

// Legacy (keeping for compatibility)
import FeedbackScreen from '../screens/FeedbackScreen';

// Type definitions for navigation
export type RootStackParamList = {
  // Auth
  Login: undefined;
  
  // Main
  Main: undefined;
  
  // Profiles
  Profiles: { profile?: any };
  CreateProfileStep1: undefined;
  CreateProfileStep2: { name: string; koreanLevel: string };
  
  // User Profile Edit
  EditProfile: undefined;
  EditInterests: { interests?: string[]; dislikes?: string[] };
  SavedVocabulary: { type: 'words' | 'phrases' };
  
  // Avatar Flow
  AvatarSelection: undefined;
  AvatarCompatibility: { interests?: string[] };
  AvatarDetail: { avatar: any; isCustom?: boolean };
  CreateAvatar: { avatar?: any; isEdit?: boolean; mode?: 'scratch' | 'random'; template?: any };
  
  // Situation Flow
  SituationSelection: { avatar: any };
  CreateSituation: undefined;
  SpeechRecommendation: { avatar: any; situation: any };
  
  // Chat
  Chat: { 
    name?: string; 
    avatarBg?: string; 
    avatar?: any; 
    situation?: any;
    recommendedLevel?: string;
  };
  
  // Post-Chat
  ConversationSummary: { 
    avatar?: any; 
    duration?: string;
    situation?: any;
    conversationHistory?: any[];
    finalMood?: number;
  };
  Analytics: { 
    avatar?: any; 
    duration?: string; 
    scores?: any;
    savedItems?: string[];
  };
  
  // Realtime
  RealtimeSession: { avatar: any };
  
  // Legacy
  Feedback: { avatar?: any; duration?: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export const AppNavigator: React.FC = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {/* Auth */}
        <Stack.Screen name="Login" component={LoginScreen} />
        
        {/* Main Tabs */}
        <Stack.Screen name="Main" component={MainTabs} />
        
        {/* Profile Creation Flow */}
        <Stack.Screen name="Profiles" component={ProfilesScreen} />
        <Stack.Screen name="CreateProfileStep1" component={CreateProfileStep1Screen} />
        <Stack.Screen name="CreateProfileStep2" component={CreateProfileStep2Screen} />
        <Stack.Screen name="EditProfile" component={EditProfileScreen} />
        <Stack.Screen name="EditInterests" component={EditInterestsScreen} />
        <Stack.Screen name="SavedVocabulary" component={SavedVocabularyScreen} />
        
        {/* Avatar Flow */}
        <Stack.Screen name="AvatarSelection" component={AvatarSelectionScreen} />
        <Stack.Screen name="AvatarCompatibility" component={AvatarCompatibilityScreen} />
        <Stack.Screen name="AvatarDetail" component={AvatarDetailScreen} />
        <Stack.Screen name="CreateAvatar" component={CreateAvatarScreen} />
        
        {/* Situation Flow */}
        <Stack.Screen name="SituationSelection" component={SituationSelectionScreen} />
        <Stack.Screen name="CreateSituation" component={CreateSituationScreen} />
        <Stack.Screen name="SpeechRecommendation" component={SpeechRecommendationScreen} />
        
        {/* Chat */}
        <Stack.Screen name="Chat" component={ChatScreen} />
        
        {/* Post-Chat Flow */}
        <Stack.Screen name="ConversationSummary" component={ConversationSummaryScreen} />
        <Stack.Screen name="Analytics" component={AnalyticsScreen} />
        
        {/* Realtime Session */}
        <Stack.Screen name="RealtimeSession" component={RealtimeSessionScreen} />
        
        {/* Legacy */}
        <Stack.Screen name="Feedback" component={FeedbackScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

/*
 * NAVIGATION FLOW:
 * 
 * 1. Login → Main (Home tab)
 * 
 * 2. Start Practice Flow:
 *    Home → AvatarSelection → SituationSelection → SpeechRecommendation → Chat
 * 
 * 3. After Chat:
 *    Chat → ConversationSummary (mistakes, vocab, save) → Analytics → Main
 * 
 * 4. Avatar Creation:
 *    Avatar tab → "새 아바타 만들기" → Choose:
 *      - "처음부터 만들기" → CreateAvatar (4 steps with AI bio)
 *      - "랜덤으로 만들기" → CreateAvatar (pre-filled with random data)
 *    Avatar card → 수정 → CreateAvatar (edit mode)
 *    Avatar card → 삭제 → Delete confirmation
 * 
 * 5. Profile & Vocabulary:
 *    My Profile tab → 배운 단어 → SavedVocabulary (words)
 *    My Profile tab → 배운 표현 → SavedVocabulary (phrases)
 *    My Profile tab → EditProfile / EditInterests (with free text input)
 * 
 * 6. Situation Creation:
 *    SituationSelection → "새 상황 만들기" → CreateSituation → Back
 */
