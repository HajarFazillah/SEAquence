import React, { useEffect, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, TouchableOpacity, Image, Switch, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import {
  ChevronRight, Bell, Moon, Globe,
  HelpCircle, LogOut, Edit, Heart, BookOpen,
  Award, Clock, TrendingUp, MessageCircle, MessageSquare,
  User, Sparkles, Camera,
} from 'lucide-react-native';
import { launchImageLibrary } from 'react-native-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Card, Header, Tag } from '../components';
import { getMyProfile, getUserStats, UserProfile, UserStats } from '../services/apiUser';

// ─── Constants ────────────────────────────────────────────────────────────────

const CUSTOM_AVATAR_KEY = 'custom_avatar_url';

const mockUser = {
  name: 'Nunnalin',
  email: 'nunnalin@example.com',
  avatarUrl: 'https://i.pravatar.cc/100?img=47',
  age: '25',
  gender: 'female',
  koreanLevel: 'intermediate',
  nativeLang: 'English',
  targetLang: 'Korean',
  interests: ['K-POP', '카페', '여행', '영화', '음식'],
  dislikes: ['정치', '스포츠'],
  memo: '저는 사회적 불안이 있어서 천천히 대화하고 싶어요. 실수해도 친절하게 대해주세요.',
};

const KOREAN_LEVELS: Record<string, { label: string; labelEn: string }> = {
  beginner:     { label: '초급', labelEn: 'Beginner' },
  intermediate: { label: '중급', labelEn: 'Intermediate' },
  advanced:     { label: '고급', labelEn: 'Advanced' },
};

const GENDER_LABELS: Record<string, string> = {
  male:   '남성',
  female: '여성',
  other:  '기타',
};

const MENU_ITEMS = [
  { id: 'notifications', icon: Bell,        label: '알림 설정',  hasToggle: true },
  { id: 'language',      icon: Globe,       label: '언어',       value: '한국어' },
  { id: 'darkMode',      icon: Moon,        label: '다크 모드',  hasToggle: true },
  { id: 'help',          icon: HelpCircle,  label: '도움말' },
  { id: 'logout',        icon: LogOut,      label: '로그아웃',   danger: true },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

const InfoItem = ({ label, value }: { label: string; value: string }) => (
  <View style={styles.infoItem}>
    <Text style={styles.infoLabel}>{label}</Text>
    <Text style={styles.infoValue}>{value}</Text>
  </View>
);

// ─── Screen ───────────────────────────────────────────────────────────────────

export const MyProfileScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const [notifications,   setNotifications]   = useState(true);
  const [darkMode,        setDarkMode]        = useState(false);
  const [realUser,        setRealUser]        = useState<UserProfile | null>(null);
  const [stats,           setStats]           = useState<UserStats>({
    completedSessions:  0,
    learnedExpressions: 0,
    practiceMinutes:    0,
    progressPercent:    0,
  });
  // Friend's addition: local override for the profile picture
  const [customAvatarUrl, setCustomAvatarUrl] = useState<string | null>(null);

  useEffect(() => {
    getMyProfile()
      .then(data => setRealUser(data))
      .catch(err => console.log('Profile fetch failed:', err));

    getUserStats()
      .then(data => setStats(data))
      .catch(err => console.log('Stats fetch failed:', err));

    // Friend's addition: restore any previously saved custom avatar
    AsyncStorage.getItem(CUSTOM_AVATAR_KEY)
      .then(saved => { if (saved) setCustomAvatarUrl(saved); })
      .catch(err => console.log('Failed to load custom avatar:', err));
  }, []);

  const display = useMemo(() => {
    const koreanLevel = realUser?.koreanLevel ?? mockUser.koreanLevel;
    return {
      name:             realUser?.username    ?? mockUser.name,
      // customAvatarUrl takes priority, then backend avatar, then mock
      avatarUrl:        customAvatarUrl ?? realUser?.avatarUrl ?? mockUser.avatarUrl,
      age:              realUser?.age         ?? mockUser.age,
      gender:           realUser?.gender      ?? mockUser.gender,
      koreanLevel,
      koreanLevelLabel: KOREAN_LEVELS[koreanLevel]?.label   ?? '중급',
      koreanLevelEn:    KOREAN_LEVELS[koreanLevel]?.labelEn ?? 'Intermediate',
      nativeLang:       realUser?.nativeLang  ?? mockUser.nativeLang,
      memo:             realUser?.memo        ?? mockUser.memo,
      interests:        realUser?.interests && realUser.interests.length > 0 ? realUser.interests : mockUser.interests,
      dislikes:         realUser?.dislikes  && realUser.dislikes.length  > 0 ? realUser.dislikes  : mockUser.dislikes,
      genderLabel:      GENDER_LABELS[realUser?.gender ?? mockUser.gender] ?? '미설정',
    };
  }, [realUser, customAvatarUrl]); // re-derive whenever customAvatarUrl changes

  // ── Handlers ───────────────────────────────────────────────────────────────

  // Friend's addition: pick a new photo or revert to default
  const handleChangePhoto = () => {
    Alert.alert(
      '프로필 사진 변경',
      '사진을 선택하거나 기본 사진으로 되돌릴 수 있어요.',
      [
        {
          text: '사진 선택',
          onPress: () => {
            launchImageLibrary(
              { mediaType: 'photo', quality: 0.8, selectionLimit: 1 },
              (response) => {
                if (response.didCancel) return;
                if (response.errorCode) {
                  Alert.alert('오류', '사진을 불러오지 못했어요. 다시 시도해주세요.');
                  return;
                }
                const uri = response.assets?.[0]?.uri;
                if (uri) {
                  setCustomAvatarUrl(uri);
                  AsyncStorage.setItem(CUSTOM_AVATAR_KEY, uri)
                    .catch(err => console.log('Failed to save avatar:', err));
                }
              }
            );
          },
        },
        {
          text: '기본 사진으로',
          onPress: () => {
            setCustomAvatarUrl(null);
            AsyncStorage.removeItem(CUSTOM_AVATAR_KEY)
              .catch(err => console.log('Failed to remove avatar:', err));
          },
        },
        { text: '취소', style: 'cancel' },
      ]
    );
  };

  const handleEditProfile    = () => navigation.navigate('EditProfile');
  const handleEditInterests  = () => navigation.navigate('EditInterests', {
    interests: display.interests,
    dislikes:  display.dislikes,
  });
  const handleViewWords      = () => navigation.navigate('SavedVocabulary', { type: 'words' });
  const handleViewPhrases    = () => navigation.navigate('SavedVocabulary', { type: 'phrases' });

  const handleMenuPress = (itemId: string) => {
    switch (itemId) {
      case 'notifications': setNotifications(prev => !prev); break;
      case 'darkMode':      setDarkMode(prev => !prev);      break;
      case 'logout':        navigation.navigate('Login');     break;
      default: break;
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="프로필" showBack={false} showBell />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* ── Hero card ── */}
        <Card variant="elevated" style={styles.heroCard}>
          <View style={styles.heroTopRow}>
            <View style={styles.avatarWrap}>
              <Image source={{ uri: display.avatarUrl }} style={styles.avatar} />
              {/* Camera icon opens photo picker; Edit navigates to profile form */}
              <TouchableOpacity style={styles.editAvatarBtn} onPress={handleChangePhoto}>
                <Camera size={12} color="#FFFFFF" />
              </TouchableOpacity>
            </View>
            <View style={styles.heroCopy}>
              <Text style={styles.userName}>{display.name}</Text>
              <View style={styles.levelChip}>
                <Sparkles size={12} color="#6C3BFF" />
                <Text style={styles.levelChipText}>
                  {display.koreanLevelLabel} · {display.koreanLevelEn}
                </Text>
              </View>
            </View>
          </View>

          <View style={styles.heroStatsRow}>
            <View style={styles.heroStatBox}>
              <Text style={styles.heroStatValue}>{stats.completedSessions}</Text>
              <Text style={styles.heroStatLabel}>대화 완료</Text>
            </View>
            <View style={styles.heroStatDivider} />
            <View style={styles.heroStatBox}>
              <Text style={styles.heroStatValue}>{stats.learnedExpressions}</Text>
              <Text style={styles.heroStatLabel}>배운 표현</Text>
            </View>
            <View style={styles.heroStatDivider} />
            <View style={styles.heroStatBox}>
              <Text style={styles.heroStatValue}>{stats.practiceMinutes}분</Text>
              <Text style={styles.heroStatLabel}>연습 시간</Text>
            </View>
          </View>
        </Card>

        {/* ── 기본 정보 ── */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <User size={18} color="#6C3BFF" />
              <Text style={styles.sectionTitleText}>기본 정보</Text>
            </View>
            <TouchableOpacity onPress={handleEditProfile} style={styles.editBtn}>
              <Edit size={14} color="#6C3BFF" />
              <Text style={styles.editLink}>수정</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.infoGrid}>
            <InfoItem label="이름" value={display.name} />
            <InfoItem label="나이" value={display.age ? `${display.age}세` : '미설정'} />
            <InfoItem label="성별" value={display.genderLabel} />
          </View>
        </Card>

        {/* ── 학습 프로필 ── */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <MessageCircle size={18} color="#4CAF50" />
              <Text style={styles.sectionTitleText}>학습 프로필</Text>
            </View>
          </View>
          <View style={styles.infoGrid}>
            <InfoItem label="모국어" value={display.nativeLang || '미설정'} />
            <InfoItem label="한국어 수준" value={`${display.koreanLevelLabel} (${display.koreanLevelEn})`} />
            <InfoItem label="학습 진행도" value={`${stats.progressPercent}%`} />
          </View>
        </Card>

        {/* ── 관심사 ── */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <Heart size={18} color="#E85D8E" />
              <Text style={styles.sectionTitleText}>관심사와 피하고 싶은 주제</Text>
            </View>
            <TouchableOpacity onPress={handleEditInterests} style={styles.editBtn}>
              <Edit size={14} color="#6C3BFF" />
              <Text style={styles.editLink}>수정</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.groupLabel}>관심사</Text>
          <View style={styles.tagWrap}>
            {display.interests.map((interest, i) => (
              <Tag key={i} label={interest} selected />
            ))}
          </View>
          <View style={styles.divider} />
          <Text style={styles.groupLabel}>피하고 싶은 주제</Text>
          <View style={styles.tagWrap}>
            {display.dislikes.map((dislike, i) => (
              <Tag key={i} label={dislike} variant="outline" />
            ))}
          </View>
        </Card>

        {/* ── AI 참고 메모 ── */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <MessageSquare size={18} color="#6C3BFF" />
              <Text style={styles.sectionTitleText}>AI 참고 메모</Text>
            </View>
            <TouchableOpacity onPress={handleEditProfile} style={styles.editBtn}>
              <Edit size={14} color="#6C3BFF" />
              <Text style={styles.editLink}>수정</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.memoText}>{display.memo || '아직 작성된 메모가 없어요.'}</Text>
        </Card>

        {/* ── 학습 기록 ── */}
        <Text style={styles.sectionTitle}>학습 기록</Text>
        <View style={styles.statsRow}>
          <TouchableOpacity style={[styles.statCard, styles.statCardClickable]} onPress={handleViewWords} activeOpacity={0.75}>
            <View style={[styles.statIconBg, { backgroundColor: '#F0EDFF' }]}>
              <BookOpen size={20} color="#6C3BFF" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.learnedExpressions}</Text>
              <Text style={styles.statLabel}>배운 단어</Text>
            </View>
            <ChevronRight size={18} color="#B0B0C5" />
          </TouchableOpacity>

          <TouchableOpacity style={[styles.statCard, styles.statCardClickable]} onPress={handleViewPhrases} activeOpacity={0.75}>
            <View style={[styles.statIconBg, { backgroundColor: '#E8F5E9' }]}>
              <MessageCircle size={20} color="#4CAF50" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.completedSessions}</Text>
              <Text style={styles.statLabel}>배운 표현</Text>
            </View>
            <ChevronRight size={18} color="#B0B0C5" />
          </TouchableOpacity>
        </View>

        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <View style={[styles.statIconBg, { backgroundColor: '#FFF3E0' }]}>
              <Award size={20} color="#F4A261" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.completedSessions}일</Text>
              <Text style={styles.statLabel}>연속 학습</Text>
            </View>
          </View>

          <View style={styles.statCard}>
            <View style={[styles.statIconBg, { backgroundColor: '#FFEBEE' }]}>
              <Clock size={20} color="#E53935" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.practiceMinutes}분</Text>
              <Text style={styles.statLabel}>연습 시간</Text>
            </View>
          </View>
        </View>

        {/* ── 설정 ── */}
        <Text style={styles.sectionTitle}>설정</Text>
        <Card variant="elevated" style={styles.menuCard}>
          {MENU_ITEMS.map((item, index) => (
            <TouchableOpacity
              key={item.id}
              style={[styles.menuItem, index < MENU_ITEMS.length - 1 && styles.menuItemBorder]}
              onPress={() => handleMenuPress(item.id)}
            >
              <View style={styles.menuItemLeft}>
                <View style={[styles.menuIconBg, item.danger && { backgroundColor: '#FFEBEE' }]}>
                  <item.icon size={18} color={item.danger ? '#E53935' : '#6C6C80'} />
                </View>
                <Text style={[styles.menuItemLabel, item.danger && styles.menuItemLabelDanger]}>
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

        <Text style={styles.version}>Talkativ v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
};

// ─── Styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe:    { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 40 },

  // Hero
  heroCard:       { marginTop: 16, marginBottom: 18, padding: 20, borderRadius: 22 },
  heroTopRow:     { flexDirection: 'row', alignItems: 'center' },
  avatarWrap:     { position: 'relative', marginRight: 16 },
  avatar:         { width: 82, height: 82, borderRadius: 41, backgroundColor: '#ECECF4' },
  editAvatarBtn:  {
    position: 'absolute', right: -2, bottom: -2,
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center',
    borderWidth: 2, borderColor: '#FFFFFF',
  },
  heroCopy:       { flex: 1 },
  userName:       { fontSize: 24, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  levelChip:      {
    flexDirection: 'row', alignItems: 'center', gap: 6, alignSelf: 'flex-start',
    backgroundColor: '#F3EEFF', paddingHorizontal: 12, paddingVertical: 7, borderRadius: 999,
  },
  levelChipText:  { fontSize: 12, fontWeight: '600', color: '#6C3BFF' },
  heroStatsRow:   {
    flexDirection: 'row', alignItems: 'center',
    marginTop: 18, paddingTop: 18,
    borderTopWidth: 1, borderTopColor: '#F0F0F5',
  },
  heroStatBox:     { flex: 1, alignItems: 'center' },
  heroStatDivider: { width: 1, height: 34, backgroundColor: '#F0F0F5' },
  heroStatValue:   { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  heroStatLabel:   { fontSize: 11, color: '#7A7A92' },

  // Section cards
  sectionTitle:    { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 12 },
  sectionCard:     { marginBottom: 16, borderRadius: 20 },
  sectionHeader:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 },
  sectionTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sectionTitleText:{ fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  editBtn:         {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#F3EEFF', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 10,
  },
  editLink:        { fontSize: 12, fontWeight: '600', color: '#6C3BFF' },

  // Info grid
  infoGrid:  { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  infoItem:  { width: '48%', backgroundColor: '#FAFAFD', borderRadius: 16, padding: 12, minHeight: 76 },
  infoLabel: { fontSize: 11, fontWeight: '600', color: '#8E8EA4', marginBottom: 6 },
  infoValue: { fontSize: 14, lineHeight: 20, color: '#1A1A2E', fontWeight: '600' },

  // Tags
  groupLabel: { fontSize: 12, fontWeight: '600', color: '#6C6C80', marginBottom: 10 },
  tagWrap:    { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  divider:    { height: 1, backgroundColor: '#F0F0F5', marginVertical: 16 },
  memoText:   { fontSize: 14, lineHeight: 21, color: '#56566F' },

  // Stats
  statsRow:         { flexDirection: 'row', gap: 12, marginBottom: 12 },
  statCard:         {
    flex: 1, backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16,
    flexDirection: 'row', alignItems: 'center',
  },
  statCardClickable:{ borderWidth: 1, borderColor: '#F0F0F5' },
  statIconBg:       { width: 42, height: 42, borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  statTextContainer:{ flex: 1 },
  statValue:        { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },
  statLabel:        { fontSize: 11, color: '#6C6C80', marginTop: 2 },

  // Menu
  menuCard:            { padding: 0, overflow: 'hidden', marginBottom: 20 },
  menuItem:            { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 14 },
  menuItemBorder:      { borderBottomWidth: 1, borderBottomColor: '#F0F0F5' },
  menuItemLeft:        { flexDirection: 'row', alignItems: 'center', gap: 12 },
  menuIconBg:          { width: 36, height: 36, borderRadius: 10, backgroundColor: '#F5F5FA', alignItems: 'center', justifyContent: 'center' },
  menuItemLabel:       { fontSize: 15, color: '#1A1A2E', fontWeight: '500' },
  menuItemLabelDanger: { color: '#E53935' },
  menuItemRight:       { flexDirection: 'row', alignItems: 'center', gap: 4 },
  menuItemValue:       { fontSize: 14, color: '#6C6C80' },

  version: { textAlign: 'center', fontSize: 12, color: '#B0B0C5', marginTop: 8 },
});

export default MyProfileScreen;