import React, { useEffect, useState } from 'react';
import { createNavigationContainerRef, NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { View, ActivityIndicator, StyleSheet, Text, TouchableOpacity } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Home, Moon, Mic, User } from 'lucide-react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

// Auth Screens
import { LoginScreen } from '../screens/LoginScreen';
import SignUpScreen from '../screens/SignUpScreen';

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
import ConversationHistoryScreen from '../screens/ConversationHistoryScreen';

// Realtime Session
import RealtimeSessionScreen from '../screens/RealtimeSessionScreen';

// Legacy
import FeedbackScreen from '../screens/FeedbackScreen';

export type RootStackParamList = {
  // Auth
  Login: undefined;
  SignUp: undefined;  // ← ADDED

  // Main
  Main: undefined;

  // Profiles
  Profiles: { profile?: any };
  CreateProfileStep1: { email: string; password: string };
  CreateProfileStep2: { 
    email: string;
    password: string;
    name: string;
    age: string;
    gender: string;
    koreanLevel: string;
  };

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
    sessionId?: string;
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
    source?: 'home' | 'session';
    avatar?: any;
    duration?: string;
    scores?: any;
    savedItems?: string[];
  };
  ConversationHistory: undefined;

  // Realtime
  RealtimeSession: { avatar: any };

  // Legacy
  Feedback: { avatar?: any; duration?: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const navigationRef = createNavigationContainerRef<any>();

const MENU_ITEMS = [
  { route: 'Home', label: '홈', icon: Home },
  { route: 'Avatar', label: '아바타', icon: Moon },
  { route: 'Real-time', label: '실시간', icon: Mic },
  { route: 'My Profile', label: '프로필', icon: User },
];

const HIDE_MENU_ROUTES = new Set([
  'Login',
  'SignUp',
  'Profiles',
  'CreateProfileStep1',
  'CreateProfileStep2',
]);

const ROUTE_TO_MENU: Record<string, string> = {
  Main: 'Home',
  Home: 'Home',
  Avatar: 'Avatar',
  'Real-time': 'Real-time',
  'My Profile': 'My Profile',
  AvatarSelection: 'Avatar',
  AvatarCompatibility: 'Avatar',
  AvatarDetail: 'Avatar',
  CreateAvatar: 'Avatar',
  RealtimeSession: 'Real-time',
  EditProfile: 'My Profile',
  EditInterests: 'My Profile',
  SavedVocabulary: 'My Profile',
  Chat: 'Home',
  ConversationSummary: 'Home',
  Analytics: 'Home',
  ConversationHistory: 'Home',
  SituationSelection: 'Home',
  CreateSituation: 'Home',
  SpeechRecommendation: 'Home',
  Feedback: 'Home',
};

const PersistentBottomMenu = ({ currentRouteName }: { currentRouteName?: string }) => {
  const insets = useSafeAreaInsets();
  const activeRoute = ROUTE_TO_MENU[currentRouteName || ''] || 'Home';
  const menuHeight = 68 + insets.bottom;

  if (!currentRouteName || HIDE_MENU_ROUTES.has(currentRouteName)) {
    return null;
  }

  const handlePress = (route: string) => {
    if (!navigationRef.isReady()) return;
    navigationRef.navigate('Main', { screen: route });
  };

  return (
    <View style={[styles.bottomMenu, { height: menuHeight, paddingBottom: Math.max(8, insets.bottom) }]}>
      {MENU_ITEMS.map(item => {
        const focused = activeRoute === item.route;
        const Icon = item.icon;
        return (
          <TouchableOpacity
            key={item.route}
            style={styles.bottomMenuItem}
            onPress={() => handlePress(item.route)}
            activeOpacity={0.75}
          >
            <Icon size={22} color={focused ? '#6C3BFF' : '#B0B0C5'} />
            <Text style={[styles.bottomMenuLabel, focused && styles.bottomMenuLabelActive]}>
              {item.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

export const AppNavigator: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [, setIsAuthenticated] = useState(false);
  const [currentRouteName, setCurrentRouteName] = useState<string>();
  const insets = useSafeAreaInsets();
  const shouldShowMenu = Boolean(currentRouteName && !HIDE_MENU_ROUTES.has(currentRouteName));
  const bottomMenuHeight = shouldShowMenu ? 68 + insets.bottom : 0;

  useEffect(() => {
    const checkAuth = async () => {
      const token = await AsyncStorage.getItem('token');
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
    <NavigationContainer
      ref={navigationRef}
      onReady={() => setCurrentRouteName(navigationRef.getCurrentRoute()?.name)}
      onStateChange={() => setCurrentRouteName(navigationRef.getCurrentRoute()?.name)}
    >
      <View style={styles.appShell}>
        <View style={[styles.navigatorShell, { paddingBottom: bottomMenuHeight }]}>
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            {/* Auth */}
            <Stack.Screen name="Login" component={LoginScreen} />
            <Stack.Screen name="SignUp" component={SignUpScreen} />

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
            <Stack.Screen name="ConversationHistory" component={ConversationHistoryScreen} />

            {/* Realtime Session */}
            <Stack.Screen name="RealtimeSession" component={RealtimeSessionScreen} />

            {/* Legacy */}
            <Stack.Screen name="Feedback" component={FeedbackScreen} />
          </Stack.Navigator>
        </View>
        <PersistentBottomMenu currentRouteName={currentRouteName} />
      </View>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  appShell: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  navigatorShell: {
    flex: 1,
  },
  bottomMenu: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 100,
    elevation: 16,
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-around',
    paddingTop: 8,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E8E8F0',
    shadowColor: '#1A1A2E',
    shadowOffset: { width: 0, height: -8 },
    shadowOpacity: 0.08,
    shadowRadius: 18,
  },
  bottomMenuItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 3,
  },
  bottomMenuLabel: {
    fontSize: 11,
    fontWeight: '500',
    color: '#B0B0C5',
  },
  bottomMenuLabelActive: {
    color: '#6C3BFF',
    fontWeight: '700',
  },
});

/*
 * NAVIGATION FLOW:
 *
 * 1. Login → Main (Home tab)
 *    Login → SignUp → CreateProfileStep1 → CreateProfileStep2 → Main
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
