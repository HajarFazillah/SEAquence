import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, Alert, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Mic, Sparkles, UserRound } from 'lucide-react-native';
import { Header, Card, Button, StatusBadge, Icon } from '../components';
import { createSession, getUserAvatars, AvatarFromDB } from '../services/apiSession';

type RealtimeMode = 'quick' | 'avatar';

const QUICK_START_AVATAR = {
  id: 'quick_start',
  name_ko: '상대방',
  name_en: 'Conversation Partner',
  role: 'unknown',
  description: '상대 정보를 모르는 일반 대화',
  avatar_bg: '#6C3BFF',
  icon: 'user',
  difficulty: 'medium',
};

export default function RealtimeScreen() {
  const navigation = useNavigation<any>();
  const [mode, setMode] = useState<RealtimeMode>('quick');
  const [selectedAvatarId, setSelectedAvatarId] = useState<number | null>(null);
  const [avatars, setAvatars] = useState<AvatarFromDB[]>([]);
  const [isLoadingAvatars, setIsLoadingAvatars] = useState(true);
  const [isStarting, setIsStarting] = useState(false);

  // ─── Fetch real avatars from DB on mount ─────────────────────────────────
  useEffect(() => {
    getUserAvatars()
      .then(setAvatars)
      .catch(() =>
        Alert.alert('오류', '아바타를 불러올 수 없습니다. 다시 시도해주세요.')
      )
      .finally(() => setIsLoadingAvatars(false));
  }, []);

  const handleQuickStart = () => {
    navigation.navigate('RealtimeSession', {
      avatar: QUICK_START_AVATAR,
      sessionId: `quick-realtime-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      situation: '빠른 실시간 대화',
    });
  };

  // ─── Start session ────────────────────────────────────────────────────────
  const handleStartSession = async () => {
    if (selectedAvatarId === null) return;
    const avatar = avatars.find((a) => a.id === selectedAvatarId);
    if (!avatar) return;

    setIsStarting(true);
    try {
      const session = await createSession({
        avatarId: avatar.id.toString(),
        avatarName: avatar.name_ko,
        avatarIcon: avatar.icon,
        avatarBg: avatar.avatar_bg,
        situation: '일상 대화',
        difficulty: avatar.difficulty,
      });
      navigation.navigate('RealtimeSession', {
        avatar,
        sessionId: session.sessionId,
        situation: session.situation,
      });
    } catch {
      Alert.alert(
        '세션 시작 실패',
        '세션을 시작할 수 없습니다. 잠시 후 다시 시도해주세요.',
        [{ text: '확인' }]
      );
    } finally {
      setIsStarting(false);
    }
  };

  const handlePrimaryAction = () => {
    if (mode === 'quick') {
      handleQuickStart();
    } else {
      handleStartSession();
    }
  };

  const primaryDisabled = mode === 'avatar' && (selectedAvatarId === null || isLoadingAvatars);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="실시간 대화" showBack={false} showBell />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Info Banner */}
        <Card variant="elevated" style={styles.infoBanner}>
          <View style={styles.infoRow}>
            <View style={styles.infoIcon}>
              <Mic size={24} color="#6C3BFF" />
            </View>
            <View style={styles.infoText}>
              <Text style={styles.infoTitle}>음성 인식 대화</Text>
              <Text style={styles.infoSubtitle}>
                마이크로 말하면 AI가 실시간으로 대화해요
              </Text>
            </View>
          </View>
        </Card>

        {/* How it works */}
        <Text style={styles.sectionTitle}>이용 방법</Text>
        <View style={styles.stepsContainer}>
          <View style={styles.step}>
            <View style={styles.stepNumber}><Text style={styles.stepNumberText}>1</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>아바타 선택</Text>
              <Text style={styles.stepDesc}>대화할 아바타를 선택하세요</Text>
            </View>
          </View>
          <View style={styles.step}>
            <View style={styles.stepNumber}><Text style={styles.stepNumberText}>2</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>마이크 허용</Text>
              <Text style={styles.stepDesc}>음성 인식을 위해 마이크를 허용하세요</Text>
            </View>
          </View>
          <View style={styles.step}>
            <View style={styles.stepNumber}><Text style={styles.stepNumberText}>3</Text></View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>대화 시작</Text>
              <Text style={styles.stepDesc}>버튼을 누르고 말하세요</Text>
            </View>
          </View>
        </View>

        {/* Realtime Mode */}
        <Text style={styles.sectionTitle}>시작 방식</Text>
        <View style={styles.modeList}>
          <TouchableModeCard
            active={mode === 'quick'}
            title="빠른 시작"
            subtitle="상대 정보 없이 바로 말투와 공손도를 분석해요"
            icon={<Sparkles size={22} color={mode === 'quick' ? '#FFFFFF' : '#6C3BFF'} />}
            onPress={() => setMode('quick')}
          />
          <TouchableModeCard
            active={mode === 'avatar'}
            title="아바타와 연습"
            subtitle="선택한 아바타의 관계와 말투 기준으로 분석해요"
            icon={<UserRound size={22} color={mode === 'avatar' ? '#FFFFFF' : '#6C3BFF'} />}
            onPress={() => setMode('avatar')}
          />
        </View>

        {/* Avatar Selection */}
        {mode === 'avatar' && (
          <>
            <Text style={styles.sectionTitle}>아바타 선택</Text>

            {isLoadingAvatars ? (
              <View style={styles.avatarLoading}>
                <ActivityIndicator size="small" color="#6C3BFF" />
                <Text style={styles.avatarLoadingText}>아바타 불러오는 중...</Text>
              </View>
            ) : avatars.length === 0 ? (
              <View style={styles.emptyAvatars}>
                <Text style={styles.emptyAvatarsText}>
                  아직 아바타가 없습니다. 아바타 탭에서 먼저 만들어보세요!
                </Text>
              </View>
            ) : (
              <View style={styles.avatarList}>
                {avatars.map((avatar) => (
                  <Card
                    key={avatar.id}
                    variant={selectedAvatarId === avatar.id ? 'outlined' : 'elevated'}
                    style={[
                      styles.avatarCard,
                      selectedAvatarId === avatar.id && styles.avatarCardSelected,
                    ]}
                    onPress={() => setSelectedAvatarId(avatar.id)}
                  >
                    <View style={styles.avatarRow}>
                      <View style={[styles.avatarIcon, styles.avatarIconFallback]}>
                        <Icon name={avatar.icon as any} size={24} color="#FFFFFF" />
                      </View>
                      <View style={styles.avatarInfo}>
                        <Text style={styles.avatarName}>{avatar.name_ko}</Text>
                        <Text style={styles.avatarRole}>{avatar.description}</Text>
                      </View>
                      <StatusBadge status={avatar.difficulty as 'easy' | 'medium' | 'hard'} />
                    </View>
                  </Card>
                ))}
              </View>
            )}
          </>
        )}

      </ScrollView>

      {/* Start Button */}
      <View style={styles.footer}>
        {isStarting ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#6C3BFF" />
            <Text style={styles.loadingText}>세션 준비 중...</Text>
          </View>
        ) : (
          <Button
            title={mode === 'quick' ? '빠른 시작하기' : '세션 시작하기'}
            onPress={handlePrimaryAction}
            showArrow
            disabled={primaryDisabled}
          />
        )}
      </View>
    </SafeAreaView>
  );
}

function TouchableModeCard({
  active,
  title,
  subtitle,
  icon,
  onPress,
}: {
  active: boolean;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  onPress: () => void;
}) {
  return (
    <Card
      variant={active ? 'outlined' : 'elevated'}
      style={[styles.modeCard, active && styles.modeCardActive]}
      onPress={onPress}
    >
      <View style={[styles.modeIcon, active && styles.modeIconActive]}>
        {icon}
      </View>
      <View style={styles.modeInfo}>
        <Text style={styles.modeTitle}>{title}</Text>
        <Text style={styles.modeSubtitle}>{subtitle}</Text>
      </View>
    </Card>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  // Info Banner
  infoBanner: { backgroundColor: '#F0EDFF', marginBottom: 24 },
  infoRow: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  infoIcon: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center',
  },
  infoText: { flex: 1 },
  infoTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 2 },
  infoSubtitle: { fontSize: 13, color: '#6C6C80' },

  // Section
  sectionTitle: { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginBottom: 14 },

  // Steps
  stepsContainer: { marginBottom: 24 },
  step: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 16 },
  stepNumber: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center', marginRight: 12,
  },
  stepNumberText: { fontSize: 14, fontWeight: '700', color: '#FFFFFF' },
  stepContent: { flex: 1 },
  stepTitle: { fontSize: 15, fontWeight: '600', color: '#1A1A2E', marginBottom: 2 },
  stepDesc: { fontSize: 13, color: '#6C6C80' },

  // Mode selection
  modeList: { gap: 12, marginBottom: 24 },
  modeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    borderColor: '#E2E2EC',
  },
  modeCardActive: {
    borderColor: '#6C3BFF',
    borderWidth: 2,
  },
  modeIcon: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#F0EDFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  modeIconActive: {
    backgroundColor: '#6C3BFF',
  },
  modeInfo: { flex: 1 },
  modeTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 3,
  },
  modeSubtitle: {
    fontSize: 12,
    color: '#6C6C80',
    lineHeight: 17,
  },

  // Avatar List
  avatarList: { gap: 12 },
  avatarCard: {},
  avatarCardSelected: { borderColor: '#6C3BFF', borderWidth: 2 },
  avatarRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatarIcon: {
    width: 48, height: 48, borderRadius: 24,
    alignItems: 'center', justifyContent: 'center',
  },
  avatarIconFallback: { backgroundColor: '#6C3BFF' },
  avatarInfo: { flex: 1 },
  avatarName: { fontSize: 16, fontWeight: '600', color: '#1A1A2E', marginBottom: 2 },
  avatarRole: { fontSize: 12, color: '#6C6C80' },

  // Avatar loading / empty
  avatarLoading: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 10, paddingVertical: 32,
  },
  avatarLoadingText: { fontSize: 14, color: '#6C6C80' },
  emptyAvatars: {
    backgroundColor: '#F0EDFF', borderRadius: 12,
    padding: 20, alignItems: 'center',
  },
  emptyAvatarsText: {
    fontSize: 14, color: '#6C3BFF', textAlign: 'center', lineHeight: 22,
  },

  // Footer
  footer: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    padding: 20, backgroundColor: '#F7F7FB',
  },
  loadingContainer: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', gap: 10, height: 52,
  },
  loadingText: { fontSize: 15, color: '#6C3BFF', fontWeight: '600' },
});
