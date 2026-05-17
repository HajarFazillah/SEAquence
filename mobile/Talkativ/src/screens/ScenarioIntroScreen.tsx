import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  ScrollView, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  ArrowLeft, MapPin, Target, RefreshCw, Sparkles, User,
} from 'lucide-react-native';
import { Icon, Card, StatusBadge, type IconName } from '../components';
import { AI_SERVER_URL } from '../constants';

const C = {
  canvas:  '#F2F1F7',
  paper:   '#F8F7FC',
  white:   '#FFFFFF',
  ink100:  '#111118',
  ink70:   '#4A4858',
  ink40:   '#9694A8',
  ink10:   '#E4E2EF',
  terra:   '#5B35E8',
  terraFg: '#EDEAFC',
};

type Situation = {
  id: string;
  name_ko: string;
  description_ko: string;
  scene_place: string;
  conversation_goal: string;
  user_role_in_scene: string;
  avatar_role_in_scene: string;
};

const FALLBACK: Situation = {
  id: 'fallback',
  name_ko: '자유 대화',
  description_ko: '아바타와 자유롭게 대화해 보세요.',
  scene_place: '일상적인 공간',
  conversation_goal: '자연스러운 대화 연습',
  user_role_in_scene: '학습자',
  avatar_role_in_scene: '대화 상대',
};

export default function ScenarioIntroScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { avatar } = route.params;

  const [situation, setSituation] = useState<Situation | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchScenario = useCallback(async () => {
    setLoading(true);
    setSituation(null);
    try {
      const res = await fetch(`${AI_SERVER_URL}/api/v1/chat/suggest-situations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ avatar, user_profile: {}, count: 3 }),
      });
      if (res.ok) {
        const data = await res.json();
        const list: Situation[] = Array.isArray(data?.situations) ? data.situations : [];
        if (list.length) {
          setSituation(list[Math.floor(Math.random() * list.length)]);
          return;
        }
      }
      setSituation(FALLBACK);
    } catch {
      setSituation(FALLBACK);
    } finally {
      setLoading(false);
    }
  }, [avatar]);

  useEffect(() => { fetchScenario(); }, [fetchScenario]);

  const handleStart = () => {
    if (!situation) return;
    navigation.navigate('RealtimeSession', { avatar, situation });
  };

  const canStart = !loading && !!situation;

  return (
    <SafeAreaView style={s.safe} edges={['top']}>
      {/* ── Header ── */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn} hitSlop={8}>
          <ArrowLeft size={22} color={C.ink100} />
        </TouchableOpacity>
        <Text style={s.headerTitle}>아바타와 연습</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView
        style={s.scroll}
        contentContainerStyle={s.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Avatar card (same as avatar selection) ── */}
        <Card variant="elevated">
          <View style={s.avatarRow}>
            <View style={[s.avatarIcon, { backgroundColor: avatar?.avatar_bg ?? '#6C3BFF' }]}>
              <Icon name={(avatar?.icon ?? 'user') as IconName} size={24} color="#FFF" />
            </View>
            <View style={s.avatarInfo}>
              <Text style={s.avatarName}>{avatar?.name_ko ?? '아바타'}</Text>
              {avatar?.description ? (
                <Text style={s.avatarRole}>{avatar.description}</Text>
              ) : null}
            </View>
            {avatar?.difficulty ? (
              <StatusBadge status={avatar.difficulty as 'easy' | 'medium' | 'hard'} />
            ) : null}
          </View>
        </Card>

        {/* ── Section label ── */}
        <View style={s.sectionLabel}>
          <Sparkles size={13} color={C.terra} strokeWidth={2} />
          <Text style={s.sectionLabelText}>오늘의 시나리오</Text>
        </View>

        {loading || !situation ? (
          <View style={s.loadingCard}>
            <ActivityIndicator color={C.terra} size="small" />
            <Text style={s.loadingText}>시나리오 생성 중...</Text>
          </View>
        ) : (
          <>
            {/* ── Scenario card ── */}
            <View style={s.scenarioCard}>
              <View style={s.placeRow}>
                <MapPin size={12} color={C.ink40} strokeWidth={2} />
                <Text style={s.placeText}>{situation.scene_place}</Text>
              </View>
              <Text style={s.scenarioTitle}>{situation.name_ko}</Text>
              <Text style={s.scenarioDesc}>{situation.description_ko}</Text>
            </View>

            {/* ── Info rows ── */}
            <View style={s.infoCard}>
              <View style={s.infoRow}>
                <View style={s.infoIconWrap}>
                  <User size={14} color={C.terra} strokeWidth={2} />
                </View>
                <View style={s.infoTexts}>
                  <Text style={s.infoLabel}>내 역할</Text>
                  <Text style={s.infoValue}>{situation.user_role_in_scene}</Text>
                </View>
              </View>
              <View style={s.infoDivider} />
              <View style={s.infoRow}>
                <View style={s.infoIconWrap}>
                  <Target size={14} color={C.terra} strokeWidth={2} />
                </View>
                <View style={s.infoTexts}>
                  <Text style={s.infoLabel}>연습 목표</Text>
                  <Text style={s.infoValue}>{situation.conversation_goal}</Text>
                </View>
              </View>
            </View>

            {/* ── Re-roll ── */}
            <TouchableOpacity style={s.reshuffleBtn} onPress={fetchScenario} activeOpacity={0.7}>
              <RefreshCw size={13} color={C.ink70} strokeWidth={2} />
              <Text style={s.reshuffleText}>다른 시나리오 보기</Text>
            </TouchableOpacity>
          </>
        )}
      </ScrollView>

      {/* ── Start button ── */}
      <View style={s.footer}>
        <TouchableOpacity
          style={[s.startBtn, !canStart && s.startBtnDisabled]}
          onPress={handleStart}
          disabled={!canStart}
          activeOpacity={0.85}
        >
          <Text style={s.startBtnText}>연습 시작하기</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.canvas },

  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
  },
  backBtn: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 16, fontWeight: '700', color: C.ink100 },

  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 16, paddingBottom: 24, gap: 12 },

  avatarRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatarIcon: {
    width: 48, height: 48, borderRadius: 24,
    alignItems: 'center', justifyContent: 'center',
  },
  avatarInfo: { flex: 1 },
  avatarName: { fontSize: 16, fontWeight: '600', color: '#1A1A2E', marginBottom: 2 },
  avatarRole: { fontSize: 12, color: '#6C6C80' },

  sectionLabel: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    marginTop: 4,
  },
  sectionLabelText: { fontSize: 12, fontWeight: '700', color: C.terra, letterSpacing: 0.5, textTransform: 'uppercase' },

  loadingCard: {
    backgroundColor: C.white, borderRadius: 18,
    paddingVertical: 40, alignItems: 'center', gap: 12,
  },
  loadingText: { fontSize: 13, color: C.ink40 },

  scenarioCard: {
    backgroundColor: C.white, borderRadius: 18,
    paddingHorizontal: 18, paddingVertical: 20, gap: 10,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06, shadowRadius: 8, elevation: 2,
    borderLeftWidth: 4, borderLeftColor: C.terra,
  },
  placeRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  placeText: { fontSize: 12, color: C.ink40 },
  scenarioTitle: { fontSize: 19, fontWeight: '800', color: C.ink100, lineHeight: 26 },
  scenarioDesc: { fontSize: 14, color: C.ink70, lineHeight: 22 },

  infoCard: {
    backgroundColor: C.white, borderRadius: 18,
    paddingHorizontal: 18, paddingVertical: 4,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06, shadowRadius: 8, elevation: 2,
  },
  infoRow: { flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 14 },
  infoIconWrap: {
    width: 32, height: 32, borderRadius: 10,
    backgroundColor: C.terraFg, alignItems: 'center', justifyContent: 'center',
  },
  infoTexts: { flex: 1 },
  infoLabel: { fontSize: 11, color: C.ink40, fontWeight: '600', letterSpacing: 0.3 },
  infoValue: { fontSize: 14, color: C.ink100, fontWeight: '600', marginTop: 2 },
  infoDivider: { height: 1, backgroundColor: C.ink10, marginHorizontal: 0 },

  reshuffleBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 7, paddingVertical: 12,
  },
  reshuffleText: { fontSize: 13, color: C.ink70, fontWeight: '600' },

  footer: { paddingHorizontal: 16, paddingBottom: 24, paddingTop: 12 },
  startBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    backgroundColor: C.terra, borderRadius: 18,
    paddingVertical: 18, gap: 10,
  },
  startBtnDisabled: { opacity: 0.5 },
  startBtnText: { fontSize: 16, fontWeight: '700', color: '#FFF', textAlign: 'center' },
});
