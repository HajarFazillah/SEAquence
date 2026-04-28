import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  TouchableOpacity, ActivityIndicator, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  BookOpen, AlertTriangle, CheckCircle, Bookmark,
  TrendingUp, Sparkles, ChevronDown, ChevronUp, Star,
} from 'lucide-react-native';
import { Header, Card, Button, ProgressBar, Icon } from '../components';

const AI_SERVER = 'http://10.0.2.2:8000';

// ── 타입 ─────────────────────────────────────────────────────────
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

interface SummaryData {
  scores:       { speechAccuracy: number; vocabulary: number; naturalness: number; };
  mistakes:     MistakeItem[];
  learnedVocab: VocabularyItem[];
  improvements: string;
}

const toMistakeType = (t: string): MistakeItem['type'] => {
  if (t === 'speech_level' || t === 'honorific')   return 'politeness';
  if (t === 'grammar'      || t === 'spelling')    return 'grammar';
  if (t === 'vocabulary'   || t === 'word_choice') return 'vocabulary';
  return 'naturalness';
};

export default function ConversationSummaryScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();

  // ── 모든 hooks 최상단 ─────────────────────────────────────────
  const [loading,         setLoading]         = useState(true);
  const [summary,         setSummary]         = useState<SummaryData | null>(null);
  const [savedWords,      setSavedWords]      = useState<Record<string, VocabularyItem>>({});
  const [expandedMistake, setExpandedMistake] = useState<number | null>(null);
  const [saveSuccess,     setSaveSuccess]     = useState<string | null>(null);

  const {
    avatar,
    duration,
    conversationHistory,
    sessionCorrections,
    avgScore,
  } = route.params || {};

  useEffect(() => {
    buildSummary();
  }, []);

  // ── 북마크 토글 ───────────────────────────────────────────────
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

  // ── 핵심: 항상 AI 서버에 전체 대화 전송 ──────────────────────
  const buildSummary = async () => {
    setLoading(true);
    try {
      // ── 점수 + 틀린 부분: sessionCorrections 우선 (빠름) ──────
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

      // ── 배울 단어/표현: 항상 AI 서버 전체 대화 분석 ───────────
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

      // 단어 + 표현 병합
      const words: VocabularyItem[] = (data.vocabulary_to_learn || []).map((v: any) => ({
        word:    v.word    || '',
        meaning: v.meaning || '',
        example: v.example || '',
        kind:    'word' as const,
      }));
      const phrases: VocabularyItem[] = (data.phrases_to_learn || []).map((p: any) => ({
        word:    p.phrase  || p.word || '',
        meaning: p.meaning || '',
        example: p.example || '',
        kind:    'phrase' as const,
      }));
      const learnedVocab = [...words, ...phrases]
        .filter((v, i, arr) => v.word && arr.findIndex(x => x.word === v.word) === i)
        .slice(0, 8);

      // AI 서버가 계산한 점수가 있으면 사용, 없으면 sessionCorrections 점수
      const aiSpeechScore   = data.scores?.speech_accuracy ?? speechScore;
      const aiVocabScore    = data.scores?.vocabulary      ?? 75;
      const aiNaturalScore  = data.scores?.naturalness     ?? 78;

      // 틀린 부분은 sessionCorrections 우선, 없으면 AI 서버 mistakes
      const finalMistakes = mistakes.length > 0
        ? mistakes
        : (data.mistakes || []).slice(0, 6).map((m: any) => ({
            original:    m.original    || '',
            correction:  m.corrected   || '',
            explanation: m.explanation || '',
            type:        toMistakeType(m.type || ''),
          }));

      setSummary({
        scores: {
          speechAccuracy: aiSpeechScore / 100,
          vocabulary:     aiVocabScore  / 100,
          naturalness:    aiNaturalScore / 100,
        },
        mistakes:     finalMistakes,
        learnedVocab,
        improvements: data.overall_feedback || '대화를 잘 진행하셨습니다!',
      });

    } catch (error) {
      console.error('Summary error:', error);

      // 폴백 — sessionCorrections만 사용
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
        scores:       { speechAccuracy: speechScore / 100, vocabulary: 0.75, naturalness: 0.78 },
        mistakes,
        learnedVocab: [],
        improvements: '대화를 잘 진행하셨습니다!',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => {
    navigation.navigate('Analytics', {
      avatar, duration,
      scores:     summary?.scores,
      savedWords: Object.values(savedWords),
    });
  };

  const getMistakeTypeColor = (type: string) =>
    ({ grammar: '#E53935', vocabulary: '#F4A261', politeness: '#6C3BFF', naturalness: '#4CAF50' }[type] || '#6C6C80');
  const getMistakeTypeLabel = (type: string) =>
    ({ grammar: '문법', vocabulary: '어휘', politeness: '존댓말', naturalness: '자연스러움' }[type] || type);

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <Header title="대화 분석 중..." showBack={false} />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6C3BFF" />
          <Text style={styles.loadingText}>AI가 대화를 분석하고 있어요...</Text>
          <Text style={styles.loadingSubtext}>배울 단어와 표현을 찾고 있어요</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!summary) return null;

  const savedCount = Object.keys(savedWords).length;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="대화 요약" showBack={false} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* ── 점수 카드 ── */}
        <Card variant="elevated" style={styles.scoreCard}>
          <View style={styles.scoreHeader}>
            <View style={[styles.avatarIcon, { backgroundColor: avatar?.avatar_bg || '#FFB6C1' }]}>
              <Icon name={avatar?.icon || 'user'} size={24} color="#FFFFFF" />
            </View>
            <View style={styles.scoreHeaderText}>
              <Text style={styles.scoreTitle}>{avatar?.name_ko || '아바타'}와의 대화</Text>
              <Text style={styles.scoreSubtitle}>
                {sessionCorrections?.length > 0 ? `${sessionCorrections.length}개 메시지 분석됨` : '대화 분석 결과'}
                {duration ? ` · ${duration}` : ''}
              </Text>
            </View>
          </View>
          <View style={styles.scoresGrid}>
            {[
              { value: summary.scores.speechAccuracy, label: '말투 정확도', color: '#6C3BFF' },
              { value: summary.scores.vocabulary,     label: '어휘력',      color: '#4CAF50' },
              { value: summary.scores.naturalness,    label: '자연스러움',  color: '#F4A261' },
            ].map((s, i) => (
              <View key={i} style={styles.scoreItem}>
                <Text style={styles.scoreValue}>{Math.round(s.value * 100)}%</Text>
                <Text style={styles.scoreLabel}>{s.label}</Text>
                <ProgressBar progress={s.value} color={s.color} style={styles.scoreBar} />
              </View>
            ))}
          </View>
        </Card>

        {/* ── 틀린 부분 ── */}
        <View style={styles.sectionHeader}>
          <AlertTriangle size={20} color="#E53935" />
          <Text style={styles.sectionTitle}>틀린 부분</Text>
          <View style={styles.countBadge}>
            <Text style={styles.countBadgeText}>{summary.mistakes.length}</Text>
          </View>
        </View>
        <View style={styles.mistakesList}>
          {summary.mistakes.length === 0 ? (
            <Card variant="elevated">
              <View style={{ alignItems: 'center', padding: 16 }}>
                <CheckCircle size={32} color="#4CAF50" />
                <Text style={styles.noMistakeText}>실수가 없어요! 완벽해요 🎉</Text>
              </View>
            </Card>
          ) : summary.mistakes.map((mistake, index) => (
            <Card key={index} variant="outlined" style={styles.mistakeCard}>
              <TouchableOpacity
                style={styles.mistakeHeader}
                onPress={() => setExpandedMistake(expandedMistake === index ? null : index)}
              >
                <View style={[styles.mistakeTypeBadge, { backgroundColor: getMistakeTypeColor(mistake.type) + '20' }]}>
                  <Text style={[styles.mistakeTypeText, { color: getMistakeTypeColor(mistake.type) }]}>
                    {getMistakeTypeLabel(mistake.type)}
                  </Text>
                </View>
                {expandedMistake === index ? <ChevronUp size={20} color="#6C6C80" /> : <ChevronDown size={20} color="#6C6C80" />}
              </TouchableOpacity>
              <View style={styles.mistakeContent}>
                <View style={styles.mistakeRow}>
                  <Text style={styles.mistakeLabelX}>✗</Text>
                  <Text style={styles.mistakeOriginal}>{mistake.original}</Text>
                </View>
                <View style={styles.mistakeRow}>
                  <Text style={styles.mistakeLabelOk}>✓</Text>
                  <Text style={styles.mistakeCorrection}>{mistake.correction}</Text>
                </View>
              </View>
              {expandedMistake === index && (
                <View style={styles.explanationBox}>
                  <Text style={styles.explanationText}>{mistake.explanation}</Text>
                </View>
              )}
            </Card>
          ))}
        </View>

        {/* ── 배운 단어 & 표현 ── */}
        <View style={styles.sectionHeader}>
          <BookOpen size={20} color="#6C3BFF" />
          <Text style={styles.sectionTitle}>배운 단어 & 표현</Text>
          {summary.learnedVocab.length > 0 && (
            <TouchableOpacity style={styles.saveAllBtn} onPress={handleSaveAll}>
              <Bookmark size={14} color="#6C3BFF" />
              <Text style={styles.saveAllText}>모두 저장</Text>
            </TouchableOpacity>
          )}
        </View>
        <Text style={styles.sectionDesc}>이번 대화에서 배우면 좋은 단어와 표현이에요</Text>

        {summary.learnedVocab.length === 0 ? (
          <Card variant="elevated" style={{ marginBottom: 20 }}>
            <View style={{ alignItems: 'center', padding: 16 }}>
              <Text style={{ fontSize: 13, color: '#6C6C80' }}>이번 대화에서 특별히 배울 단어가 없어요 👍</Text>
            </View>
          </Card>
        ) : (
          <View style={styles.vocabList}>
            {summary.learnedVocab.map((item, index) => {
              const isSaved   = !!savedWords[item.word];
              const justSaved = saveSuccess === item.word;
              return (
                <Card key={index} variant="elevated" style={[styles.vocabCard, isSaved && styles.vocabCardSaved]}>
                  <View style={styles.vocabHeader}>
                    <View style={styles.vocabWordRow}>
                      <Text style={styles.vocabWord}>{item.word}</Text>
                      <View style={[styles.kindBadge, item.kind === 'phrase' ? styles.kindBadgePhrase : styles.kindBadgeWord]}>
                        <Text style={[styles.kindBadgeText, item.kind === 'phrase' ? styles.kindBadgeTextPhrase : styles.kindBadgeTextWord]}>
                          {item.kind === 'phrase' ? '표현' : '단어'}
                        </Text>
                      </View>
                    </View>
                    <TouchableOpacity
                      style={[styles.bookmarkBtn, isSaved && styles.bookmarkBtnSaved]}
                      onPress={() => handleToggleSave(item)}
                      activeOpacity={0.7}
                    >
                      <Bookmark size={18} color={isSaved ? '#FFFFFF' : '#6C3BFF'} fill={isSaved ? '#FFFFFF' : 'transparent'} />
                    </TouchableOpacity>
                  </View>
                  {item.meaning ? <Text style={styles.vocabMeaning}>{item.meaning}</Text> : null}
                  {item.example ? (
                    <View style={styles.vocabExample}>
                      <Text style={styles.vocabExampleLabel}>예문</Text>
                      <Text style={styles.vocabExampleText}>{item.example}</Text>
                    </View>
                  ) : null}
                  {justSaved && (
                    <View style={styles.savedToast}>
                      <CheckCircle size={12} color="#4CAF50" />
                      <Text style={styles.savedToastText}>저장됐어요!</Text>
                    </View>
                  )}
                </Card>
              );
            })}
          </View>
        )}

        {/* ── 전체 피드백 ── */}
        <View style={styles.sectionHeader}>
          <CheckCircle size={20} color="#4CAF50" />
          <Text style={styles.sectionTitle}>AI 피드백</Text>
        </View>
        <Card variant="elevated" style={styles.feedbackCard}>
          <View style={styles.feedbackRow}>
            <Sparkles size={16} color="#4CAF50" />
            <Text style={styles.feedbackText}>{summary.improvements}</Text>
          </View>
        </Card>

        {/* ── 저장 현황 ── */}
        {savedCount > 0 && (
          <View style={styles.savedBanner}>
            <Star size={16} color="#6C3BFF" fill="#6C3BFF" />
            <Text style={styles.savedBannerText}>{savedCount}개 단어가 저장됐어요</Text>
          </View>
        )}

      </ScrollView>

      <View style={styles.footer}>
        <Button title="계속하기" onPress={handleContinue} showArrow />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:    { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  loadingText:      { fontSize: 16, fontWeight: '600', color: '#1A1A2E', marginTop: 16 },
  loadingSubtext:   { fontSize: 13, color: '#6C6C80', marginTop: 4 },

  scoreCard:       { marginBottom: 24 },
  scoreHeader:     { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
  avatarIcon:      { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  scoreHeaderText: { flex: 1 },
  scoreTitle:      { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },
  scoreSubtitle:   { fontSize: 13, color: '#6C6C80' },
  scoresGrid:      { flexDirection: 'row', gap: 12 },
  scoreItem:       { flex: 1, alignItems: 'center' },
  scoreValue:      { fontSize: 24, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  scoreLabel:      { fontSize: 11, color: '#6C6C80', marginBottom: 8 },
  scoreBar:        { width: '100%' },

  sectionHeader:  { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8, marginTop: 8 },
  sectionTitle:   { flex: 1, fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  sectionDesc:    { fontSize: 12, color: '#6C6C80', marginBottom: 12 },
  countBadge:     { backgroundColor: '#FFEBEE', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  countBadgeText: { fontSize: 13, fontWeight: '600', color: '#E53935' },
  saveAllBtn:     { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 6, backgroundColor: '#F0EDFF', borderRadius: 16 },
  saveAllText:    { fontSize: 12, fontWeight: '600', color: '#6C3BFF' },

  mistakesList:     { gap: 12, marginBottom: 20 },
  mistakeCard:      { borderColor: '#FFE0E0' },
  mistakeHeader:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  mistakeTypeBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  mistakeTypeText:  { fontSize: 11, fontWeight: '600' },
  mistakeContent:   { gap: 8 },
  mistakeRow:       { flexDirection: 'row', alignItems: 'flex-start' },
  mistakeLabelX:    { fontSize: 14, color: '#E53935', fontWeight: '700', marginRight: 8, width: 20 },
  mistakeLabelOk:   { fontSize: 14, color: '#4CAF50', fontWeight: '700', marginRight: 8, width: 20 },
  mistakeOriginal:  { flex: 1, fontSize: 14, color: '#E53935', textDecorationLine: 'line-through' },
  mistakeCorrection:{ flex: 1, fontSize: 14, color: '#4CAF50', fontWeight: '600' },
  explanationBox:   { backgroundColor: '#F5F5FA', borderRadius: 8, padding: 12, marginTop: 12 },
  explanationText:  { fontSize: 13, color: '#1A1A2E', lineHeight: 20 },
  noMistakeText:    { marginTop: 8, fontSize: 15, fontWeight: '600', color: '#1A1A2E' },

  vocabList:           { gap: 12, marginBottom: 20 },
  vocabCard:           { borderWidth: 1, borderColor: 'transparent' },
  vocabCardSaved:      { borderColor: '#6C3BFF', backgroundColor: '#FAFAFF' },
  vocabHeader:         { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  vocabWordRow:        { flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 },
  vocabWord:           { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  kindBadge:           { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8 },
  kindBadgeWord:       { backgroundColor: '#E3F2FD' },
  kindBadgePhrase:     { backgroundColor: '#F3E5F5' },
  kindBadgeText:       { fontSize: 10, fontWeight: '600' },
  kindBadgeTextWord:   { color: '#1565C0' },
  kindBadgeTextPhrase: { color: '#6A1B9A' },
  bookmarkBtn:         { width: 36, height: 36, borderRadius: 18, backgroundColor: '#F0EDFF', alignItems: 'center', justifyContent: 'center' },
  bookmarkBtnSaved:    { backgroundColor: '#6C3BFF' },
  vocabMeaning:        { fontSize: 13, color: '#6C6C80', marginBottom: 8 },
  vocabExample:        { backgroundColor: '#F5F5FA', borderRadius: 8, padding: 10 },
  vocabExampleLabel:   { fontSize: 11, color: '#6C3BFF', fontWeight: '600', marginBottom: 2 },
  vocabExampleText:    { fontSize: 13, color: '#1A1A2E', lineHeight: 18 },
  savedToast:          { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 8 },
  savedToastText:      { fontSize: 11, color: '#4CAF50', fontWeight: '600' },

  feedbackCard: { marginBottom: 20 },
  feedbackRow:  { flexDirection: 'row', alignItems: 'flex-start', gap: 10 },
  feedbackText: { flex: 1, fontSize: 14, color: '#1A1A2E', lineHeight: 22 },

  savedBanner:     { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#F0EDFF', paddingVertical: 12, paddingHorizontal: 16, borderRadius: 12, marginBottom: 20 },
  savedBannerText: { flex: 1, fontSize: 13, fontWeight: '600', color: '#6C3BFF' },

  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
});