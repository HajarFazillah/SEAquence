import React, { useEffect, useMemo, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Switch,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { fetchMyVocabulary } from '../services/apiVocabulary';
import { logoutUser } from '../services/apiAuth';
import {
  ChevronRight,
  Globe,
  LogOut,
  Edit,
  Heart,
  BookOpen,
  MessageCircle,
  MessageSquare,
  User,
  Sparkles,
  Camera,
  Trash2,
} from 'lucide-react-native';
import { launchImageLibrary } from 'react-native-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Card, Header, Tag } from '../components';
import {
  getMyProfile,
  getUserStats,
  UserProfile,
  UserStats,
} from '../services/apiUser';
import { deleteAllMyMistakes } from '../services/apiMistakes';
import { deleteAllMySessions } from '../services/apiSession';
import { deleteAllMyVocabulary } from '../services/apiVocabulary';

// ─── Constants ────────────────────────────────────────────────────────────────

const CUSTOM_AVATAR_KEY = 'custom_avatar_url';

const mockUser = {
  name: 'New User',
  email: 'newuser@example.com',
  avatarUrl: 'https://api.dicebear.com/9.x/thumbs/png?seed=NewUser',
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
  beginner: { label: '초급', labelEn: 'Beginner' },
  intermediate: { label: '중급', labelEn: 'Intermediate' },
  advanced: { label: '고급', labelEn: 'Advanced' },
};

const GENDER_LABELS: Record<string, string> = {
  male: '남성',
  female: '여성',
  other: '기타',
};

const MENU_ITEMS = [
  { id: 'language', icon: Globe, label: '언어', value: '한국어' },
  { id: 'reset', icon: Trash2, label: '데이터 초기화', warning: true },
  { id: 'logout', icon: LogOut, label: '로그아웃', danger: true },
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
  const [realUser, setRealUser] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<UserStats>({
    completedSessions: 0,
    learnedExpressions: 0,
    practiceMinutes: 0,
    progressPercent: 0,
  });
  // Friend's addition: local override for the profile picture
  const [customAvatarUrl, setCustomAvatarUrl] = useState<string | null>(null);

  useEffect(() => {
    getMyProfile()
      .then(data => setRealUser(data))
      .catch(err => console.log('Profile fetch failed:', err));

    AsyncStorage.getItem(CUSTOM_AVATAR_KEY)
      .then(saved => {
        if (saved) setCustomAvatarUrl(saved);
      })
      .catch(err => console.log('Failed to load custom avatar:', err));
  }, []);

  // Refetch profile, stats, and vocab counts every time the profile screen
  // regains focus, so edits made on child screens are reflected immediately.
  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      (async () => {
        const [profileRes, statsRes, vocabRes] = await Promise.allSettled([
          getMyProfile(),
          getUserStats(),
          fetchMyVocabulary(),
        ]);
        if (cancelled) return;

        if (profileRes.status === 'fulfilled') {
          setRealUser(profileRes.value);
        }

        const base: UserStats =
          statsRes.status === 'fulfilled'
            ? statsRes.value
            : {
                completedSessions: 0,
                learnedExpressions: 0,
                practiceMinutes: 0,
                progressPercent: 0,
              };

        if (vocabRes.status === 'fulfilled') {
          const words = vocabRes.value.filter(v => v.kind === 'word').length;
          const phrases = vocabRes.value.filter(
            v => v.kind === 'phrase',
          ).length;
          setStats({ ...base, learnedWords: words, learnedPhrases: phrases });
        } else {
          setStats({ ...base, learnedWords: 0, learnedPhrases: 0 });
        }
      })();
      return () => {
        cancelled = true;
      };
    }, []),
  );

  const display = useMemo(() => {
    const koreanLevel = realUser?.koreanLevel ?? mockUser.koreanLevel;
    return {
      name: realUser?.username ?? mockUser.name,
      // customAvatarUrl takes priority, then backend avatar, then mock
      avatarUrl: customAvatarUrl ?? realUser?.avatarUrl ?? mockUser.avatarUrl,
      age: realUser?.age ?? mockUser.age,
      gender: realUser?.gender ?? mockUser.gender,
      koreanLevel,
      koreanLevelLabel: KOREAN_LEVELS[koreanLevel]?.label ?? '중급',
      koreanLevelEn: KOREAN_LEVELS[koreanLevel]?.labelEn ?? 'Intermediate',
      nativeLang: realUser?.nativeLang ?? mockUser.nativeLang,
      memo: realUser?.memo ?? mockUser.memo,
      interests: realUser?.interests ?? [],
      dislikes: realUser?.dislikes ?? [],
      genderLabel:
        GENDER_LABELS[realUser?.gender ?? mockUser.gender] ?? '미설정',
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
              response => {
                if (response.didCancel) return;
                if (response.errorCode) {
                  Alert.alert(
                    '오류',
                    '사진을 불러오지 못했어요. 다시 시도해주세요.',
                  );
                  return;
                }
                const uri = response.assets?.[0]?.uri;
                if (uri) {
                  setCustomAvatarUrl(uri);
                  AsyncStorage.setItem(CUSTOM_AVATAR_KEY, uri).catch(err =>
                    console.log('Failed to save avatar:', err),
                  );
                }
              },
            );
          },
        },
        {
          text: '기본 사진으로',
          onPress: () => {
            setCustomAvatarUrl(null);
            AsyncStorage.removeItem(CUSTOM_AVATAR_KEY).catch(err =>
              console.log('Failed to remove avatar:', err),
            );
          },
        },
        { text: '취소', style: 'cancel' },
      ],
    );
  };

  // ── Data-reset helpers ─────────────────────────────────────────────────────

  const executeReset = useCallback(async (scope: 'local' | 'server' | 'all') => {
    try {
      if (scope === 'local' || scope === 'all') {
        await AsyncStorage.multiRemove([
          'custom_avatar_url',
          'favorite_avatars',
          'custom_situations',
          'talkativ.personalization.events.v1',
        ]);
        setCustomAvatarUrl(null);
      }

      if (scope === 'server' || scope === 'all') {
        const [mistakesRes, sessionsRes, vocabRes] = await Promise.allSettled([
          deleteAllMyMistakes(),
          deleteAllMySessions(),
          deleteAllMyVocabulary(),
        ]);

        const failures = [
          mistakesRes.status === 'rejected' && '실수 기록',
          sessionsRes.status  === 'rejected' && '세션 기록',
          vocabRes.status     === 'rejected' && '단어/표현',
        ].filter(Boolean) as string[];

        if (failures.length > 0) {
          Alert.alert(
            '서버 삭제 실패',
            `다음 항목을 삭제하지 못했어요:\n${failures.map(f => `• ${f}`).join('\n')}\n\n서버 연결을 확인하거나 잠시 후 다시 시도해주세요.`,
          );
          return;
        }

        // Clear local conversation preview cards and per-session histories
        // so the home screen no longer shows stale chat history cards.
        const allKeys = await AsyncStorage.getAllKeys();
        const sessionKeys = allKeys.filter(
          k => k.startsWith('chat_history_') || k.startsWith('realtime_turns_'),
        );
        await AsyncStorage.multiRemove([
          'conversation_previews_v1',
          ...sessionKeys,
        ]);
      }

      Alert.alert('완료', '선택한 데이터가 삭제되었어요.');
    } catch {
      Alert.alert('오류', '데이터 삭제 중 오류가 발생했어요. 다시 시도해주세요.');
    }
  }, []);

  const confirmAndClear = useCallback((scope: 'local' | 'server' | 'all') => {
    const descriptions: Record<typeof scope, string> = {
      local:  '기기에 저장된 프로필 사진, 즐겨찾기, 직접 만든 상황, 연습 패턴 기록이 삭제돼요.',
      server: '서버에 저장된 세션 기록, 실수 기록, 단어/표현이 모두 삭제돼요.',
      all:    '기기 데이터와 서버에 저장된 세션 기록, 실수 기록, 단어/표현이 모두 삭제돼요.',
    };
    Alert.alert(
      '정말 삭제하시겠어요?',
      `${descriptions[scope]}\n\n이 작업은 되돌릴 수 없어요.`,
      [
        { text: '취소', style: 'cancel' },
        { text: '삭제', style: 'destructive', onPress: () => executeReset(scope) },
      ],
    );
  }, [executeReset]);

  const handleEditProfile = () => navigation.navigate('EditProfile');
  const handleEditInterests = () =>
    navigation.navigate('EditInterests', {
      interests: display.interests,
      dislikes: display.dislikes,
    });
  const handleViewWords = () =>
    navigation.navigate('SavedVocabulary', { type: 'words' });
  const handleViewPhrases = () =>
    navigation.navigate('SavedVocabulary', { type: 'phrases' });

  const handleMenuPress = (itemId: string) => {
    switch (itemId) {
      case 'logout':
        Alert.alert(
          '로그아웃',
          '로그아웃하시겠어요?',
          [
            { text: '취소', style: 'cancel' },
            {
              text: '로그아웃',
              style: 'destructive',
              onPress: async () => {
                await logoutUser();
                navigation.reset({
                  index: 0,
                  routes: [{ name: 'Login' }],
                });
              },
            },
          ],
        );
        break;

      case 'reset':
        Alert.alert(
          '데이터 초기화',
          '어떤 데이터를 삭제하시겠어요?\n\n기기 데이터 — 프로필 사진, 즐겨찾기, 직접 만든 상황, 연습 패턴\n\n서버 기록 — 세션 기록, 실수 기록, 저장한 단어/표현',
          [
            { text: '취소', style: 'cancel' },
            { text: '기기 데이터만',  onPress: () => confirmAndClear('local') },
            { text: '서버 기록만',    onPress: () => confirmAndClear('server') },
            { text: '전체 삭제', style: 'destructive', onPress: () => confirmAndClear('all') },
          ],
        );
        break;
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="프로필" showBack={false} />

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Hero card ── */}
        <Card variant="elevated" style={styles.heroCard}>
          <View style={styles.heroTopRow}>
            <View style={styles.avatarWrap}>
              <Image
                source={{ uri: display.avatarUrl }}
                style={styles.avatar}
              />
              {/* Camera icon opens photo picker; Edit navigates to profile form */}
              <TouchableOpacity
                style={styles.editAvatarBtn}
                onPress={handleChangePhoto}
              >
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
              <Text style={styles.heroStatValue}>
                {stats.completedSessions}
              </Text>
              <Text style={styles.heroStatLabel}>대화 완료</Text>
            </View>
            <View style={styles.heroStatDivider} />
            <View style={styles.heroStatBox}>
              <Text style={styles.heroStatValue}>
                {(stats.learnedWords ?? 0) + (stats.learnedPhrases ?? 0)}
              </Text>
              <Text style={styles.heroStatLabel}>배운 단어/표현</Text>
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
            <TouchableOpacity
              onPress={handleEditProfile}
              style={styles.editBtn}
            >
              <Edit size={14} color="#6C3BFF" />
              <Text style={styles.editLink}>수정</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.infoGrid}>
            <InfoItem label="이름" value={display.name} />
            <InfoItem
              label="나이"
              value={display.age ? `${display.age}세` : '미설정'}
            />
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
            <InfoItem
              label="한국어 수준"
              value={`${display.koreanLevelLabel} (${display.koreanLevelEn})`}
            />
            <InfoItem label="학습 진행도" value={`${stats.progressPercent}%`} />
          </View>
        </Card>

        {/* ── 관심사 ── */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <Heart size={18} color="#E85D8E" />
              <Text style={styles.sectionTitleText}>
                관심사와 피하고 싶은 주제
              </Text>
            </View>
            <TouchableOpacity
              onPress={handleEditInterests}
              style={styles.editBtn}
            >
              <Edit size={14} color="#6C3BFF" />
              <Text style={styles.editLink}>수정</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.groupLabel}>관심사</Text>
          {display.interests.length > 0 ? (
            <View style={styles.tagWrap}>
              {display.interests.map((interest, i) => (
                <Tag key={i} label={interest} selected />
              ))}
            </View>
          ) : (
            <Text style={styles.emptyText}>아직 선택한 관심사가 없어요.</Text>
          )}
          <View style={styles.divider} />
          <Text style={styles.groupLabel}>피하고 싶은 주제</Text>
          {display.dislikes.length > 0 ? (
            <View style={styles.tagWrap}>
              {display.dislikes.map((dislike, i) => (
                <Tag key={i} label={dislike} variant="outline" />
              ))}
            </View>
          ) : (
            <Text style={styles.emptyText}>피하고 싶은 주제가 없어요.</Text>
          )}
        </Card>

        {/* ── AI 참고 메모 ── */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <View style={styles.sectionTitleRow}>
              <MessageSquare size={18} color="#6C3BFF" />
              <Text style={styles.sectionTitleText}>AI 참고 메모</Text>
            </View>
            <TouchableOpacity
              onPress={handleEditProfile}
              style={styles.editBtn}
            >
              <Edit size={14} color="#6C3BFF" />
              <Text style={styles.editLink}>수정</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.memoText}>
            {display.memo || '아직 작성된 메모가 없어요.'}
          </Text>
        </Card>

        {/* ── 학습 기록 ── */}
        <Text style={styles.sectionTitle}>학습 기록</Text>
        <View style={styles.statsRow}>
          <TouchableOpacity
            style={[styles.statCard, styles.statCardClickable]}
            onPress={handleViewWords}
            activeOpacity={0.75}
          >
            <View style={[styles.statIconBg, styles.wordsIconBg]}>
              <BookOpen size={20} color="#6C3BFF" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.learnedWords ?? 0}</Text>
              <Text style={styles.statLabel}>배운 단어</Text>
            </View>
            <ChevronRight size={18} color="#B0B0C5" />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.statCard, styles.statCardClickable]}
            onPress={handleViewPhrases}
            activeOpacity={0.75}
          >
            <View style={[styles.statIconBg, styles.phrasesIconBg]}>
              <MessageCircle size={20} color="#4CAF50" />
            </View>
            <View style={styles.statTextContainer}>
              <Text style={styles.statValue}>{stats.learnedPhrases ?? 0}</Text>
              <Text style={styles.statLabel}>배운 표현</Text>
            </View>
            <ChevronRight size={18} color="#B0B0C5" />
          </TouchableOpacity>
        </View>

        {/* ── 설정 ── */}
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
                <View
                  style={[
                    styles.menuIconBg,
                    item.danger && styles.menuIconDangerBg,
                    item.warning && styles.menuIconWarningBg,
                  ]}
                >
                  <item.icon
                    size={18}
                    color={
                      item.danger ? '#E53935' :
                      item.warning ? '#F57C00' :
                      '#6C6C80'
                    }
                  />
                </View>
                <View style={styles.menuItemLabelWrap}>
                  <Text
                    style={[
                      styles.menuItemLabel,
                      item.danger && styles.menuItemLabelDanger,
                      item.warning && styles.menuItemLabelWarning,
                    ]}
                  >
                    {item.label}
                  </Text>
                  {item.warning ? (
                    <Text style={styles.menuItemSublabel}>
                      기기 저장 데이터만 삭제 · 되돌릴 수 없음
                    </Text>
                  ) : null}
                </View>
              </View>

              {item.value ? (
                <View style={styles.menuItemRight}>
                  <Text style={styles.menuItemValue}>{item.value}</Text>
                </View>
              ) : !item.danger && !item.warning ? (
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
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 40 },

  // Hero
  heroCard: {
    marginTop: 16,
    marginBottom: 18,
    padding: 20,
    borderRadius: 22,
    borderWidth: 1,
    borderColor: '#E8E8F0',
  },
  heroTopRow: { flexDirection: 'row', alignItems: 'center' },
  avatarWrap: { position: 'relative', marginRight: 16 },
  avatar: {
    width: 82,
    height: 82,
    borderRadius: 41,
    backgroundColor: '#ECECF4',
  },
  editAvatarBtn: {
    position: 'absolute',
    right: -2,
    bottom: -2,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#6C3BFF',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  heroCopy: { flex: 1 },
  userName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 4,
  },
  levelChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    backgroundColor: '#F3EEFF',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 999,
  },
  levelChipText: { fontSize: 12, fontWeight: '600', color: '#6C3BFF' },
  heroStatsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 18,
    paddingTop: 18,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F5',
  },
  heroStatBox: { flex: 1, alignItems: 'center' },
  heroStatDivider: { width: 1, height: 34, backgroundColor: '#F0F0F5' },
  heroStatValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 4,
  },
  heroStatLabel: { fontSize: 11, color: '#7A7A92' },

  // Section cards
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 12,
  },
  sectionCard: {
    marginBottom: 16,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#E8E8F0',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  sectionTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sectionTitleText: { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  editBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#F3EEFF',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 10,
  },
  editLink: { fontSize: 12, fontWeight: '600', color: '#6C3BFF' },

  // Info grid
  infoGrid: { flexDirection: 'row', gap: 10 },
  infoItem: {
    flex: 1,
    backgroundColor: '#FAFAFD',
    borderRadius: 16,
    padding: 12,
  },
  infoLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#8E8EA4',
    marginBottom: 6,
  },
  infoValue: {
    fontSize: 14,
    lineHeight: 20,
    color: '#1A1A2E',
    fontWeight: '600',
  },

  // Tags
  groupLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C6C80',
    marginBottom: 10,
  },
  tagWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  divider: { height: 1, backgroundColor: '#F0F0F5', marginVertical: 16 },
  emptyText: { fontSize: 13, lineHeight: 20, color: '#8E8EA4' },
  memoText: { fontSize: 14, lineHeight: 21, color: '#56566F' },

  // Stats
  statsRow: { flexDirection: 'row', gap: 12, marginBottom: 12 },
  statCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  statCardClickable: { borderWidth: 1, borderColor: '#F0F0F5' },
  statIconBg: {
    width: 42,
    height: 42,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  wordsIconBg: { backgroundColor: '#F0EDFF' },
  phrasesIconBg: { backgroundColor: '#E8F5E9' },
  statTextContainer: { flex: 1 },
  statValue: { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },
  statLabel: { fontSize: 11, color: '#6C6C80', marginTop: 2 },

  // Menu
  menuCard: {
    padding: 0,
    overflow: 'hidden',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#E8E8F0',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  menuItemBorder: { borderBottomWidth: 1, borderBottomColor: '#F0F0F5' },
  menuItemLeft: { flexDirection: 'row', alignItems: 'center', gap: 12, flex: 1 },
  menuIconBg: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: '#F5F5FA',
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuIconDangerBg: { backgroundColor: '#FFEBEE' },
  menuIconWarningBg: { backgroundColor: '#FFF3E0' },
  menuItemLabelWrap: { flex: 1 },
  menuItemLabel: { fontSize: 15, color: '#1A1A2E', fontWeight: '500' },
  menuItemLabelDanger: { color: '#E53935' },
  menuItemLabelWarning: { color: '#F57C00' },
  menuItemSublabel: { fontSize: 11, color: '#B0A090', marginTop: 2 },
  menuItemRight: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  menuItemValue: { fontSize: 14, color: '#6C6C80' },

  version: {
    textAlign: 'center',
    fontSize: 12,
    color: '#B0B0C5',
    marginTop: 8,
  },
});

export default MyProfileScreen;
