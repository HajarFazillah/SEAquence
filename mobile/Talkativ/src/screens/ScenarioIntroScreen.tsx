import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  ScrollView, ActivityIndicator, TextInput, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  ArrowLeft, MapPin, Target, RefreshCw, Sparkles, User,
  Pencil, ChevronDown, ChevronUp, Check,
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
  const [showCustom, setShowCustom] = useState(false);
  const [customTitle, setCustomTitle] = useState('');
  const [customDesc, setCustomDesc] = useState('');
  const [isCustomised, setIsCustomised] = useState(false);

  const fetchScenario = useCallback(async () => {
    setLoading(true);
    setSituation(null);
    setShowCustom(false);
    setIsCustomised(false);
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
          const picked = list[Math.floor(Math.random() * list.length)];
          setSituation(picked);
          setCustomTitle(picked.name_ko);
          setCustomDesc(picked.description_ko);
          return;
        }
      }
      setSituation(FALLBACK);
      setCustomTitle(FALLBACK.name_ko);
      setCustomDesc(FALLBACK.description_ko);
    } catch {
      setSituation(FALLBACK);
      setCustomTitle(FALLBACK.name_ko);
      setCustomDesc(FALLBACK.description_ko);
    } finally {
      setLoading(false);
    }
  }, [avatar]);

  useEffect(() => { fetchScenario(); }, [fetchScenario]);

  const applyCustomDesc = () => {
    if (!situation || !customTitle.trim() || !customDesc.trim()) return;
    setSituation({ ...situation, name_ko: customTitle.trim(), description_ko: customDesc.trim() });
    setIsCustomised(true);
    setShowCustom(false);
  };

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

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          style={s.scroll}
          contentContainerStyle={s.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* ── Avatar card ── */}
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
            {isCustomised ? (
              <View style={s.customBadge}>
                <Pencil size={10} color={C.terra} strokeWidth={2} />
                <Text style={s.customBadgeText}>수정됨</Text>
              </View>
            ) : null}
          </View>

          {loading || !situation ? (
            <View style={s.loadingCard}>
              <ActivityIndicator color={C.terra} size="small" />
              <Text style={s.loadingText}>시나리오 생성 중...</Text>
            </View>
          ) : (
            <>
              {/* ── Scenario card ── */}
              <View style={[s.scenarioCard, isCustomised && s.scenarioCardCustom]}>
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

              {/* ── Action row: re-roll + customise toggle ── */}
              <View style={s.actionRow}>
                <TouchableOpacity style={s.actionBtn} onPress={fetchScenario} activeOpacity={0.7}>
                  <RefreshCw size={13} color={C.ink70} strokeWidth={2} />
                  <Text style={s.actionBtnText}>다른 시나리오</Text>
                </TouchableOpacity>
                <View style={s.actionDivider} />
                <TouchableOpacity
                  style={s.actionBtn}
                  onPress={() => setShowCustom(v => !v)}
                  activeOpacity={0.7}
                >
                  <Pencil size={13} color={showCustom ? C.terra : C.ink70} strokeWidth={2} />
                  <Text style={[s.actionBtnText, showCustom && { color: C.terra }]}>
                    직접 수정
                  </Text>
                  {showCustom
                    ? <ChevronUp size={13} color={C.terra} strokeWidth={2} />
                    : <ChevronDown size={13} color={C.ink70} strokeWidth={2} />}
                </TouchableOpacity>
              </View>

              {/* ── Custom input (expandable) ── */}
              {showCustom ? (
                <View style={s.customCard}>
                  <Text style={s.customLabel}>시나리오 수정</Text>
                  <Text style={s.customFieldLabel}>제목</Text>
                  <TextInput
                    style={[s.customInput, s.customInputSingle]}
                    value={customTitle}
                    onChangeText={setCustomTitle}
                    placeholder="시나리오 제목을 입력하세요..."
                    placeholderTextColor={C.ink40}
                  />
                  <Text style={s.customFieldLabel}>내용</Text>
                  <TextInput
                    style={s.customInput}
                    value={customDesc}
                    onChangeText={setCustomDesc}
                    multiline
                    numberOfLines={4}
                    placeholder="시나리오 내용을 직접 입력하세요..."
                    placeholderTextColor={C.ink40}
                    textAlignVertical="top"
                  />
                  <TouchableOpacity
                    style={[s.applyBtn, (!customTitle.trim() || !customDesc.trim()) && s.applyBtnDisabled]}
                    onPress={applyCustomDesc}
                    disabled={!customTitle.trim() || !customDesc.trim()}
                    activeOpacity={0.85}
                  >
                    <Check size={15} color="#FFF" strokeWidth={2.5} />
                    <Text style={s.applyBtnText}>적용하기</Text>
                  </TouchableOpacity>
                </View>
              ) : null}
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>

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

  // Avatar card
  avatarRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatarIcon: {
    width: 48, height: 48, borderRadius: 24,
    alignItems: 'center', justifyContent: 'center',
  },
  avatarInfo: { flex: 1 },
  avatarName: { fontSize: 16, fontWeight: '600', color: '#1A1A2E', marginBottom: 2 },
  avatarRole: { fontSize: 12, color: '#6C6C80' },

  // Section label
  sectionLabel: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    marginTop: 4,
  },
  sectionLabelText: { fontSize: 12, fontWeight: '700', color: C.terra, letterSpacing: 0.5, textTransform: 'uppercase' },
  customBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 3,
    backgroundColor: C.terraFg, paddingHorizontal: 7, paddingVertical: 3,
    borderRadius: 99,
  },
  customBadgeText: { fontSize: 10, fontWeight: '700', color: C.terra },

  // Loading
  loadingCard: {
    backgroundColor: C.white, borderRadius: 18,
    paddingVertical: 40, alignItems: 'center', gap: 12,
  },
  loadingText: { fontSize: 13, color: C.ink40 },

  // Scenario card
  scenarioCard: {
    backgroundColor: C.white, borderRadius: 18,
    paddingHorizontal: 18, paddingVertical: 20, gap: 10,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06, shadowRadius: 8, elevation: 2,
    borderLeftWidth: 4, borderLeftColor: C.terra,
  },
  scenarioCardCustom: { borderLeftColor: '#7C3AED' },
  placeRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  placeText: { fontSize: 12, color: C.ink40 },
  scenarioTitle: { fontSize: 19, fontWeight: '800', color: C.ink100, lineHeight: 26 },
  scenarioDesc: { fontSize: 14, color: C.ink70, lineHeight: 22 },

  // Info card
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
  infoDivider: { height: 1, backgroundColor: C.ink10 },

  // Action row
  actionRow: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: C.white, borderRadius: 14,
    paddingVertical: 4,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04, shadowRadius: 4, elevation: 1,
  },
  actionBtn: {
    flex: 1, flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', gap: 6, paddingVertical: 12,
  },
  actionBtnText: { fontSize: 13, color: C.ink70, fontWeight: '600' },
  actionDivider: { width: 1, height: 20, backgroundColor: C.ink10 },

  // Custom input
  customCard: {
    backgroundColor: C.white, borderRadius: 18,
    padding: 16, gap: 12,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06, shadowRadius: 8, elevation: 2,
  },
  customLabel: { fontSize: 13, fontWeight: '700', color: C.ink100 },
  customFieldLabel: { fontSize: 11, fontWeight: '600', color: C.ink40, letterSpacing: 0.3 },
  customInputSingle: { minHeight: 0 },
  customInput: {
    borderWidth: 1, borderColor: C.ink10,
    borderRadius: 12, padding: 12,
    fontSize: 14, color: C.ink100, lineHeight: 22,
    minHeight: 100, backgroundColor: C.paper,
  },
  applyBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 7, backgroundColor: C.terra,
    borderRadius: 12, paddingVertical: 13,
  },
  applyBtnDisabled: { opacity: 0.4 },
  applyBtnText: { fontSize: 14, fontWeight: '700', color: '#FFF' },

  // Footer
  footer: { paddingHorizontal: 16, paddingBottom: 24, paddingTop: 12 },
  startBtn: {
    alignItems: 'center', justifyContent: 'center',
    backgroundColor: C.terra, borderRadius: 18, paddingVertical: 18,
  },
  startBtnDisabled: { opacity: 0.5 },
  startBtnText: { fontSize: 16, fontWeight: '700', color: '#FFF' },
});
