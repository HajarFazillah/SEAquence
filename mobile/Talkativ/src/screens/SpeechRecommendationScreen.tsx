import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, ActivityIndicator, TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { MapPin, ChevronLeft, X } from 'lucide-react-native';
import { Icon } from '../components';
import { apiService } from '../services/api';
import { createSession } from '../services/apiSession';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ExampleExpression {
  greetings: string[];
  questions: string[];
  responses: string[];
}

interface AvoidExpression {
  wrong:  string;
  reason: string;
}

interface Recommendation {
  recommended_level: 'formal' | 'polite' | 'informal';
  recommended_level_info: {
    name_ko:     string;
    description: string;
    endings:     string[];
  };
  reason_ko:           string;
  example_expressions: ExampleExpression;
  avoid_expressions:   AvoidExpression[];
  tips:                string[];
}

// ─── Fallback data ────────────────────────────────────────────────────────────

const LEVEL_INFO = {
  formal: {
    name:     '합쇼체',
    endings:  '-습니다, -습니까',
    examples: ['안녕하십니까', '감사합니다', '좋습니다', '말씀해 주십시오'],
    avoid:    ['야, 뭐해?', '알겠어', '그래'],
    tips: [
      '어미 -습니다, -습니까를 사용하세요.',
      '격식 있는 어휘를 선택하세요: 나→저, 밥→식사, 이름→성함',
      '존칭을 항상 사용하세요: 선생님, 교수님',
    ],
  },
  polite: {
    name:     '해요체',
    endings:  '-어요, -아요',
    examples: ['안녕하세요', '감사해요', '좋아요', '어디 가세요?'],
    avoid:    ['야, 뭐해?', '알겠어', '그래'],
    tips: [
      '어미 -어요, -아요를 사용하세요.',
      '격식 어휘를 사용하세요: 나→저, 밥→식사',
      '자연스럽고 부드럽게 말하세요.',
    ],
  },
  informal: {
    name:     '반말',
    endings:  '-어, -아, -야',
    examples: ['안녕', '고마워', '좋아', '어디 가?'],
    avoid:    ['안녕하세요', '감사합니다', '~습니다'],
    tips: [
      '어미 -어, -아, -야를 사용하세요.',
      '친근하게 자연스럽게 말하세요.',
      '너무 격식 있는 표현은 어색할 수 있어요.',
    ],
  },
};

const buildFallback = (avatar: any, situation: any): Recommendation => {
  const storedLevel = avatar?.formality_from_user || avatar?.recommendedLevel;
  const level: 'formal' | 'polite' | 'informal' =
    storedLevel && LEVEL_INFO[storedLevel as keyof typeof LEVEL_INFO]
      ? storedLevel
      : ['professor', 'boss', 'ceo', 'client', 'doctor'].includes(avatar?.role)
      ? 'formal'
      : ['friend', 'close_friend', 'classmate', 'roommate', 'younger_sibling'].includes(avatar?.role)
      ? 'informal'
      : 'polite';

  const info = LEVEL_INFO[level];
  return {
    recommended_level: level,
    recommended_level_info: {
      name_ko:     info.name,
      description: `${info.name}를 사용하세요.`,
      endings:     info.endings.split(', '),
    },
    reason_ko: `${avatar?.name_ko || '상대방'}${situation?.name_ko ? `와 ${situation.name_ko} 상황에서` : '와의 대화에서'} 적절한 말투입니다.`,
    example_expressions: {
      greetings: info.examples.slice(0, 2),
      questions: [`${info.examples[0]}?`],
      responses: info.examples.slice(0, 2),
    },
    avoid_expressions: info.avoid.slice(0, 3).map(w => ({
      wrong:  w,
      reason: `${info.name} 대화에서는 어색한 표현입니다.`,
    })),
    tips: info.tips,
  };
};

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function SpeechRecommendationScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();
  const { avatar, situation } = route.params || {};

  const [loading,        setLoading]        = useState(true);
  const [isStarting,     setIsStarting]     = useState(false);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);

  const rec = recommendation || buildFallback(avatar, situation);

  const loadRecommendation = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getSpeechRecommendation(avatar || {}, situation);
      setRecommendation(data);
    } catch (error) {
      console.error('Failed to load recommendation:', error);
      setRecommendation(buildFallback(avatar, situation));
    } finally {
      setLoading(false);
    }
  }, [avatar, situation]);

  useEffect(() => { loadRecommendation(); }, [loadRecommendation]);

  const handleStartChat = async () => {
    if (isStarting) return;
    setIsStarting(true);

    try {
      const session = await createSession({
        avatarId: String(avatar?.id || avatar?.avatarId || avatar?.name_ko || 'unknown-avatar'),
        avatarName: avatar?.name_ko || '아바타',
        avatarIcon: avatar?.icon || 'user',
        avatarBg: avatar?.avatarBg || avatar?.avatar_bg || '#6C3BFF',
        situation: situation?.name_ko || situation?.title || '일상 대화',
        difficulty: avatar?.difficulty || 'medium',
      });

      navigation.navigate('Chat', {
        avatar,
        situation,
        recommendedLevel: rec.recommended_level,
        sessionId: session.sessionId,
      });
    } catch (error) {
      console.error('Failed to create chat session:', error);
      navigation.navigate('Chat', {
        avatar,
        situation,
        recommendedLevel: rec.recommended_level,
      });
    } finally {
      setIsStarting(false);
    }
  };

  // ── Loading ────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
            <ChevronLeft size={18} color="#111" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>추천 말투</Text>
          <View style={styles.headerBtn} />
        </View>
        <View style={styles.loadingWrap}>
          <ActivityIndicator size="large" color={BRAND} />
          <Text style={styles.loadingText}>분석 중...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <ChevronLeft size={18} color="#111" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>추천 말투</Text>
        <View style={styles.headerBtn} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* ── Context card ── */}
        <View style={styles.ctxCard}>
          <View style={[styles.ctxAvatar, { backgroundColor: avatar?.avatarBg || avatar?.avatar_bg || '#C4B5FD' }]}>
            <Icon name={avatar?.icon || 'user'} size={28} color="#fff" />
          </View>
          <View style={styles.ctxInfo}>
            <Text style={styles.ctxLabel}>대화 상대</Text>
            <Text style={styles.ctxName}>{avatar?.name_ko || '상대방'}</Text>
            <View style={styles.ctxSitRow}>
              <MapPin size={12} color="#bbb" />
              <Text style={styles.ctxSit}>{situation?.name_ko || '일상 대화'}</Text>
            </View>
          </View>
        </View>

        {/* ── Recommended level hero ── */}
        <View style={styles.recCard}>
          <View style={styles.recBlob} />
          <Text style={styles.recEye}>추천 말투</Text>
          <View style={styles.recBadge}>
            <Text style={styles.recBadgeText}>{rec.recommended_level_info.name_ko}</Text>
          </View>
          <Text style={styles.recReason}>{rec.reason_ko}</Text>
        </View>

        {/* ── 이렇게 말해보세요 ── */}
        <Text style={styles.sectionLabel}>이렇게 말해보세요</Text>
        <View style={styles.exCard}>
          {[
            { label: '인사', items: rec.example_expressions.greetings.slice(0, 3) },
            { label: '질문', items: rec.example_expressions.questions.slice(0, 3) },
            { label: '대답', items: rec.example_expressions.responses.slice(0, 3) },
          ].map((sec, si) => (
            <View key={si} style={[styles.exSection, si > 0 && styles.exSectionBorder]}>
              <Text style={styles.exSectionLabel}>{sec.label}</Text>
              <View style={styles.exChips}>
                {sec.items.map((exp, i) => (
                  <View key={i} style={styles.exChip}>
                    <Text style={styles.exChipText}>{exp}</Text>
                  </View>
                ))}
              </View>
            </View>
          ))}
        </View>

        {/* ── 피해야 할 표현 ── */}
        <Text style={styles.sectionLabel}>피해야 할 표현</Text>
        <View style={styles.avCard}>
          {rec.avoid_expressions.slice(0, 3).map((item, i) => (
            <View key={i} style={[styles.avItem, i > 0 && styles.avItemBorder]}>
              <View style={styles.avXBox}>
                <X size={11} color="#FF4D4D" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.avWrong}>{item.wrong}</Text>
                <Text style={styles.avReason}>{item.reason}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* ── 팁 ── */}
        <Text style={styles.sectionLabel}>팁</Text>
        <View style={styles.tipsCard}>
          {rec.tips.slice(0, 4).map((tip, i) => (
            <View key={i} style={[styles.tipItem, i > 0 && styles.tipItemBorder]}>
              <View style={styles.tipNum}>
                <Text style={styles.tipNumText}>{i + 1}</Text>
              </View>
              <Text style={styles.tipText}>{tip}</Text>
            </View>
          ))}
        </View>

      </ScrollView>

      {/* Footer */}
      <View style={styles.footer}>
        <TouchableOpacity style={[styles.startBtn, isStarting && styles.startBtnDisabled]} onPress={handleStartChat} disabled={isStarting}>
          <Text style={styles.startBtnText}>{isStarting ? '세션 준비 중...' : '대화 시작하기'}</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const BRAND = '#6C3BFF';
const BG    = '#F7F7FB';

const styles = StyleSheet.create({
  safe:    { flex: 1, backgroundColor: BG },
  content: { paddingHorizontal: 16, paddingBottom: 110, paddingTop: 4 },

  // Header
  header:      { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12 },
  headerBtn:   { width: 36, height: 36, borderRadius: 18, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 15, fontWeight: '500', color: '#111' },

  // Loading
  loadingWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12 },
  loadingText: { fontSize: 13, color: '#999' },

  // Context card
  ctxCard:   { backgroundColor: '#fff', borderRadius: 22, padding: 16, flexDirection: 'row', alignItems: 'center', gap: 14, marginBottom: 14 },
  ctxAvatar: { width: 56, height: 56, borderRadius: 28, alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  ctxInfo:   { flex: 1 },
  ctxLabel:  { fontSize: 10, color: '#bbb', fontWeight: '500', letterSpacing: 0.4, marginBottom: 2 },
  ctxName:   { fontSize: 18, fontWeight: '500', color: '#111', marginBottom: 4 },
  ctxSitRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  ctxSit:    { fontSize: 12, color: '#999' },

  // Recommended level
  recCard:    { backgroundColor: BRAND, borderRadius: 22, padding: 22, alignItems: 'center', gap: 10, marginBottom: 14, position: 'relative', overflow: 'hidden' },
  recBlob:    { position: 'absolute', width: 120, height: 120, borderRadius: 60, right: -30, top: -30, backgroundColor: 'rgba(255,255,255,0.08)' },
  recEye:     { fontSize: 10, fontWeight: '500', color: 'rgba(255,255,255,0.65)', letterSpacing: 0.6 },
  recBadge:   { backgroundColor: '#fff', borderRadius: 22, paddingHorizontal: 32, paddingVertical: 10 },
  recBadgeText:{ fontSize: 22, fontWeight: '500', color: BRAND },
  recReason:  { fontSize: 13, color: 'rgba(255,255,255,0.85)', textAlign: 'center', lineHeight: 20 },

  // Section label
  sectionLabel: { fontSize: 11, fontWeight: '500', color: '#999', letterSpacing: 0.5, marginBottom: 9 },

  // Examples
  exCard:          { backgroundColor: '#fff', borderRadius: 22, overflow: 'hidden', marginBottom: 14 },
  exSection:       { padding: 14 },
  exSectionBorder: { borderTopWidth: 0.5, borderTopColor: '#F0F0F8' },
  exSectionLabel:  { fontSize: 11, fontWeight: '500', color: BRAND, letterSpacing: 0.4, marginBottom: 10 },
  exChips:         { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  exChip:          { backgroundColor: '#EDE9FE', paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 },
  exChipText:      { fontSize: 13, fontWeight: '500', color: BRAND },

  // Avoid
  avCard:       { backgroundColor: '#fff', borderRadius: 22, overflow: 'hidden', marginBottom: 14 },
  avItem:       { flexDirection: 'row', alignItems: 'flex-start', gap: 12, padding: 14 },
  avItemBorder: { borderTopWidth: 0.5, borderTopColor: '#F0F0F8' },
  avXBox:       { width: 24, height: 24, borderRadius: 8, backgroundColor: '#FFEBE9', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 },
  avWrong:      { fontSize: 13, fontWeight: '500', color: '#FF4D4D', textDecorationLine: 'line-through', marginBottom: 3 },
  avReason:     { fontSize: 12, color: '#999', lineHeight: 17 },

  // Tips
  tipsCard:      { backgroundColor: '#fff', borderRadius: 22, overflow: 'hidden', marginBottom: 14 },
  tipItem:       { flexDirection: 'row', alignItems: 'flex-start', gap: 12, padding: 14 },
  tipItemBorder: { borderTopWidth: 0.5, borderTopColor: '#F0F0F8' },
  tipNum:        { width: 22, height: 22, borderRadius: 8, backgroundColor: '#EDE9FE', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 1 },
  tipNumText:    { fontSize: 11, fontWeight: '500', color: BRAND },
  tipText:       { flex: 1, fontSize: 13, color: '#444', lineHeight: 20 },

  // Footer
  footer:       { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 16, paddingBottom: 28, backgroundColor: BG },
  startBtn:     { backgroundColor: BRAND, borderRadius: 22, paddingVertical: 15, alignItems: 'center' },
  startBtnDisabled: { opacity: 0.7 },
  startBtnText: { fontSize: 15, fontWeight: '500', color: '#fff' },
});