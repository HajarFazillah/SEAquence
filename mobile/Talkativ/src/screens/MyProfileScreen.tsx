import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, TouchableOpacity, Image, Switch, Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { 
  ChevronRight, Bell, Moon, Globe, 
  HelpCircle, LogOut, Edit, Heart, BookOpen,
  Award, Clock, TrendingUp, MessageCircle, MessageSquare,
} from 'lucide-react-native';
import { Card, Tag, ProgressBar } from '../components';
import { getMyProfile, getUserStats, UserProfile, UserStats } from '../services/apiUser';

<<<<<<< Updated upstream
=======

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const CARD_WIDTH = (SCREEN_WIDTH - 52) / 2;

>>>>>>> Stashed changes
const mockUser = {
  id: 'user_1',
  name: 'Nunnalin',
  email: 'nunnalin@example.com',
  avatarUrl: 'https://i.pravatar.cc/100?img=47',
  age: 25,
  gender: 'female',
  koreanLevel: 'intermediate',
  interests: ['K-POP', '카페', '여행', '영화', '음식'],
  dislikes: ['정치', '스포츠'],
  memo: '저는 사회적 불안이 있어서 천천히 대화하고 싶어요. 실수해도 친절하게 대해주세요.',
  joinedAt: '2026-01-15',
};

const KOREAN_LEVELS = [
  { id: 'beginner', label: '초급', labelEn: 'Beginner' },
  { id: 'intermediate', label: '중급', labelEn: 'Intermediate' },
  { id: 'advanced', label: '고급', labelEn: 'Advanced' },
];

const MENU_ITEMS = [
  { id: 'notifications', icon: Bell, label: '알림 설정', hasToggle: true },
  { id: 'language', icon: Globe, label: '언어', value: '한국어' },
  { id: 'darkMode', icon: Moon, label: '다크 모드', hasToggle: true },
  { id: 'help', icon: HelpCircle, label: '도움말' },
  { id: 'logout', icon: LogOut, label: '로그아웃', danger: true },
];

export const MyProfileScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [realUser, setRealUser] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<UserStats>({
    completedSessions: 0,
    learnedExpressions: 0,
    practiceMinutes: 0,
    progressPercent: 0,
  });

  useEffect(() => {
    getMyProfile()
      .then(data => setRealUser(data))
      .catch(err => console.log('Profile fetch failed:', err));

    getUserStats()
      .then(data => setStats(data))
      .catch(err => console.log('Stats fetch failed:', err));
  }, []);

  const displayName = realUser?.username ?? mockUser.name;
  const displayEmail = realUser?.email ?? mockUser.email;
  const displayLevel = realUser?.koreanLevel ?? mockUser.koreanLevel;
  const displayAvatar = realUser?.avatarUrl ?? mockUser.avatarUrl;
  const displayMemo = realUser?.memo ?? mockUser.memo;
  const displayInterests = realUser?.interests && realUser.interests.length > 0 
    ? realUser.interests 
    : mockUser.interests;
  const displayDislikes = realUser?.dislikes && realUser.dislikes.length > 0
    ? realUser.dislikes
    : mockUser.dislikes;

  const handleEditProfile = () => {
    navigation.navigate('EditProfile');
  };

  const handleEditInterests = () => {
    navigation.navigate('EditInterests', { 
      interests: displayInterests,
      dislikes: displayDislikes,
    });
  };

  const handleViewWords = () => {
    navigation.navigate('SavedVocabulary', { type: 'words' });
  };

  const handleViewPhrases = () => {
    navigation.navigate('SavedVocabulary', { type: 'phrases' });
  };

  const handleMenuPress = (itemId: string) => {
    switch (itemId) {
      case 'notifications':
        setNotifications(!notifications);
        break;
      case 'darkMode':
        setDarkMode(!darkMode);
        break;
      case 'help':
        break;
      case 'logout':
        navigation.navigate('Login');
        break;
    }
  };

  const level = KOREAN_LEVELS.find(l => l.id === displayLevel);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Profile Header Card */}
        <View style={styles.profileCard}>
          <View style={styles.profileCardContent}>
            <View style={styles.avatarContainer}>
              <Image source={{ uri: displayAvatar }} style={styles.avatar} />
              <TouchableOpacity style={styles.editAvatarBtn} onPress={handleEditProfile}>
                <Edit size={12} color="#FFFFFF" />
              </TouchableOpacity>
            </View>
            <View style={styles.profileInfo}>
              <Text style={styles.userName}>{displayName}</Text>
              <Text style={styles.userEmail}>{displayEmail}</Text>
              <View style={styles.levelBadge}>
                <Text style={styles.levelText}>{level?.label} ({level?.labelEn})</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Memo Section */}
        {displayMemo && (
          <Card variant="elevated" style={styles.memoCard}>
            <View style={styles.memoHeader}>
              <MessageSquare size={18} color="#6C3BFF" />
              <Text style={styles.memoTitle}>AI 참고 메모</Text>
              <TouchableOpacity onPress={handleEditProfile} style={styles.memoEditBtn}>
                <Edit size={14} color="#6C3BFF" />
              </TouchableOpacity>
            </View>
            <Text style={styles.memoText}>{displayMemo}</Text>
          </Card>
        )}

        {/* Learning Stats */}
        <Text style={styles.sectionTitle}>학습 기록</Text>
        
        {/* Stats Row 1: Words & Phrases (Clickable) */}
        <View style={styles.statsRow}>
          <TouchableOpacity 
            style={[styles.statCard, styles.statCardClickable]} 
            onPress={handleViewWords}
            activeOpacity={0.7}
          >
            <View style={[styles.statIconBg, { backgroundColor: '#F0EDFF' }]}>
              <BookOpen size={22} color="#6C3BFF" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.learnedExpressions}</Text>
              <Text style={styles.statLabel}>배운 단어</Text>
            </View>
            <View style={styles.viewMoreBadge}>
              <Text style={styles.viewMoreText}>보기</Text>
              <ChevronRight size={14} color="#6C3BFF" />
            </View>
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.statCard, styles.statCardClickable]} 
            onPress={handleViewPhrases}
            activeOpacity={0.7}
          >
            <View style={[styles.statIconBg, { backgroundColor: '#E8F5E9' }]}>
              <MessageCircle size={22} color="#4CAF50" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.completedSessions}</Text>
              <Text style={styles.statLabel}>배운 표현</Text>
            </View>
            <View style={[styles.viewMoreBadge, { backgroundColor: '#E8F5E9' }]}>
              <Text style={[styles.viewMoreText, { color: '#4CAF50' }]}>보기</Text>
              <ChevronRight size={14} color="#4CAF50" />
            </View>
          </TouchableOpacity>
        </View>

        {/* Stats Row 2: Streak & Time */}
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <View style={[styles.statIconBg, { backgroundColor: '#FFF3E0' }]}>
              <Award size={22} color="#F4A261" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.completedSessions}일</Text>
              <Text style={styles.statLabel}>연속 학습</Text>
            </View>
          </View>

          <View style={styles.statCard}>
            <View style={[styles.statIconBg, { backgroundColor: '#FFEBEE' }]}>
              <Clock size={22} color="#E53935" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.practiceMinutes}분</Text>
              <Text style={styles.statLabel}>연습 시간</Text>
            </View>
          </View>
        </View>

        {/* Interests Section */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <Heart size={18} color="#E53935" />
              <Text style={styles.sectionTitleText}>관심사</Text>
            </View>
            <TouchableOpacity onPress={handleEditInterests} style={styles.editBtn}>
              <Edit size={14} color="#6C3BFF" />
              <Text style={styles.editLink}>수정</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.tagContainer}>
            {displayInterests.map((interest, i) => (
              <Tag key={i} label={interest} selected />
            ))}
          </View>
          
          <View style={styles.divider} />
          
          <Text style={styles.sectionSubtitle}>피하고 싶은 주제</Text>
          <View style={styles.tagContainer}>
            {displayDislikes.map((dislike, i) => (
              <Tag key={i} label={dislike} variant="outline" />
            ))}
          </View>
        </Card>

        {/* Learning Progress */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <TrendingUp size={18} color="#6C3BFF" />
              <Text style={styles.sectionTitleText}>학습 진행도</Text>
            </View>
          </View>
          
          <View style={styles.progressItem}>
            <View style={styles.progressHeader}>
              <Text style={styles.progressText}>말투 정확도</Text>
              <Text style={[styles.progressPercent, { color: '#6C3BFF' }]}>
                {stats.progressPercent}%
              </Text>
            </View>
            <ProgressBar progress={stats.progressPercent / 100} color="#6C3BFF" />
          </View>
          
          <View style={styles.progressItem}>
            <View style={styles.progressHeader}>
              <Text style={styles.progressText}>어휘력</Text>
              <Text style={[styles.progressPercent, { color: '#4CAF50' }]}>65%</Text>
            </View>
            <ProgressBar progress={0.65} color="#4CAF50" />
          </View>
          
          <View style={[styles.progressItem, { marginBottom: 0 }]}>
            <View style={styles.progressHeader}>
              <Text style={styles.progressText}>자연스러움</Text>
              <Text style={[styles.progressPercent, { color: '#F4A261' }]}>82%</Text>
            </View>
            <ProgressBar progress={0.82} color="#F4A261" />
          </View>
        </Card>

        {/* Settings Menu */}
        <Text style={styles.sectionTitle}>설정</Text>
        <Card variant="elevated" style={styles.menuCard}>
          {MENU_ITEMS.map((item, index) => (
            <TouchableOpacity 
              key={item.id}
              style={[
                styles.menuItem,
                index < MENU_ITEMS.length - 1 && styles.menuItemBorder,
              ]}
              onPress={() => handleMenuPress(item.id)}
            >
              <View style={styles.menuItemLeft}>
                <View style={[
                  styles.menuIconBg,
                  item.danger && { backgroundColor: '#FFEBEE' },
                ]}>
                  <item.icon 
                    size={18} 
                    color={item.danger ? '#E53935' : '#6C6C80'} 
                  />
                </View>
                <Text style={[
                  styles.menuItemLabel,
                  item.danger && styles.menuItemLabelDanger,
                ]}>
                  {item.label}
                </Text>
              </View>
              
              {item.hasToggle ? (
                <Switch
                  value={item.id === 'notifications' ? notifications : darkMode}
                  onValueChange={() => handleMenuPress(item.id)}
                  trackColor={{ false: '#E2E2EC', true: '#6C3BFF' }}
                  thumbColor="#FFFFFF"
                />
              ) : item.value ? (
                <View style={styles.menuItemRight}>
                  <Text style={styles.menuItemValue}>{item.value}</Text>
                  <ChevronRight size={18} color="#B0B0C5" />
                </View>
              ) : !item.danger ? (
                <ChevronRight size={18} color="#B0B0C5" />
              ) : null}
            </TouchableOpacity>
          ))}
        </Card>

        {/* App Version */}
        <Text style={styles.version}>Talkativ v1.0.0</Text>

      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 40 },

  profileCard: {
    backgroundColor: '#6C3BFF',
    borderRadius: 20,
    padding: 20,
    marginTop: 16,
    marginBottom: 24,
  },
  profileCardContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    position: 'relative',
    marginRight: 16,
  },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#E8E8F0',
    borderWidth: 3,
    borderColor: 'rgba(255,255,255,0.3)',
  },
  editAvatarBtn: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#1A1A2E',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#6C3BFF',
  },
  profileInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.7)',
    marginBottom: 10,
  },
  levelBadge: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  levelText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },

  memoCard: {
    marginBottom: 20,
  },
  memoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  memoTitle: {
    flex: 1,
    fontSize: 14,
    fontWeight: '700',
    color: '#1A1A2E',
  },
  memoEditBtn: {
    padding: 4,
  },
  memoText: {
    fontSize: 14,
    color: '#6C6C80',
    lineHeight: 20,
  },

  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 12,
  },

  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 8,
    elevation: 2,
  },
  statCardClickable: {
    borderWidth: 1,
    borderColor: '#F0F0F5',
  },
  statIconBg: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  statTextContainer: {
    flex: 1,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A2E',
  },
  statLabel: {
    fontSize: 11,
    color: '#6C6C80',
    marginTop: 2,
  },
  viewMoreBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0EDFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  viewMoreText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#6C3BFF',
  },

  sectionCard: {
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sectionTitleText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
  },
  sectionSubtitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6C6C80',
    marginBottom: 10,
  },
  editBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#F0EDFF',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
  },
  editLink: {
    fontSize: 12,
    color: '#6C3BFF',
    fontWeight: '600',
  },
  tagContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  divider: {
    height: 1,
    backgroundColor: '#F0F0F5',
    marginVertical: 16,
  },

  progressItem: {
    marginBottom: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressText: {
    fontSize: 14,
    color: '#1A1A2E',
  },
  progressPercent: {
    fontSize: 14,
    fontWeight: '700',
  },

  menuCard: {
    padding: 0,
    overflow: 'hidden',
    marginBottom: 20,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  menuItemBorder: {
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F5',
  },
  menuItemLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  menuIconBg: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#F5F5FA',
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuItemLabel: {
    fontSize: 15,
    color: '#1A1A2E',
    fontWeight: '500',
  },
  menuItemLabelDanger: {
    color: '#E53935',
  },
  menuItemRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  menuItemValue: {
    fontSize: 14,
    color: '#6C6C80',
  },

  version: {
    textAlign: 'center',
    fontSize: 12,
    color: '#B0B0C5',
    marginTop: 8,
  },
});

export default MyProfileScreen;
