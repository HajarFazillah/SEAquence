import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, Alert, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Mic, Sparkles, UserRound, ChevronDown, ChevronUp, HelpCircle, GitCompare } from 'lucide-react-native';
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

  const [showHowTo, setShowHowTo] = useState(false);
  const [showDiff, setShowDiff] = useState(false);

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
  const handleStartSession = () => {
    if (selectedAvatarId === null) return;
    const avatar = avatars.find((a) => a.id === selectedAvatarId);
    if (!avatar) return;
    navigation.navigate('ScenarioIntro', { avatar });
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
      <Header title="실시간 대화" showBack={false} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Info Banner */}
        <Card variant="elevated" style={styles.infoBanner}>
          <View style={styles.infoRow}>
            <View style={styles.infoIcon}>
              <Mic size={24} color="#6C3BFF" />
            </View>
            <View style={styles.infoText}>
              <Text style={styles.infoTitle}>실시간 음성 분석</Text>
              <Text style={styles.infoSubtitle}>
                대화를 녹음하면 말투·공손도를 자동으로 분석하고 피드백을 드려요
              </Text>
            </View>
          </View>
        </Card>

        {/* Info Cards */}
        <View style={styles.infoCards}>
          <Card variant="elevated" style={styles.infoCardCollapsible} onPress={() => setShowHowTo(v => !v)}>
            <View style={styles.infoCardHeader}>
              <View style={styles.infoCardIconWrap}>
                <HelpCircle size={15} color="#6C3BFF" />
              </View>
              <Text style={styles.infoCardTitle}>어떻게 사용하나요?</Text>
              {showHowTo
                ? <ChevronUp size={16} color="#6C3BFF" />
                : <ChevronDown size={16} color="#9694A8" />}
            </View>
            {showHowTo && (
              <View style={styles.infoCardBody}>
                {[
                  '마이크 버튼을 눌러 녹음을 시작해요',
                  '대화가 끝나면 다시 눌러 분석을 받아요',
                  '말투·공손도 피드백과 개선 제안을 확인해요',
                ].map((step, i) => (
                  <View key={i} style={styles.infoStep}>
                    <View style={styles.infoStepDot}>
                      <Text style={styles.infoStepNum}>{i + 1}</Text>
                    </View>
                    <Text style={styles.infoStepText}>{step}</Text>
                  </View>
                ))}
              </View>
            )}
          </Card>

          <Card variant="elevated" style={styles.infoCardCollapsible} onPress={() => setShowDiff(v => !v)}>
            <View style={styles.infoCardHeader}>
              <View style={styles.infoCardIconWrap}>
                <GitCompare size={15} color="#6C3BFF" />
              </View>
              <Text style={styles.infoCardTitle}>두 모드의 차이는?</Text>
              {showDiff
                ? <ChevronUp size={16} color="#6C3BFF" />
                : <ChevronDown size={16} color="#9694A8" />}
            </View>
            {showDiff && (
              <View style={styles.infoCardBody}>
                <View style={styles.diffRow}>
                  <View style={styles.diffCol}>
                    <Text style={styles.diffLabel}>빠른 시작</Text>
                    <Text style={styles.diffText}>실제 두 사람이 대화할 때 사용해요. 화자를 자동으로 구분해요.</Text>
                  </View>
                  <View style={styles.diffDivider} />
                  <View style={styles.diffCol}>
                    <Text style={styles.diffLabel}>아바타와 연습</Text>
                    <Text style={styles.diffText}>혼자 연습할 때 사용해요. 아바타 관계에 맞는 말투를 분석해요.</Text>
                  </View>
                </View>
              </View>
            )}
          </Card>
        </View>

        {/* Mode Selection */}
        <Text style={styles.sectionTitle}>시작 방식 선택</Text>
        <View style={styles.modeList}>
          <TouchableModeCard
            active={mode === 'quick'}
            title="빠른 시작"
            tag="2인 대화"
            subtitle="실제 두 사람의 대화를 녹음해요. 화자를 자동으로 구분해 각각 분석해요."
            icon={<Sparkles size={22} color={mode === 'quick' ? '#FFFFFF' : '#6C3BFF'} />}
            onPress={() => setMode('quick')}
          />
          <TouchableModeCard
            active={mode === 'avatar'}
            title="아바타와 연습"
            tag="혼자 연습"
            subtitle="선배·교수님 등 아바타 관계를 설정하고 그에 맞는 말투로 혼자 연습해요."
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
        <Button
          title={mode === 'quick' ? '빠른 시작하기' : '세션 시작하기'}
          onPress={handlePrimaryAction}
          showArrow
          disabled={primaryDisabled}
        />
      </View>
    </SafeAreaView>
  );
}

function TouchableModeCard({
  active,
  title,
  tag,
  subtitle,
  icon,
  onPress,
}: {
  active: boolean;
  title: string;
  tag: string;
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
        <View style={styles.modeTitleRow}>
          <Text style={styles.modeTitle}>{title}</Text>
          <View style={[styles.modeTag, active && styles.modeTagActive]}>
            <Text style={[styles.modeTagText, active && styles.modeTagTextActive]}>{tag}</Text>
          </View>
        </View>
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

  // Info cards
  infoCards: { gap: 10, marginBottom: 24 },
  infoCardCollapsible: { paddingVertical: 12 },
  infoCardHeader: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  infoCardIconWrap: {
    width: 26, height: 26, borderRadius: 8,
    backgroundColor: '#F0EDFF', alignItems: 'center', justifyContent: 'center',
  },
  infoCardTitle: { flex: 1, fontSize: 14, fontWeight: '600', color: '#1A1A2E' },
  infoCardBody: { marginTop: 14, gap: 10 },
  infoStep: { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  infoStepDot: {
    width: 20, height: 20, borderRadius: 10,
    backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center',
    marginTop: 1,
  },
  infoStepNum: { fontSize: 11, fontWeight: '700', color: '#FFFFFF' },
  infoStepText: { flex: 1, fontSize: 13, color: '#4A4858', lineHeight: 19 },
  diffRow: { flexDirection: 'row', gap: 12 },
  diffCol: { flex: 1, gap: 4 },
  diffDivider: { width: 1, backgroundColor: '#E4E2EF' },
  diffLabel: { fontSize: 12, fontWeight: '700', color: '#6C3BFF' },
  diffText: { fontSize: 12, color: '#4A4858', lineHeight: 18 },

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
  modeTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 3 },
  modeTitle: { fontSize: 15, fontWeight: '700', color: '#1A1A2E' },
  modeTag: {
    paddingHorizontal: 8, paddingVertical: 2, borderRadius: 99,
    backgroundColor: '#F0EDFF',
  },
  modeTagActive: { backgroundColor: 'rgba(255,255,255,0.25)' },
  modeTagText: { fontSize: 11, fontWeight: '600', color: '#6C3BFF' },
  modeTagTextActive: { color: '#FFFFFF' },
  modeSubtitle: { fontSize: 12, color: '#6C6C80', lineHeight: 17 },

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
