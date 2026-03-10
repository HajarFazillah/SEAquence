import React from 'react';
import Svg, { Circle } from 'react-native-svg';

import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

// Mock user data (replace with real API later)
const mockUser = {
  name: 'Nunnalin',
  avatarUrl: 'https://i.pravatar.cc/100?img=47', // placeholder avatar
};

// Mock in-progress data
const mockInProgress = [
  { id: '1', category: '실물 프로필', name: '하자', progress: 0.6, color: '#5B8DEF' },
  { id: '2', category: '아바타', name: '김에은', progress: 0.4, color: '#F4A261' },
  { id: '3', category: '실물 프로필', name: '민준', progress: 0.75, color: '#5B8DEF' },
];

// Mock summarize data
const mockSummarize = [
  {
    id: '1',
    title: 'Vocabularies',
    subtitle: '23 words saved',
    count: 23,
    iconEmoji: '💼',
    iconBg: '#FFE8E8',
    ringColor: '#F4A261',
  },
  {
    id: '2',
    title: 'Phrases',
    subtitle: '5 phrases saved',
    count: 5,
    iconEmoji: '👤',
    iconBg: '#EAE8FF',
    ringColor: '#6C3BFF',
  },
  {
    id: '3',
    title: 'Generated Avatar',
    subtitle: '5 avatars saved',
    count: 5,
    iconEmoji: '📖',
    iconBg: '#FFF3E0',
    ringColor: '#F4A261',
  },
];

// Circular progress ring component
const CircularProgress = ({ percentage }: { percentage: number }) => {
  const size = 80;
  const strokeWidth = 6;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={{ position: 'absolute' }}>
        {/* Background circle */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255,255,255,0.3)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* Progress circle */}
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#FFFFFF"
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          rotation="-90"
          origin={`${size / 2}, ${size / 2}`}
        />
      </Svg>
      <Text style={{ color: '#FFFFFF', fontWeight: '700', fontSize: 16 }}>{percentage}%</Text>
    </View>
  );
};

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  const handleProfilePress = () => {
    navigation.navigate('My Profile' as never);
  };

  const handleNotificationPress = () => {
    console.log('Notification pressed'); // TODO: later
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>

        {/* ── PART 1: Top greeting header ── */}
        <View style={styles.header}>
          {/* Left: avatar + greeting (tappable → My Profile) */}
          <TouchableOpacity style={styles.profileRow} onPress={handleProfilePress}>
            <Image
              source={{ uri: mockUser.avatarUrl }}
              style={styles.avatar}
            />
            <View style={styles.greetingText}>
              <Text style={styles.hello}>Hello!</Text>
              <Text style={styles.username}>{mockUser.name}</Text>
            </View>
          </TouchableOpacity>

          {/* Right: notification bell */}
          <TouchableOpacity onPress={handleNotificationPress} style={styles.notifButton}>
            <Text style={styles.notifIcon}>🔔</Text>
          </TouchableOpacity>
        </View>

        {/* ── PART 2: Analysis dashboard card ── */}
        <View style={styles.analysisCard}>
          {/* Top row: text + menu */}
          <View style={styles.analysisTop}>
            <Text style={styles.analysisTitle}>
              Your Korean skills{'\n'}can be improved daily !
            </Text>
            <TouchableOpacity style={styles.menuButton}>
              <Text style={styles.menuDots}>···</Text>
            </TouchableOpacity>
          </View>

          {/* Bottom row: Analysis button + progress ring */}
          <View style={styles.analysisBottom}>
            <TouchableOpacity style={styles.analysisButton}>
              <Text style={styles.analysisButtonText}>Analysis</Text>
            </TouchableOpacity>
            <CircularProgress percentage={85} />
          </View>
        </View>

        {/* ── PART 3: In Progress ── */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>In Progress</Text>
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{mockInProgress.length}</Text>
          </View>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.horizontalScroll}
          contentContainerStyle={styles.horizontalScrollContent}
        >
          {mockInProgress.map((item) => (
            <TouchableOpacity
              key={item.id} style={styles.progressCard} onPress={() => navigation.navigate('Profiles', { profile: item })}>
              <Text style={styles.progressCategory}>{item.category}</Text>
              <Text style={styles.progressName}>{item.name}</Text>
              <View style={styles.progressBarBg}>
                <View
                  style={[
                    styles.progressBarFill,
                    {
                      width: `${item.progress * 100}%` as any,
                      backgroundColor: item.color,
                    },
                  ]}
                />
              </View>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* ── PART 4: Summarize ── */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Summary</Text>
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{mockSummarize.length}</Text>
          </View>
        </View>

        <View style={styles.summarizeList}>
          {mockSummarize.map((item) => (
            <TouchableOpacity
              key={item.id}
              style={styles.summarizeRow}
              onPress={() => {
                if (item.title === 'Generated Avatar') {
                  navigation.navigate('Main', { screen: 'Avatar' });
                }
              }}
            >
              {/* Left: icon */}
              <View style={[styles.summarizeIcon, { backgroundColor: item.iconBg }]}>
                <Text style={styles.summarizeEmoji}>{item.iconEmoji}</Text>
              </View>

              {/* Middle: title + subtitle */}
              <View style={styles.summarizeText}>
                <Text style={styles.summarizeTitle}>{item.title}</Text>
                <Text style={styles.summarizeSubtitle}>{item.subtitle}</Text>
              </View>

              {/* Right: count ring */}
              <View style={[styles.summarizeCountRing, { borderColor: item.ringColor }]}>
                <Text style={[styles.summarizeCount, { color: item.ringColor }]}>
                  {item.count}
                </Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 32,
  },

  // ── Part 1: Header ──
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  profileRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    marginRight: 12,
    backgroundColor: '#E8E8F0', // fallback color while loading
  },
  greetingText: {
    justifyContent: 'center',
  },
  hello: {
    fontSize: 13,
    color: '#6C6C80',
  },
  username: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A2E',
  },
  notifButton: {
    padding: 8,
  },
  notifIcon: {
    fontSize: 22,
  },

  // ── Part 2: Analysis card ──
  analysisCard: {
    backgroundColor: '#6C3BFF',
    borderRadius: 20,
    padding: 20,
    marginBottom: 28,
  },
  analysisTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 20,
  },
  analysisTitle: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 24,
    flex: 1,
  },
  menuButton: {
    padding: 4,
  },
  menuDots: {
    color: '#FFFFFF',
    fontSize: 18,
    letterSpacing: 2,
  },
  analysisBottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  analysisButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    paddingVertical: 10,
    paddingHorizontal: 24,
  },
  analysisButtonText: {
    color: '#6C3BFF',
    fontWeight: '600',
    fontSize: 14,
  },

  // ── Part 3: In Progress ──
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A2E',
    marginRight: 8,
  },
  countBadge: {
    backgroundColor: '#F0EDFF',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  countText: {
    color: '#6C3BFF',
    fontWeight: '600',
    fontSize: 13,
  },
  horizontalScroll: {
    marginBottom: 28,
  },
  horizontalScrollContent: {
    paddingRight: 20,
    gap: 12,
  },
  progressCard: {
    backgroundColor: '#F5F5FA',
    borderRadius: 16,
    padding: 16,
    width: 160,
    justifyContent: 'space-between',
    minHeight: 110,
  },
  progressCategory: {
    fontSize: 12,
    color: '#6C6C80',
    marginBottom: 8,
  },
  progressName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 16,
  },
  progressBarBg: {
    height: 6,
    backgroundColor: '#E2E2EC',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: 6,
    borderRadius: 4,
  },
  // ── Part 4: Summarize ──
  summarizeList: {
    gap: 12,
  },
  summarizeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  summarizeIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  summarizeEmoji: {
    fontSize: 20,
  },
  summarizeText: {
    flex: 1,
  },
  summarizeTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1A2E',
    marginBottom: 2,
  },
  summarizeSubtitle: {
    fontSize: 12,
    color: '#B0B0C5',
  },
  summarizeCountRing: {
    width: 40,
    height: 40,
    borderRadius: 20,
    borderWidth: 3,
    alignItems: 'center',
    justifyContent: 'center',
  },
  summarizeCount: {
    fontWeight: '700',
    fontSize: 14,
  },

});