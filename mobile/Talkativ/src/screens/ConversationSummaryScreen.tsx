import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, TouchableOpacity, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  BookOpen, AlertTriangle, CheckCircle, Bookmark,
  TrendingUp, MessageCircle, Sparkles, ChevronDown, ChevronUp,
} from 'lucide-react-native';
import { Header, Card, Button, ProgressBar, Tag, Icon } from '../components';

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
}

interface SummaryData {
  scores:            { speechAccuracy: number; vocabulary: number; naturalness: number; };
  mistakes:          MistakeItem[];
  vocabularyToLearn: VocabularyItem[];
  phrasesToLearn:    VocabularyItem[];
  improvements:      string[];
  suggestions:       string[];
}

const mockSummary: SummaryData = {
  scores:            { speechAccuracy: 0.80, vocabulary: 0.72, naturalness: 0.78 },
  mistakes:          [],
  vocabularyToLearn: [
    { word: '감사합니다', meaning: 'Thank you (formal)', example: '도와주셔서 감사합니다.' },
    { word: '실례합니다', meaning: 'Excuse me',          example: '실례합니다, 질문이 있어요.' },
  ],
  phrasesToLearn:    [
    { word: '어떻게 지내세요?', meaning: 'How are you?',     example: '오랜만이에요! 어떻게 지내세요?' },
    { word: '다음에 또 봬요',   meaning: 'See you next time', example: '오늘 즐거웠어요. 다음에 또 봬요!' },
  ],
  improvements: ['대화를 잘 진행하셨습니다!'],
  suggestions:  [],
};

const toMistakeType = (t: string): MistakeItem['type'] => {
  if (t === 'speech_level' || t === 'honorific') return 'politeness';
  if (t === 'grammar'      || t === 'spelling')  return 'grammar';
  if (t === 'vocabulary'   || t === 'word_choice') return 'vocabulary';
  return 'naturalness';
};

export default function ConversationSummaryScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();
  const {
    avatar,
    duration,
    conversationHistory,
    sessionReport,
    sessionCorrections,  // ← ChatScreen에서 전달된 교정 데이터
    avgScore,            // ← ChatScreen에서 계산된 평균 점수
  } = route.params || {};

  const [loading,         setLoading]         = useState(true);
  const [summary,         setSummary]         = useState<SummaryData>(mockSummary);
  const [savedItems,      setSavedItems]      = useState<Set<string>>(new Set());
  const [expandedMistake, setExpandedMistake] = useState<number | null>(null);

  useEffect(() => {
    buildSummary();
  }, []);

  const buildSummary = async () => {
    try {
      setLoading(true);

      // ── 우선순위 1: ChatScreen에서 수집된 실시간 교정 데이터 사용 ──
      if (sessionCorrections && sessionCorrections.length > 0) {
        const allCorrections = sessionCorrections.flatMap((s: any) => s.corrections || []);
        const speechScore    = avgScore || 80;

        // error/warning corrections만 mistakes로 표시
        const mistakes = allCorrections
          .filter((c: any) => c.severity === 'error' || c.severity === 'warning')
          .slice(0, 6)
          .map((c: any) => ({
            original:    c.original    || '',
            correction:  c.corrected   || '',
            explanation: c.explanation || '',
            type:        toMistakeType(c.type || ''),
          }));

        // 격려 메시지 수집
        const encouragements = sessionCorrections
          .filter((s: any) => s.encouragement && !s.has_errors)
          .map((s: any) => s.encouragement)
          .slice(0, 2);

        // 팁 수집
        const tips = allCorrections
          .filter((c: any) => c.tip)
          .map((c: any) => c.tip)
          .slice(0, 3);

        setSummary({
          scores: {
            speechAccuracy: speechScore / 100,
            vocabulary:     (sessionReport?.scores?.vocabulary  || 75) / 100,
            naturalness:    (sessionReport?.scores?.naturalness || 78) / 100,
          },
          mistakes,
          vocabularyToLearn: (sessionReport?.vocabulary_to_learn || []).map((v: any) => ({
            word:    v.word    || '',
            meaning: v.meaning || '',
            example: v.example || '',
          })),
          phrasesToLearn: (sessionReport?.phrases_to_learn || []).map((p: any) => ({
            word:    p.phrase || p.word || '',
            meaning: p.meaning || '',
            example: p.example || '',
          })),
          improvements: encouragements.length > 0
            ? encouragements
            : [sessionReport?.overall_feedback || '대화를 잘 진행하셨습니다!'],
          suggestions: tips,
        });
        return;
      }

      // ── 우선순위 2: AI 서버 분석 호출 ─────────────────────────────
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
          conversation_history: (conversationHistory || []).map((m: any) => ({
            role:    m.role || (m.sender === 'ai' ? 'assistant' : 'user'),
            content: m.content || m.text || '',
          })),
        }),
      });

      if (!res.ok) throw new Error(`Analyze error: ${res.status}`);
      const data = await res.json();

      setSummary({
        scores: {
          speechAccuracy: (data.scores?.speech_accuracy || 80) / 100,
          vocabulary:     (data.scores?.vocabulary       || 75) / 100,
          naturalness:    (data.scores?.naturalness      || 78) / 100,
        },
        mistakes: (data.mistakes || []).slice(0, 5).map((m: any) => ({
          original:    m.original    || '',
          correction:  m.corrected   || '',
          explanation: m.explanation || '',
          type:        toMistakeType(m.type || ''),
        })),
        vocabularyToLearn: (data.vocabulary_to_learn || []).map((v: any) => ({
          word:    v.word    || '',
          meaning: v.meaning || '',
          example: v.example || '',
        })),
        phrasesToLearn: (data.phrases_to_learn || []).map((p: any) => ({
          word:    p.phrase || p.word || '',
          meaning: p.meaning || '',
          example: p.example || '',
        })),
        improvements: data.overall_feedback
          ? [data.overall_feedback]
          : ['대화를 잘 진행하셨습니다!'],
        suggestions: (data.mistakes || [])
          .slice(0, 2)
          .map((m: any) => m.explanation || '')
          .filter(Boolean),
      });

    } catch (error) {
      console.error('Summary error — using mock:', error);
      setSummary(mockSummary);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveItem = (item: string) => {
    setSavedItems(prev => {
      const next = new Set(prev);
      next.has(item) ? next.delete(item) : next.add(item);
      return next;
    });
  };

  const handleSaveAll = () => {
    setSavedItems(new Set([
      ...summary.vocabularyToLearn.map(v => v.word),
      ...summary.phrasesToLearn.map(p => p.word),
    ]));
  };

  const handleContinue = () => {
    navigation.navigate('Analytics', {
      avatar,
      duration,
      scores:     summary.scores,
      savedItems: Array.from(savedItems),
    });
  };

  const getMistakeTypeColor = (type: string) => {
    switch (type) {
      case 'grammar':     return '#E53935';
      case 'vocabulary':  return '#F4A261';
      case 'politeness':  return '#6C3BFF';
      case 'naturalness': return '#4CAF50';
      default:            return '#6C6C80';
    }
  };

  const getMistakeTypeLabel = (type: string) => {
    switch (type) {
      case 'grammar':     return '문법';
      case 'vocabulary':  return '어휘';
      case 'politeness':  return '존댓말';
      case 'naturalness': return '자연스러움';
      default:            return type;
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <Header title="대화 분석 중..." showBack={false} />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6C3BFF" />
          <Text style={styles.loadingText}>
            {sessionCorrections?.length > 0
              ? '대화 결과를 정리하고 있어요...'
              : 'AI가 대화를 분석하고 있어요...'}
          </Text>
          <Text style={styles.loadingSubtext}>잠시만 기다려주세요</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="대화 요약" showBack={false} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* ── 점수 카드 ── */}
        <Card variant="elevated" style={styles.scoreCard}>
          <View style={styles.scoreHeader}>
            <View style={[styles.avatarIcon, { backgroundColor: avatar?.avatarBg || avatar?.avatar_bg || '#FFB6C1' }]}>
              <Icon name={avatar?.icon || 'user'} size={24} color="#FFFFFF" />
            </View>
            <View style={styles.scoreHeaderText}>
              <Text style={styles.scoreTitle}>{avatar?.name_ko || '아바타'}와의 대화</Text>
              <Text style={styles.scoreSubtitle}>
                {sessionCorrections?.length > 0
                  ? `${sessionCorrections.length}개 메시지 분석됨`
                  : '대화 분석 결과'}
              </Text>
            </View>
          </View>

          <View style={styles.scoresGrid}>
            <View style={styles.scoreItem}>
              <Text style={styles.scoreValue}>{Math.round(summary.scores.speechAccuracy * 100)}%</Text>
              <Text style={styles.scoreLabel}>말투 정확도</Text>
              <ProgressBar progress={summary.scores.speechAccuracy} color="#6C3BFF" style={styles.scoreBar} />
            </View>
            <View style={styles.scoreItem}>
              <Text style={styles.scoreValue}>{Math.round(summary.scores.vocabulary * 100)}%</Text>
              <Text style={styles.scoreLabel}>어휘력</Text>
              <ProgressBar progress={summary.scores.vocabulary} color="#4CAF50" style={styles.scoreBar} />
            </View>
            <View style={styles.scoreItem}>
              <Text style={styles.scoreValue}>{Math.round(summary.scores.naturalness * 100)}%</Text>
              <Text style={styles.scoreLabel}>자연스러움</Text>
              <ProgressBar progress={summary.scores.naturalness} color="#F4A261" style={styles.scoreBar} />
            </View>
          </View>
        </Card>

        {/* ── 틀린 부분 ── */}
        <View style={styles.sectionHeader}>
          <AlertTriangle size={20} color="#E53935" />
          <Text style={styles.sectionTitle}>틀린 부분</Text>
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{summary.mistakes.length}</Text>
          </View>
        </View>

        <View style={styles.mistakesList}>
          {summary.mistakes.map((mistake, index) => (
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
                {expandedMistake === index
                  ? <ChevronUp size={20} color="#6C6C80" />
                  : <ChevronDown size={20} color="#6C6C80" />}
              </TouchableOpacity>

              <View style={styles.mistakeContent}>
                <View style={styles.mistakeRow}>
                  <Text style={styles.mistakeLabel}>✗</Text>
                  <Text style={styles.mistakeOriginal}>{mistake.original}</Text>
                </View>
                <View style={styles.mistakeRow}>
                  <Text style={styles.correctionLabel}>✓</Text>
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

          {summary.mistakes.length === 0 && (
            <Card variant="elevated">
              <View style={{ alignItems: 'center', padding: 16 }}>
                <CheckCircle size={32} color="#4CAF50" />
                <Text style={{ marginTop: 8, fontSize: 15, fontWeight: '600', color: '#1A1A2E' }}>
                  실수가 없어요! 완벽해요 🎉
                </Text>
              </View>
            </Card>
          )}
        </View>

        {/* ── 배울 단어 ── */}
        {summary.vocabularyToLearn.length > 0 && (
          <>
            <View style={styles.sectionHeader}>
              <BookOpen size={20} color="#6C3BFF" />
              <Text style={styles.sectionTitle}>배울 단어</Text>
              <TouchableOpacity style={styles.saveAllBtn} onPress={handleSaveAll}>
                <Bookmark size={16} color="#6C3BFF" />
                <Text style={styles.saveAllText}>모두 저장</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.vocabList}>
              {summary.vocabularyToLearn.map((item, index) => (
                <Card key={index} variant="elevated" style={styles.vocabCard}>
                  <View style={styles.vocabHeader}>
                    <Text style={styles.vocabWord}>{item.word}</Text>
                    <TouchableOpacity onPress={() => handleSaveItem(item.word)}>
                      <Bookmark size={20} color={savedItems.has(item.word) ? '#6C3BFF' : '#B0B0C5'} fill={savedItems.has(item.word) ? '#6C3BFF' : 'transparent'} />
                    </TouchableOpacity>
                  </View>
                  <Text style={styles.vocabMeaning}>{item.meaning}</Text>
                  <View style={styles.vocabExample}>
                    <Text style={styles.vocabExampleLabel}>예문:</Text>
                    <Text style={styles.vocabExampleText}>{item.example}</Text>
                  </View>
                </Card>
              ))}
            </View>
          </>
        )}

        {/* ── 배울 표현 ── */}
        {summary.phrasesToLearn.length > 0 && (
          <>
            <View style={styles.sectionHeader}>
              <MessageCircle size={20} color="#4CAF50" />
              <Text style={styles.sectionTitle}>배울 표현</Text>
            </View>
            <View style={styles.vocabList}>
              {summary.phrasesToLearn.map((item, index) => (
                <Card key={index} variant="elevated" style={styles.vocabCard}>
                  <View style={styles.vocabHeader}>
                    <Text style={styles.vocabWord}>{item.word}</Text>
                    <TouchableOpacity onPress={() => handleSaveItem(item.word)}>
                      <Bookmark size={20} color={savedItems.has(item.word) ? '#6C3BFF' : '#B0B0C5'} fill={savedItems.has(item.word) ? '#6C3BFF' : 'transparent'} />
                    </TouchableOpacity>
                  </View>
                  <Text style={styles.vocabMeaning}>{item.meaning}</Text>
                  <View style={styles.vocabExample}>
                    <Text style={styles.vocabExampleLabel}>예문:</Text>
                    <Text style={styles.vocabExampleText}>{item.example}</Text>
                  </View>
                </Card>
              ))}
            </View>
          </>
        )}

        {/* ── 잘한 점 ── */}
        <View style={styles.sectionHeader}>
          <CheckCircle size={20} color="#4CAF50" />
          <Text style={styles.sectionTitle}>잘한 점</Text>
        </View>
        <Card variant="elevated" style={styles.improvementsCard}>
          {summary.improvements.map((item, index) => (
            <View key={index} style={styles.improvementItem}>
              <Sparkles size={16} color="#4CAF50" />
              <Text style={styles.improvementText}>{item}</Text>
            </View>
          ))}
        </Card>

        {/* ── 다음에 연습할 것 ── */}
        {summary.suggestions.length > 0 && (
          <>
            <View style={styles.sectionHeader}>
              <TrendingUp size={20} color="#F4A261" />
              <Text style={styles.sectionTitle}>다음에 연습할 것</Text>
            </View>
            <Card variant="elevated" style={styles.suggestionsCard}>
              {summary.suggestions.map((item, index) => (
                <View key={index} style={styles.suggestionItem}>
                  <View style={styles.suggestionBullet} />
                  <Text style={styles.suggestionText}>{item}</Text>
                </View>
              ))}
            </Card>
          </>
        )}

        {/* ── 저장된 항목 ── */}
        {savedItems.size > 0 && (
          <View style={styles.savedBanner}>
            <Bookmark size={18} color="#6C3BFF" fill="#6C3BFF" />
            <Text style={styles.savedBannerText}>{savedItems.size}개 항목이 저장되었어요</Text>
          </View>
        )}

      </ScrollView>

      <View style={styles.footer}>
        <Button
          title={`저장하고 계속하기 (${savedItems.size})`}
          onPress={handleContinue}
          showArrow
        />
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

  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12, marginTop: 8 },
  sectionTitle:  { flex: 1, fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  countBadge:    { backgroundColor: '#FFEBEE', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  countText:     { fontSize: 13, fontWeight: '600', color: '#E53935' },
  saveAllBtn:    { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 6, backgroundColor: '#F0EDFF', borderRadius: 16 },
  saveAllText:   { fontSize: 12, fontWeight: '600', color: '#6C3BFF' },

  mistakesList:     { gap: 12, marginBottom: 20 },
  mistakeCard:      { borderColor: '#FFE0E0' },
  mistakeHeader:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  mistakeTypeBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  mistakeTypeText:  { fontSize: 11, fontWeight: '600' },
  mistakeContent:   { gap: 8 },
  mistakeRow:       { flexDirection: 'row', alignItems: 'flex-start' },
  mistakeLabel:     { fontSize: 14, color: '#E53935', fontWeight: '700', marginRight: 8, width: 20 },
  correctionLabel:  { fontSize: 14, color: '#4CAF50', fontWeight: '700', marginRight: 8, width: 20 },
  mistakeOriginal:  { flex: 1, fontSize: 14, color: '#E53935', textDecorationLine: 'line-through' },
  mistakeCorrection:{ flex: 1, fontSize: 14, color: '#4CAF50', fontWeight: '600' },
  explanationBox:   { backgroundColor: '#F5F5FA', borderRadius: 8, padding: 12, marginTop: 12 },
  explanationText:  { fontSize: 13, color: '#1A1A2E', lineHeight: 20 },

  vocabList:         { gap: 12, marginBottom: 20 },
  vocabCard:         {},
  vocabHeader:       { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 },
  vocabWord:         { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  vocabMeaning:      { fontSize: 13, color: '#6C6C80', marginBottom: 8 },
  vocabExample:      { backgroundColor: '#F5F5FA', borderRadius: 8, padding: 10 },
  vocabExampleLabel: { fontSize: 11, color: '#6C3BFF', fontWeight: '600', marginBottom: 2 },
  vocabExampleText:  { fontSize: 13, color: '#1A1A2E' },

  improvementsCard: { marginBottom: 20 },
  improvementItem:  { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 10 },
  improvementText:  { flex: 1, fontSize: 14, color: '#1A1A2E' },

  suggestionsCard: { marginBottom: 20 },
  suggestionItem:  { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 10 },
  suggestionBullet:{ width: 6, height: 6, borderRadius: 3, backgroundColor: '#F4A261', marginTop: 6, marginRight: 10 },
  suggestionText:  { flex: 1, fontSize: 14, color: '#1A1A2E', lineHeight: 20 },

  savedBanner:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: '#F0EDFF', paddingVertical: 12, borderRadius: 12, marginBottom: 20 },
  savedBannerText: { fontSize: 14, fontWeight: '600', color: '#6C3BFF' },

  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
});