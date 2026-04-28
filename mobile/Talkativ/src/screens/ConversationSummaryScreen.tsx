import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, ActivityIndicator, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  BookOpen, AlertCircle, CheckCircle, Bookmark,
  TrendingUp, ChevronDown, ChevronLeft,
} from 'lucide-react-native';
import { Icon } from '../components';

const AI_SERVER = 'http://10.0.2.2:8000';

// ─── Types ────────────────────────────────────────────────────────────────────

interface MistakeItem {
  original:    string;
  correction:  string;
  explanation: string;
  type:        'grammar' | 'vocabulary' | 'politeness' | 'naturalness';
}

interface VocabularyItem {
  word:    string;
  meaning: string;
  example: string;
  kind:    'word' | 'phrase';
}

interface ScoreDetail {
  source?: string;
  used_fallback?: boolean;
  note?: string;
  components?: Record<string, any>;
}

interface SummaryData {
  scores:       { speechAccuracy: number; vocabulary: number; naturalness: number };
  mistakes:     MistakeItem[];
  learnedVocab: VocabularyItem[];
  improvements: string;
  scoreDetails: { speechAccuracy?: ScoreDetail; vocabulary?: ScoreDetail; naturalness?: ScoreDetail };
  usedFallbackScores: boolean;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const toMistakeType = (t: string): MistakeItem['type'] => {
  if (t === 'speech_level' || t === 'honorific')   return 'politeness';
  if (t === 'grammar'      || t === 'spelling')    return 'grammar';
  if (t === 'vocabulary'   || t === 'word_choice') return 'vocabulary';
  return 'naturalness';
};

const MISTAKE_META: Record<string, { label: string; color: string }> = {
  grammar:     { label: '문법',       color: '#FF4D4D' },
  vocabulary:  { label: '어휘',       color: '#EAB308' },
  politeness:  { label: '존댓말',     color: '#6C3BFF' },
  naturalness: { label: '자연스러움', color: '#22C55E' },
};

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function ConversationSummaryScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();

  const [loading,         setLoading]         = useState(true);
  const [summary,         setSummary]         = useState<SummaryData | null>(null);
  const [savedWords,      setSavedWords]      = useState<Record<string, VocabularyItem>>({});
  const [expandedMistake, setExpandedMistake] = useState<number | null>(null);
  const [saveSuccess,     setSaveSuccess]     = useState<string | null>(null);

  const { avatar, duration, conversationHistory, sessionCorrections, avgScore } = route.params || {};

  const handleToggleSave = (item: VocabularyItem) => {
    setSavedWords(prev => {
      const next = { ...prev };
      if (next[item.word]) {
        delete next[item.word];
      } else {
        next[item.word] = item;
        setSaveSuccess(item.word);
        setTimeout(() => setSaveSuccess(null), 1500);
      }
      return next;
    });
  };

  const handleSaveAll = () => {
    if (!summary) return;
    const entries: Record<string, VocabularyItem> = {};
    summary.learnedVocab.forEach(v => { entries[v.word] = v; });
    setSavedWords(prev => ({ ...prev, ...entries }));
    Alert.alert('저장 완료', `${summary.learnedVocab.length}개가 저장됐어요!`);
  };

  const buildSummary = useCallback(async () => {
    setLoading(true);
    try {
      const speechScore = avgScore ?? 80;
      const mistakes: MistakeItem[] = sessionCorrections
        ? sessionCorrections
            .flatMap((s: any) => s.corrections || [])
            .filter((c: any) => c.severity === 'error' || c.severity === 'warning')
            .slice(0, 6)
            .map((c: any) => ({
              original:    c.original    || '',
              correction:  c.corrected   || '',
              explanation: c.explanation || '',
              type:        toMistakeType(c.type || ''),
            }))
        : [];

      const history = (conversationHistory || []).map((m: any) => ({
        role:    m.role || (m.sender === 'ai' ? 'assistant' : 'user'),
        content: m.content || m.text || '',
      }));

      const res = await fetch(`${AI_SERVER}/api/v1/chat/analyze`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          avatar: {
            id:                 avatar?.id                 || 'test',
            name_ko:            avatar?.name_ko            || '아바타',
            role:               avatar?.role               || 'friend',
            personality_traits: avatar?.personality_traits || [],
            interests:          avatar?.interests          || [],
            dislikes:           avatar?.dislikes           || [],
          },
          conversation_history: history,
        }),
      });

      if (!res.ok) throw new Error(`Analyze error: ${res.status}`);
      const data = await res.json();

      const words: VocabularyItem[] = (data.vocabulary_to_learn || []).map((v: any) => ({
        word: v.word || '', meaning: v.meaning || '', example: v.example || '', kind: 'word' as const,
      }));
      const phrases: VocabularyItem[] = (data.phrases_to_learn || []).map((p: any) => ({
        word: p.phrase || p.word || '', meaning: p.meaning || '', example: p.example || '', kind: 'phrase' as const,
      }));
      const learnedVocab = [...words, ...phrases]
        .filter((v, i, arr) => v.word && arr.findIndex(x => x.word === v.word) === i)
        .slice(0, 8);

      const finalMistakes = mistakes.length > 0 ? mistakes
        : (data.mistakes || []).slice(0, 6).map((m: any) => ({
            original:    m.original    || '',
            correction:  m.corrected   || '',
            explanation: m.explanation || '',
            type:        toMistakeType(m.type || ''),
          }));

      setSummary({
        scores: {
          speechAccuracy: (data.scores?.speech_accuracy ?? speechScore) / 100,
          vocabulary:     (data.scores?.vocabulary      ?? 75)          / 100,
          naturalness:    (data.scores?.naturalness     ?? 78)          / 100,
        },
        mistakes:     finalMistakes,
        learnedVocab,
        improvements: data.overall_feedback || '대화를 잘 진행하셨습니다!',
        scoreDetails: {
          speechAccuracy: data.score_details?.speech_accuracy,
          vocabulary: data.score_details?.vocabulary,
          naturalness: data.score_details?.naturalness,
        },
        usedFallbackScores: Boolean(data.used_fallback_scores),
      });
    } catch (error) {
      console.error('Summary error:', error);
      const speechScore = avgScore ?? 80;
      const mistakes: MistakeItem[] = sessionCorrections
        ? sessionCorrections
            .flatMap((s: any) => s.corrections || [])
            .filter((c: any) => c.severity === 'error' || c.severity === 'warning')
            .slice(0, 6)
            .map((c: any) => ({
              original:    c.original    || '',
              correction:  c.corrected   || '',
              explanation: c.explanation || '',
              type:        toMistakeType(c.type || ''),
            }))
        : [];
      setSummary({
        scores: { speechAccuracy: speechScore / 100, vocabulary: 0.75, naturalness: 0.78 },
        mistakes, learnedVocab: [], improvements: '분석 서버 연결에 실패해 일부 기본 점수를 표시하고 있어요.',
        scoreDetails: {
          speechAccuracy: { source: 'frontend_fallback', used_fallback: true, note: '세션 평균 교정 점수를 사용했습니다.' },
          vocabulary: { source: 'frontend_fallback', used_fallback: true, note: '분석 서버 연결 실패로 기본값을 사용했습니다.' },
          naturalness: { source: 'frontend_fallback', used_fallback: true, note: '분석 서버 연결 실패로 기본값을 사용했습니다.' },
        },
        usedFallbackScores: true,
      });
    } finally {
      setLoading(false);
    }
  }, [avatar, avgScore, conversationHistory, sessionCorrections]);

  useEffect(() => { buildSummary(); }, [buildSummary]);

  const handleContinue = () => {
    navigation.navigate('Analytics', {
      avatar,
      duration,
      scores: summary?.scores,
      scoreDetails: summary?.scoreDetails,
      usedFallbackScores: summary?.usedFallbackScores,
      savedWords: Object.values(savedWords),
    });
  };

  // ── Loading ────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <View style={styles.header}>
          <View style={styles.headerBtn} />
          <Text style={styles.headerTitle}>대화 분석 중...</Text>
          <View style={styles.headerBtn} />
        </View>
        <View style={styles.loadingWrap}>
          <ActivityIndicator size="large" color="#6C3BFF" />
          <Text style={styles.loadingText}>AI가 대화를 분석하고 있어요</Text>
          <Text style={styles.loadingHint}>배울 단어와 표현을 찾고 있어요</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!summary) return null;
  const savedCount = Object.keys(savedWords).length;
  const scoreCards = [
    { value: summary.scores.speechAccuracy, label: '말투 정확도', detail: summary.scoreDetails.speechAccuracy },
    { value: summary.scores.vocabulary, label: '어휘력', detail: summary.scoreDetails.vocabulary },
    { value: summary.scores.naturalness, label: '자연스러움', detail: summary.scoreDetails.naturalness },
  ];

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <ChevronLeft size={22} color="#111" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>대화 요약</Text>
        <View style={styles.headerBtn} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* ── Score card ── */}
        <View style={styles.scoreCard}>
          <View style={styles.scoreBlob} />
          <View style={styles.scoreTop}>
            <View style={[styles.avatarCircle, { backgroundColor: avatar?.avatar_bg || BRAND }]}>
              <Icon name={avatar?.icon || 'user'} size={18} color="#fff" />
            </View>
            <View>
              <Text style={styles.scoreName}>{avatar?.name_ko || '아바타'}와의 대화</Text>
              <Text style={styles.scoreSub}>
                {sessionCorrections?.length > 0
                  ? `${sessionCorrections.length}개 메시지 분석`
                  : '대화 분석 결과'}
                {duration ? ` · ${duration}` : ''}
              </Text>
            </View>
          </View>
          <View style={styles.scoreNums}>
            {scoreCards.map((s, i) => (
              <View key={i} style={styles.scoreCol}>
                <Text style={styles.scoreNum}>{Math.round(s.value * 100)}</Text>
                <View style={styles.scoreBarTrack}>
                  <View style={[styles.scoreBarFill, { width: `${Math.round(s.value * 100)}%` as any }]} />
                </View>
                <Text style={styles.scoreColLabel}>{s.label}</Text>
                {s.detail?.source ? (
                  <Text style={styles.scoreSourceLabel}>
                    {s.detail.used_fallback ? '기본값 사용' : s.detail.source === 'rule_based' ? '규칙 기반' : '혼합 계산'}
                  </Text>
                ) : null}
              </View>
            ))}
          </View>
          <View style={styles.scoreMetaBox}>
            <Text style={styles.scoreMetaTitle}>
              {summary.usedFallbackScores ? '일부 점수는 임시값입니다' : '점수는 실제 계산 근거를 함께 표시합니다'}
            </Text>
            {scoreCards.map((item, index) => (
              item.detail?.note ? (
                <Text key={index} style={styles.scoreMetaText}>
                  {item.label}: {item.detail.note}
                </Text>
              ) : null
            ))}
          </View>
        </View>

        {/* ── Mistakes ── */}
        <View style={styles.sectionHead}>
          <AlertCircle size={14} color="#FF4D4D" />
          <Text style={styles.sectionTitle}>틀린 부분</Text>
          {summary.mistakes.length > 0 && (
            <View style={styles.countBadge}>
              <Text style={styles.countBadgeText}>{summary.mistakes.length}</Text>
            </View>
          )}
        </View>

        {summary.mistakes.length === 0 ? (
          <View style={[styles.card, styles.emptyCard]}>
            <CheckCircle size={24} color="#22C55E" />
            <Text style={styles.emptyText}>실수가 없어요. 완벽해요!</Text>
          </View>
        ) : (
          <View style={styles.list}>
            {summary.mistakes.map((m, i) => {
              const meta     = MISTAKE_META[m.type] || { label: m.type, color: '#999' };
              const expanded = expandedMistake === i;
              return (
                <View key={i} style={styles.card}>
                  <TouchableOpacity
                    style={styles.mistakeHdr}
                    onPress={() => setExpandedMistake(expanded ? null : i)}
                    activeOpacity={0.7}
                  >
                    <View style={[styles.typePill, { backgroundColor: meta.color + '14' }]}>
                      <Text style={[styles.typePillText, { color: meta.color }]}>{meta.label}</Text>
                    </View>
                    <View style={{ flex: 1 }} />
                    <ChevronDown
                      size={14}
                      color="#bbb"
                      style={{ transform: [{ rotate: expanded ? '180deg' : '0deg' }] }}
                    />
                  </TouchableOpacity>

                  {/* Compare boxes — always visible */}
                  <View style={styles.cmpRow}>
                    <View style={styles.cmpInput}>
                      <Text style={styles.cmpLblPurple}>입력</Text>
                      <Text style={styles.cmpOrigText}>{m.original}</Text>
                    </View>
                    <Text style={styles.cmpArrow}>→</Text>
                    <View style={styles.cmpFixed}>
                      <Text style={styles.cmpLblGreen}>수정</Text>
                      <Text style={styles.cmpFixedText}>{m.correction}</Text>
                    </View>
                  </View>

                  {/* Explanation — collapsible */}
                  {expanded && (
                    <View style={styles.explanationBox}>
                      <Text style={styles.explanationText}>{m.explanation}</Text>
                    </View>
                  )}
                </View>
              );
            })}
          </View>
        )}

        {/* ── Vocab ── */}
        <View style={styles.sectionHead}>
          <BookOpen size={14} color={BRAND} />
          <Text style={styles.sectionTitle}>배운 단어 & 표현</Text>
          {summary.learnedVocab.length > 0 && (
            <TouchableOpacity style={styles.saveAllBtn} onPress={handleSaveAll}>
              <Bookmark size={11} color={BRAND} />
              <Text style={styles.saveAllText}>모두 저장</Text>
            </TouchableOpacity>
          )}
        </View>
        <Text style={styles.sectionSub}>이번 대화에서 배우면 좋은 단어와 표현이에요</Text>

        {summary.learnedVocab.length === 0 ? (
          <View style={[styles.card, styles.emptyCard]}>
            <Text style={styles.emptyText}>이번 대화에서 특별히 배울 단어가 없어요</Text>
          </View>
        ) : (
          <View style={styles.list}>
            {summary.learnedVocab.map((item, i) => {
              const isSaved   = !!savedWords[item.word];
              const justSaved = saveSuccess === item.word;
              return (
                <View key={i} style={[styles.card, styles.vocabCard, isSaved && styles.cardSaved]}>
                  <View style={styles.vocabTop}>
                    <Text style={styles.vocabWord}>{item.word}</Text>
                    <View style={[styles.kindPill, item.kind === 'phrase' ? styles.kindPillPhrase : styles.kindPillWord]}>
                      <Text style={[styles.kindPillText, item.kind === 'phrase' ? styles.kindTextPhrase : styles.kindTextWord]}>
                        {item.kind === 'phrase' ? '표현' : '단어'}
                      </Text>
                    </View>
                    <TouchableOpacity
                      style={[styles.bookmarkBtn, isSaved && styles.bookmarkBtnOn]}
                      onPress={() => handleToggleSave(item)}
                      activeOpacity={0.7}
                    >
                      <Bookmark size={14} color={isSaved ? '#fff' : BRAND} fill={isSaved ? '#fff' : 'none'} />
                    </TouchableOpacity>
                  </View>
                  {item.meaning ? <Text style={styles.vocabMeaning}>{item.meaning}</Text> : null}
                  {item.example ? (
                    <View style={styles.vocabEx}>
                      <Text style={styles.vocabExLabel}>예문</Text>
                      <Text style={styles.vocabExText}>{item.example}</Text>
                    </View>
                  ) : null}
                  {justSaved && (
                    <View style={styles.savedToast}>
                      <CheckCircle size={11} color="#22C55E" />
                      <Text style={styles.savedToastText}>저장됐어요!</Text>
                    </View>
                  )}
                </View>
              );
            })}
          </View>
        )}

        {/* ── AI feedback ── */}
        <View style={styles.sectionHead}>
          <TrendingUp size={14} color="#22C55E" />
          <Text style={styles.sectionTitle}>AI 피드백</Text>
        </View>
        <View style={[styles.card, styles.feedbackCard]}>
          <View style={styles.feedbackIcon}>
            <CheckCircle size={14} color="#22C55E" />
          </View>
          <Text style={styles.feedbackText}>{summary.improvements}</Text>
        </View>

        {/* ── Saved banner ── */}
        {savedCount > 0 && (
          <View style={styles.savedBanner}>
            <Bookmark size={13} color={BRAND} fill={BRAND} />
            <Text style={styles.savedBannerText}>{savedCount}개 단어가 저장됐어요</Text>
          </View>
        )}

      </ScrollView>

      {/* Footer */}
      <View style={styles.footer}>
        <TouchableOpacity style={styles.continueBtn} onPress={handleContinue}>
          <Text style={styles.continueBtnText}>계속하기</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const BRAND  = '#6C3BFF';
const GREY   = '#F2F2F7';
const BORDER = '#E5E5EA';

const styles = StyleSheet.create({
  safe:    { flex: 1, backgroundColor: '#fff' },
  content: { paddingHorizontal: 16, paddingBottom: 110, paddingTop: 8 },

  // Header
  header:      { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 14, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: BORDER },
  headerBtn:   { width: 36, alignItems: 'center' },
  headerTitle: { fontSize: 15, fontWeight: '500', color: '#111' },

  // Loading
  loadingWrap: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10 },
  loadingText: { fontSize: 15, fontWeight: '500', color: '#111' },
  loadingHint: { fontSize: 12, color: '#999' },

  // Score card
  scoreCard:     { backgroundColor: BRAND, borderRadius: 20, padding: 18, marginBottom: 20, marginTop: 4, position: 'relative', overflow: 'hidden' },
  scoreBlob:     { position: 'absolute', width: 140, height: 140, borderRadius: 70, right: -40, top: -40, backgroundColor: 'rgba(255,255,255,0.10)' },
  scoreTop:      { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 16 },
  avatarCircle:  { width: 38, height: 38, borderRadius: 19, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(255,255,255,0.25)' },
  scoreName:     { fontSize: 14, fontWeight: '500', color: '#fff' },
  scoreSub:      { fontSize: 11, color: 'rgba(255,255,255,0.70)', marginTop: 1 },
  scoreNums:     { flexDirection: 'row', gap: 8 },
  scoreCol:      { flex: 1, backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 12, padding: 10, alignItems: 'center', gap: 4 },
  scoreNum:      { fontSize: 22, fontWeight: '500', color: '#fff', lineHeight: 26 },
  scoreBarTrack: { width: '100%', height: 3, borderRadius: 2, backgroundColor: 'rgba(255,255,255,0.25)', overflow: 'hidden' },
  scoreBarFill:  { height: '100%', borderRadius: 2, backgroundColor: '#fff' },
  scoreColLabel: { fontSize: 10, color: 'rgba(255,255,255,0.75)', textAlign: 'center' },
  scoreSourceLabel: { fontSize: 9, color: 'rgba(255,255,255,0.78)', textAlign: 'center' },
  scoreMetaBox:  { marginTop: 12, padding: 10, borderRadius: 12, backgroundColor: 'rgba(255,255,255,0.12)', gap: 4 },
  scoreMetaTitle: { fontSize: 11, fontWeight: '600', color: '#fff' },
  scoreMetaText: { fontSize: 10, lineHeight: 15, color: 'rgba(255,255,255,0.85)' },

  // Section
  sectionHead:    { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10, marginTop: 6 },
  sectionTitle:   { flex: 1, fontSize: 14, fontWeight: '500', color: '#111' },
  sectionSub:     { fontSize: 12, color: '#999', marginTop: -6, marginBottom: 10 },
  countBadge:     { paddingHorizontal: 8, paddingVertical: 3, backgroundColor: 'rgba(255,77,77,0.10)', borderRadius: 20 },
  countBadgeText: { fontSize: 11, fontWeight: '500', color: '#FF4D4D' },
  saveAllBtn:     { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 10, paddingVertical: 5, backgroundColor: GREY, borderRadius: 20 },
  saveAllText:    { fontSize: 11, fontWeight: '500', color: BRAND },

  // Card
  card:     { backgroundColor: '#fff', borderRadius: 14, borderWidth: 0.5, borderColor: BORDER, overflow: 'hidden', marginBottom: 8 },
  cardSaved:{ borderColor: BRAND, borderWidth: 1 },
  list:     { marginBottom: 4 },

  // Empty
  emptyCard: { alignItems: 'center', gap: 10, paddingVertical: 24, paddingHorizontal: 20, marginBottom: 8 },
  emptyText: { fontSize: 13, color: '#999' },

  // Mistake
  mistakeHdr:  { flexDirection: 'row', alignItems: 'center', padding: 12, paddingBottom: 10 },
  typePill:    { paddingHorizontal: 9, paddingVertical: 4, borderRadius: 20 },
  typePillText:{ fontSize: 10, fontWeight: '500' },

  // Compare boxes
  cmpRow:       { flexDirection: 'row', alignItems: 'stretch', gap: 6, paddingHorizontal: 12, paddingBottom: 12 },
  cmpInput:     { flex: 1, padding: 9, borderRadius: 10, backgroundColor: '#fff', borderWidth: 1, borderColor: 'rgba(108,59,255,0.35)' },
  cmpFixed:     { flex: 1, padding: 9, borderRadius: 10, backgroundColor: '#fff', borderWidth: 1, borderColor: 'rgba(34,197,94,0.35)' },
  cmpLblPurple: { fontSize: 9, fontWeight: '500', letterSpacing: 0.06, marginBottom: 3, color: BRAND },
  cmpLblGreen:  { fontSize: 9, fontWeight: '500', letterSpacing: 0.06, marginBottom: 3, color: '#22C55E' },
  cmpOrigText:  { fontSize: 13, fontWeight: '500', color: '#888', textDecorationLine: 'line-through' },
  cmpFixedText: { fontSize: 13, fontWeight: '500', color: '#22C55E' },
  cmpArrow:     { alignSelf: 'center', fontSize: 12, color: '#bbb' },

  // Explanation
  explanationBox: { backgroundColor: GREY, padding: 12, borderTopWidth: 0.5, borderTopColor: BORDER },
  explanationText:{ fontSize: 12, color: '#555', lineHeight: 18 },

  // Vocab
  vocabCard:       { padding: 13 },
  vocabTop:        { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  vocabWord:       { fontSize: 15, fontWeight: '500', color: '#111', flex: 1 },
  kindPill:        { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 20 },
  kindPillWord:    { backgroundColor: 'rgba(2,132,199,0.10)' },
  kindPillPhrase:  { backgroundColor: 'rgba(108,59,255,0.10)' },
  kindPillText:    { fontSize: 10, fontWeight: '500' },
  kindTextWord:    { color: '#0284C7' },
  kindTextPhrase:  { color: BRAND },
  bookmarkBtn:     { width: 30, height: 30, borderRadius: 15, backgroundColor: GREY, borderWidth: 0.5, borderColor: BORDER, alignItems: 'center', justifyContent: 'center' },
  bookmarkBtnOn:   { backgroundColor: BRAND, borderColor: BRAND },
  vocabMeaning:    { fontSize: 12, color: '#666', marginBottom: 8 },
  vocabEx:         { backgroundColor: GREY, borderRadius: 10, padding: 9 },
  vocabExLabel:    { fontSize: 9, fontWeight: '500', color: BRAND, letterSpacing: 0.06, marginBottom: 3 },
  vocabExText:     { fontSize: 12, color: '#333', lineHeight: 18 },
  savedToast:      { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 8 },
  savedToastText:  { fontSize: 11, color: '#22C55E', fontWeight: '500' },

  // Feedback
  feedbackCard: { flexDirection: 'row', gap: 10, padding: 14, marginBottom: 8 },
  feedbackIcon: { width: 28, height: 28, borderRadius: 8, backgroundColor: 'rgba(34,197,94,0.10)', alignItems: 'center', justifyContent: 'center' },
  feedbackText: { flex: 1, fontSize: 13, color: '#333', lineHeight: 20 },

  // Saved banner
  savedBanner:     { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: GREY, paddingVertical: 12, paddingHorizontal: 14, borderRadius: 12, marginTop: 4, marginBottom: 8 },
  savedBannerText: { flex: 1, fontSize: 13, fontWeight: '500', color: BRAND },

  // Footer
  footer:          { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 16, backgroundColor: '#fff', borderTopWidth: 1, borderTopColor: BORDER },
  continueBtn:     { backgroundColor: BRAND, borderRadius: 22, paddingVertical: 14, alignItems: 'center' },
  continueBtnText: { fontSize: 15, fontWeight: '500', color: '#fff' },
});
