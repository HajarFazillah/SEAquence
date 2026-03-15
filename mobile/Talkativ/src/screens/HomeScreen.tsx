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
import { 
  Bell, MessageCircle, Heart, Mic, Users,
  TrendingUp, Clock, BookOpen, Smile, Meh, Frown,
} from 'lucide-react-native';
import { Card, Button, StatusBadge, Icon } from '../components';

// Mock user data
const mockUser = {
  name: 'Nunnalin',
  avatarUrl: 'https://i.pravatar.cc/100?img=47',
  interests: ['K-POP', '카페', '여행', '영화'],
};

// Mock in-progress data with mood and difficulty
const mockInProgress = [
  { 
    id: '1', 
    avatarId: 'sujin_friend',
    avatarName: '김수진', 
    avatarIcon: 'users' as const,
    avatarBg: '#C8B4F8',
    situation: '카페에서 수다', 
    mood: 75, // Avatar mood
    difficulty: 'easy' as const,
  },
  { 
    id: '2', 
    avatarId: 'minsu_senior',
    avatarName: '이민수', 
    avatarIcon: 'briefcase' as const,
    avatarBg: '#B4D4F8',
    situation: '캠퍼스 만남', 
    mood: 45,
    difficulty: 'medium' as const,
  },
  { 
    id: '3', 
    avatarId: 'professor_kim',
    avatarName: '김교수님', 
    avatarIcon: 'book' as const,
    avatarBg: '#B4F8D4',
    situation: '연구실 방문', 
    mood: 30,
    difficulty: 'hard' as const,
  },
];

// Mock stats
const mockStats = [
  { id: '1', title: '완료한 대화', count: 12, icon: 'message' as const, color: '#6C3BFF' },
  { id: '2', title: '배운 표현', count: 48, icon: 'book' as const, color: '#F4A261' },
  { id: '3', title: '연습 시간', count: 3.5, unit: '시간', icon: 'clock' as const, color: '#4CAF50' },
];

// Get mood icon and color
const getMoodConfig = (mood: number) => {
  if (mood >= 70) return { icon: Smile, color: '#4CAF50', label: '좋음' };
  if (mood >= 40) return { icon: Meh, color: '#F4A261', label: '보통' };
  return { icon: Frown, color: '#E53935', label: '나쁨' };
};

// Circular progress ring
const CircularProgress = ({ percentage }: { percentage: number }) => {
  const size = 80;
  const strokeWidth = 6;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={{ position: 'absolute' }}>
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="rgba(255,255,255,0.3)"
          strokeWidth={strokeWidth}
          fill="none"
        />
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

  const handleContinueConversation = (item: typeof mockInProgress[0]) => {
    navigation.navigate('Chat', {
      avatar: {
        id: item.avatarId,
        name_ko: item.avatarName,
        icon: item.avatarIcon,
        avatarBg: item.avatarBg,
        difficulty: item.difficulty,
      },
      situation: { name_ko: item.situation },
    });
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>

        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity 
            style={styles.profileRow} 
            onPress={() => navigation.navigate('My Profile')}
          >
            <Image source={{ uri: mockUser.avatarUrl }} style={styles.avatar} />
            <View style={styles.greetingText}>
              <Text style={styles.hello}>안녕하세요!</Text>
              <Text style={styles.username}>{mockUser.name}</Text>
            </View>
          </TouchableOpacity>
          <TouchableOpacity style={styles.notifButton}>
            <Bell size={24} color="#1A1A2E" />
          </TouchableOpacity>
        </View>

        {/* Main CTA Card */}
        <View style={styles.ctaCard}>
          <View style={styles.ctaTop}>
            <Text style={styles.ctaTitle}>
              한국어 실력을{'\n'}매일 향상시켜보세요!
            </Text>
            <CircularProgress percentage={85} />
          </View>
          <View style={styles.ctaButtons}>
            <Button
              title="대화 시작"
              onPress={() => navigation.navigate('AvatarSelection')}
              variant="outline"
              size="medium"
              showArrow
              style={styles.ctaBtn}
            />
            <Button
              title="궁합 분석"
              onPress={() => navigation.navigate('AvatarCompatibility', { 
                interests: mockUser.interests 
              })}
              variant="ghost"
              size="medium"
              showArrow={false}
              style={styles.ctaBtnGhost}
            />
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <TouchableOpacity 
            style={styles.quickAction}
            onPress={() => navigation.navigate('AvatarSelection')}
          >
            <View style={[styles.quickIcon, { backgroundColor: '#F0EDFF' }]}>
              <MessageCircle size={24} color="#6C3BFF" />
            </View>
            <Text style={styles.quickLabel}>새 대화</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.quickAction}
            onPress={() => navigation.navigate('AvatarCompatibility', {
              interests: mockUser.interests
            })}
          >
            <View style={[styles.quickIcon, { backgroundColor: '#FFEBEE' }]}>
              <Heart size={24} color="#E53935" />
            </View>
            <Text style={styles.quickLabel}>궁합 분석</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.quickAction}
            onPress={() => navigation.navigate('Main', { screen: 'Real-time' })}
          >
            <View style={[styles.quickIcon, { backgroundColor: '#E8F5E9' }]}>
              <Mic size={24} color="#4CAF50" />
            </View>
            <Text style={styles.quickLabel}>실시간</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.quickAction}
            onPress={() => navigation.navigate('Main', { screen: 'Avatar' })}
          >
            <View style={[styles.quickIcon, { backgroundColor: '#FFF0E0' }]}>
              <Users size={24} color="#F4A261" />
            </View>
            <Text style={styles.quickLabel}>아바타</Text>
          </TouchableOpacity>
        </View>

        {/* In Progress - Now showing mood and difficulty */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>진행 중</Text>
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{mockInProgress.length}</Text>
          </View>
        </View>

        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.horizontalScroll}
          contentContainerStyle={styles.horizontalContent}
        >
          {mockInProgress.map((item) => {
            const moodConfig = getMoodConfig(item.mood);
            const MoodIcon = moodConfig.icon;

            return (
              <Card 
                key={item.id} 
                variant="elevated" 
                style={styles.progressCard}
                onPress={() => handleContinueConversation(item)}
              >
                {/* Avatar header */}
                <View style={styles.progressAvatarRow}>
                  <View style={[styles.progressAvatarIcon, { backgroundColor: item.avatarBg }]}>
                    <Icon name={item.avatarIcon} size={20} color="#FFFFFF" />
                  </View>
                  <StatusBadge status={item.difficulty} />
                </View>

                {/* Avatar name & situation */}
                <Text style={styles.progressAvatarName}>{item.avatarName}</Text>
                <Text style={styles.progressSituation}>{item.situation}</Text>

                {/* Mood indicator */}
                <View style={styles.moodRow}>
                  <MoodIcon size={16} color={moodConfig.color} />
                  <Text style={[styles.moodText, { color: moodConfig.color }]}>
                    기분: {moodConfig.label}
                  </Text>
                </View>

                {/* Mood bar */}
                <View style={styles.moodBarTrack}>
                  <View 
                    style={[
                      styles.moodBarFill, 
                      { 
                        width: `${item.mood}%`,
                        backgroundColor: moodConfig.color,
                      }
                    ]} 
                  />
                </View>
              </Card>
            );
          })}
        </ScrollView>

        {/* Stats */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>통계</Text>
        </View>

        <View style={styles.statsRow}>
          {mockStats.map((stat) => (
            <Card key={stat.id} variant="elevated" style={styles.statCard}>
              <Icon name={stat.icon} size={28} color={stat.color} />
              <Text style={styles.statCount}>
                {stat.count}{stat.unit || ''}
              </Text>
              <Text style={styles.statTitle}>{stat.title}</Text>
            </Card>
          ))}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  container: { paddingHorizontal: 20, paddingTop: 16, paddingBottom: 32 },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  profileRow: { flexDirection: 'row', alignItems: 'center' },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    marginRight: 12,
    backgroundColor: '#E8E8F0',
  },
  greetingText: { justifyContent: 'center' },
  hello: { fontSize: 13, color: '#6C6C80' },
  username: { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },
  notifButton: { padding: 8 },

  ctaCard: {
    backgroundColor: '#6C3BFF',
    borderRadius: 20,
    padding: 20,
    marginBottom: 24,
  },
  ctaTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  ctaTitle: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
    lineHeight: 26,
    flex: 1,
  },
  ctaButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  ctaBtn: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  ctaBtnGhost: {
    flex: 1,
  },

  quickActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 28,
  },
  quickAction: { alignItems: 'center' },
  quickIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  quickLabel: { fontSize: 12, color: '#6C6C80', fontWeight: '500' },

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

  horizontalScroll: { marginBottom: 28 },
  horizontalContent: { gap: 12 },
  
  progressCard: { 
    width: 180, 
    minHeight: 140,
  },
  progressAvatarRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  progressAvatarIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  progressAvatarName: { 
    fontSize: 16, 
    fontWeight: '700', 
    color: '#1A1A2E', 
    marginBottom: 2,
  },
  progressSituation: { 
    fontSize: 12, 
    color: '#6C6C80', 
    marginBottom: 12,
  },
  moodRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 8,
  },
  moodText: {
    fontSize: 12,
    fontWeight: '600',
  },
  moodBarTrack: {
    height: 6,
    backgroundColor: '#E2E2EC',
    borderRadius: 3,
    overflow: 'hidden',
  },
  moodBarFill: {
    height: '100%',
    borderRadius: 3,
  },

  statsRow: { flexDirection: 'row', gap: 12 },
  statCard: { flex: 1, alignItems: 'center', paddingVertical: 20 },
  statCount: { fontSize: 20, fontWeight: '700', color: '#1A1A2E', marginTop: 8, marginBottom: 4 },
  statTitle: { fontSize: 11, color: '#6C6C80' },
});

export default HomeScreen;
