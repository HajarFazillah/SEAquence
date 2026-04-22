import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput,
  KeyboardAvoidingView, Platform, ActivityIndicator, Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  ChevronLeft, X, Send, Smile, Meh, Frown, Angry, Heart,
  CheckCircle, AlertCircle, Lightbulb,
} from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SpeechLevelBadge, Icon } from '../components';

const AI_SERVER = 'http://10.0.2.2:8000';

type HistoryRole = 'user' | 'assistant';
interface HistoryItem { role: HistoryRole; content: string; }

interface Correction {
  original:    string;
  corrected:   string;
  explanation: string;
  severity:    'error' | 'warning' | 'info';
  tip?:        string;
  type?:       string;
}

interface NaturalAlternative {
  expression:  string;
  explanation: string;
}

interface SpeechAnalysis {
  detected_speech_level: string;
  detected_speech_level_code?: string;
  detected_speech_confidence?: number;
  speech_level_correct:  boolean;
  expected_speech_level: string;
  expected_speech_level_code?: string;
  input_kind?: string;
  verdict?: string;
  has_errors:            boolean;
  accuracy_score:        number;
  corrections:           Correction[];
  natural_alternatives:  NaturalAlternative[];
  encouragement?:        string;
  summary?:              string;
}

interface Message {
  id:       string;
  text:     string;
  sender:   'user' | 'ai';
  feedback?: SpeechAnalysis;
}

const getMoodConfig = (mood: number) => {
  if (mood >= 80) return { icon: Heart,  color: '#E91E63', label: '아주 좋아요!' };
  if (mood >= 60) return { icon: Smile,  color: '#4CAF50', label: '좋아요'       };
  if (mood >= 40) return { icon: Meh,    color: '#F4A261', label: '그저 그래요'  };
  if (mood >= 20) return { icon: Frown,  color: '#FF9800', label: '조금 힘들어요' };
  return           { icon: Angry,  color: '#E53935', label: '화나요!'       };
};

const buildHistoryFromMessages = (messages: Message[]): HistoryItem[] =>
  messages
    .map(m => ({ role: (m.sender === 'user' ? 'user' : 'assistant') as HistoryRole, content: m.text }))
    .filter(m => m.content.trim().length > 0);

const LEVEL_LABELS: Record<string, string> = {
  formal: '합쇼체',
  polite: '해요체',
  informal: '반말',
};

const normalizeSpeechLevelCode = (level: any, explicitCode?: string) => {
  if (explicitCode) return explicitCode;
  if (typeof level === 'object' && level?.code) return String(level.code);
  if (typeof level === 'string') {
    const normalized = level.trim().toLowerCase();
    return LEVEL_LABELS[normalized] ? normalized : '';
  }
  return '';
};

const normalizeSpeechLevelLabel = (level: any, explicitLabel?: string) => {
  if (explicitLabel) return explicitLabel;
  if (typeof level === 'object') {
    const label = level?.label_ko || level?.label || level?.name_ko;
    if (label) return String(label);
    if (level?.code) return LEVEL_LABELS[String(level.code).toLowerCase()] || String(level.code);
  }
  if (typeof level === 'string') {
    const normalized = level.trim().toLowerCase();
    return LEVEL_LABELS[normalized] || level;
  }
  return '';
};

const normalizeConfidence = (level: any, explicitConfidence?: number) => {
  if (typeof explicitConfidence === 'number') return explicitConfidence;
  if (typeof level === 'object' && typeof level?.confidence === 'number') return level.confidence;
  return undefined;
};

const normalizeScore = (score: any) => {
  const parsed = Number(score);
  if (!Number.isFinite(parsed)) return 80;
  return Math.max(0, Math.min(100, Math.round(parsed)));
};

const sendMessageToAI = async (
  text:      string,
  history:   HistoryItem[],
  avatar:    any,
  situation: any,
  user_id:   string,
) => {
  const res = await fetch(`${AI_SERVER}/api/v1/chat`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_message:         text,
      conversation_history: history,
      avatar: {
        id:                 avatar?.id                 || 'test',
        name_ko:            avatar?.name_ko            || '아바타',
        role:               avatar?.role               || 'friend',
        personality_traits: avatar?.personality_traits || [],
        interests:          avatar?.interests          || [],
        dislikes:           avatar?.dislikes           || [],
      },
      situation: situation?.name_ko || situation?.title || null,
      user_id,
    }),
  });

  if (!res.ok) throw new Error(`AI server error: ${res.status}`);
  const data = await res.json();

  const correction = data.correction;
  const detectedRaw = correction?.detected_speech_level || correction?.detected_level;
  const expectedRaw = correction?.expected_speech_level || correction?.expected_level;
  const speech_analysis: SpeechAnalysis | null = correction ? {
    detected_speech_level: normalizeSpeechLevelLabel(
      detectedRaw,
      correction.detected_speech_level_label || correction.detected_level_label,
    ),
    detected_speech_level_code: normalizeSpeechLevelCode(
      detectedRaw,
      correction.detected_speech_level_code || correction.detected_level_code,
    ),
    detected_speech_confidence: normalizeConfidence(
      detectedRaw,
      correction.detected_speech_level_confidence || correction.detected_confidence,
    ),
    speech_level_correct: correction.speech_level_correct ?? true,
    expected_speech_level: normalizeSpeechLevelLabel(
      expectedRaw,
      correction.expected_speech_level_label || correction.expected_level_label,
    ),
    expected_speech_level_code: normalizeSpeechLevelCode(
      expectedRaw,
      correction.expected_speech_level_code || correction.expected_level_code,
    ),
    input_kind: correction.input_kind || correction.inputKind,
    verdict: correction.verdict,
    has_errors: correction.has_errors ?? false,
    accuracy_score: normalizeScore(correction.accuracy_score),
    corrections: correction.corrections || [],
    natural_alternatives: correction.natural_alternatives || [],
    encouragement: correction.encouragement || '',
    summary: correction.summary || correction.overall_feedback || '',
  } : null;

  console.log('[Chat] natural_alternatives:', speech_analysis?.natural_alternatives?.length, speech_analysis?.natural_alternatives);

  return {
    message:        data.message,
    speech_analysis,
    mood_change:    data.mood_change    || 0,
    current_mood:   data.current_mood   || 70,
    mood_emoji:     data.mood_emoji     || '😊',
    correct_streak: data.correct_streak || 0,
  };
};

const analyzeSessionWithAI = async (avatar: any, history: HistoryItem[]) => {
  const res = await fetch(`${AI_SERVER}/api/v1/chat/analyze`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ avatar, conversation_history: history }),
  });
  if (!res.ok) throw new Error(`Analyze error: ${res.status}`);
  return res.json();
};

const severityColor = (s: string) =>
  s === 'error' ? '#E53935' : s === 'warning' ? '#F4A261' : '#6C3BFF';

const feedbackTitle = (fb: SpeechAnalysis) => {
  const detected = normalizeSpeechLevelLabel(fb.detected_speech_level);
  const expected = normalizeSpeechLevelLabel(fb.expected_speech_level);

  if (fb.verdict === 'practice_expression') return `${detected || expected || '말투'} 연습 표현`;
  if (fb.verdict === 'fragment') return '표현 조각';
  if (fb.verdict === 'wrong_speech_level') return detected ? `${detected} 사용됨` : '말투 수정 필요';
  if (fb.verdict === 'needs_revision') return '수정이 필요한 표현';
  if (fb.verdict === 'unclear') return '말투를 판단하기 어려워요';

  if (fb.input_kind === 'meta_practice') return `${detected || expected || '말투'} 연습 표현`;
  if (fb.input_kind === 'fragment') return '표현 조각';
  if (fb.input_kind === 'non_korean') return '한국어 표현 아님';

  if (!detected) return fb.expected_speech_level || '말투 분석';
  if (detected.includes('연습 표현') || detected.includes('표현 분석')) {
    return detected;
  }
  if (fb.detected_speech_confidence && fb.detected_speech_confidence < 0.75) {
    return `${detected}에 가까워요`;
  }
  return `${detected} 감지`;
};

export default function ChatScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();

  const avatar           = route.params?.avatar;
  const situation        = route.params?.situation;
  const recommendedLevel = route.params?.recommendedLevel || 'polite';
  const profileName      = route.params?.name     || avatar?.name_ko || '아바타';
  const profileBg        = route.params?.avatarBg || avatar?.avatar_bg || '#FFB6C1';

  const flatListRef = useRef<FlatList>(null);

  const [messages,         setMessages]         = useState<Message[]>([{
    id: '0',
    text: avatar?.greeting || `안녕하세요! ${situation?.name_ko || '대화'}를 시작해볼까요?`,
    sender: 'ai',
  }]);
  const [input,            setInput]            = useState('');
  const [loading,          setLoading]          = useState(false);
  const [avatarMood,       setAvatarMood]       = useState(70);
  const [startTime]        = useState(Date.now());
  const [userId,           setUserId]           = useState('test-user-1');
  const [correctStreak,    setCorrectStreak]    = useState(0);
  const [expandedFeedback, setExpandedFeedback] = useState<Record<string, boolean>>({});

  const moodAnim    = useRef(new Animated.Value(70)).current;

  useEffect(() => {
    AsyncStorage.getItem('user_id').then(id => { if (id) setUserId(id); });
  }, []);

  useEffect(() => {
    if (messages.length > 0)
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
  }, [messages]);

  useEffect(() => {
    Animated.spring(moodAnim, { toValue: avatarMood, useNativeDriver: false, friction: 8 }).start();
  }, [avatarMood, moodAnim]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const text    = input.trim();
    const userMsg: Message = { id: Date.now().toString(), text, sender: 'user' };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const history: HistoryItem[] = [
        ...buildHistoryFromMessages(messages),
        { role: 'user', content: text },
      ];

      const data = await sendMessageToAI(text, history, avatar, situation, userId);
      const aiMsg: Message = { id: (Date.now() + 1).toString(), text: data.message, sender: 'ai' };

      setAvatarMood(data.current_mood);
      setCorrectStreak(data.correct_streak);

      setMessages(prev => {
        const updated = prev.map(m =>
          m.id === userMsg.id ? { ...m, feedback: data.speech_analysis ?? undefined } : m
        );
        return [...updated, aiMsg];
      });

      // 피드백 있으면 항상 펼침
      if (data.speech_analysis) {
        setExpandedFeedback(prev => ({ ...prev, [userMsg.id]: true }));
      }

    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: '네, 그렇군요! 더 이야기해주세요.',
        sender: 'ai',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleEndChat = async () => {
    const duration    = Math.floor((Date.now() - startTime) / 1000);
    const durationStr = `${String(Math.floor(duration/60)).padStart(2,'0')}:${String(duration%60).padStart(2,'0')}`;
    const history     = buildHistoryFromMessages(messages);

    const sessionCorrections = messages
      .filter(m => m.sender === 'user' && m.feedback)
      .map(m => ({
        message:        m.text,
        accuracy_score: m.feedback!.accuracy_score,
        has_errors:     m.feedback!.has_errors,
        corrections:    m.feedback!.corrections,
        detected_level: m.feedback!.detected_speech_level,
        encouragement:  m.feedback!.encouragement,
      }));

    const avgScore = sessionCorrections.length > 0
      ? Math.round(sessionCorrections.reduce((s, c) => s + c.accuracy_score, 0) / sessionCorrections.length)
      : 100;

    let sessionReport = null;
    try { sessionReport = await analyzeSessionWithAI(avatar, history); } catch {}

    navigation.navigate('ConversationSummary', {
      avatar, duration: durationStr, situation,
      conversationHistory: history, finalMood: avatarMood,
      sessionReport, sessionCorrections, avgScore,
    });
  };

  // ── 피드백 카드 ───────────────────────────────────────────────
  const renderFeedbackCard = (item: Message) => {
    if (!item.feedback) return null;

    const fb           = item.feedback;
    const expanded     = expandedFeedback[item.id] ?? true;
    const hasError     = fb.has_errors;
    const alternatives = fb.natural_alternatives || [];
    const hasAlts      = alternatives.length > 0;

    return (
      <TouchableOpacity
        style={[styles.feedbackCard, hasError ? styles.feedbackCardError : styles.feedbackCardOk]}
        onPress={() => setExpandedFeedback(prev => ({ ...prev, [item.id]: !expanded }))}
        activeOpacity={0.8}
      >
        {/* ── 요약 행 ── */}
        <View style={styles.feedbackSummaryRow}>
          {hasError
            ? <AlertCircle size={14} color="#E53935" />
            : <CheckCircle size={14} color="#4CAF50" />}
          <Text style={[styles.feedbackSummaryText, { color: hasError ? '#E53935' : '#4CAF50' }]}>
            {feedbackTitle(fb)}
          </Text>
          <Text style={styles.feedbackScore}>{fb.accuracy_score}점</Text>
          <Text style={styles.feedbackExpand}>{expanded ? '▲' : '▼'}</Text>
        </View>

        {expanded && (
          <View style={styles.feedbackDetail}>
            {fb.summary ? (
              <Text style={styles.feedbackSummaryNote}>{fb.summary}</Text>
            ) : null}

            {/* ── 오류가 없을 때: 이렇게도 말할 수 있어요 우선 표시 ── */}
            {!hasError && hasAlts && (
              <View style={styles.alternativesSection}>
                <View style={styles.alternativesHeader}>
                  <Lightbulb size={14} color="#6C3BFF" />
                  <Text style={styles.alternativesTitle}>이렇게도 말할 수 있어요</Text>
                </View>
                {alternatives.map((alt, i) => (
                  <View key={i} style={[
                    styles.alternativeItem,
                    i < alternatives.length - 1 && styles.alternativeItemBorder,
                  ]}>
                    <Text style={styles.alternativeExpression}>"{alt.expression}"</Text>
                    {alt.explanation ? (
                      <Text style={styles.alternativeExplain}>{alt.explanation}</Text>
                    ) : null}
                  </View>
                ))}
              </View>
            )}

            {/* 격려 메시지 — 대안 없을 때만 표시 */}
            {(!hasAlts || hasError) && fb.encouragement ? (
              <Text style={styles.feedbackEncouragement}>{fb.encouragement}</Text>
            ) : null}

            {/* ── 오류 있을 때: 교정 목록 ── */}
            {hasError && fb.corrections.length > 0 && (
              <View style={styles.correctionList}>
                {fb.corrections.map((c, i) => (
                  <View key={i} style={[styles.correctionItem, { borderLeftColor: severityColor(c.severity) }]}>
                    <View style={styles.correctionRow}>
                      <Text style={styles.correctionOriginal}>✕ {c.original}</Text>
                      <Text style={styles.correctionArrow}>→</Text>
                      <Text style={styles.correctionFixed}>{c.corrected}</Text>
                    </View>
                    <Text style={styles.correctionExplain}>{c.explanation}</Text>
                    {c.tip ? <Text style={styles.correctionTip}>💡 {c.tip}</Text> : null}
                  </View>
                ))}
              </View>
            )}

            {/* 오류 있을 때도 대안 표현 */}
            {hasError && hasAlts && (
              <View style={[styles.alternativesSection, { marginTop: 10 }]}>
                <View style={styles.alternativesHeader}>
                  <Lightbulb size={14} color="#6C3BFF" />
                  <Text style={styles.alternativesTitle}>이렇게도 말할 수 있어요</Text>
                </View>
                {alternatives.map((alt, i) => (
                  <View key={i} style={[
                    styles.alternativeItem,
                    i < alternatives.length - 1 && styles.alternativeItemBorder,
                  ]}>
                    <Text style={styles.alternativeExpression}>"{alt.expression}"</Text>
                    {alt.explanation ? (
                      <Text style={styles.alternativeExplain}>{alt.explanation}</Text>
                    ) : null}
                  </View>
                ))}
              </View>
            )}

          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={styles.messageWrapper}>
      <View style={[styles.bubbleRow, item.sender === 'user' ? styles.bubbleRowUser : styles.bubbleRowAi]}>
        {item.sender === 'ai' && (
          <View style={[styles.bubbleAvatar, { backgroundColor: profileBg }]}>
            <Icon name={avatar?.icon || 'user'} size={16} color="#FFFFFF" />
          </View>
        )}
        <View style={[
          styles.bubble,
          item.sender === 'user' ? styles.bubbleUser : styles.bubbleAi,
          item.feedback?.has_errors && styles.bubbleWarning,
        ]}>
          <Text style={[styles.bubbleText, item.sender === 'user' && styles.bubbleTextUser]}>
            {item.text}
          </Text>
        </View>
      </View>
      {item.sender === 'user' && item.feedback && renderFeedbackCard(item)}
    </View>
  );

  const moodConfig = getMoodConfig(avatarMood);
  const MoodIcon   = moodConfig.icon;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <ChevronLeft size={24} color="#1A1A2E" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <View style={[styles.headerAvatar, { backgroundColor: profileBg }]}>
            <Icon name={avatar?.icon || 'user'} size={16} color="#FFFFFF" />
          </View>
          <View>
            <Text style={styles.headerName}>{profileName}</Text>
            <Text style={styles.headerSituation}>{situation?.name_ko || '대화'}</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.headerBtn} onPress={handleEndChat}>
          <X size={24} color="#E53935" />
        </TouchableOpacity>
      </View>

      <View style={styles.moodBarContainer}>
        <MoodIcon size={18} color={moodConfig.color} />
        <Text style={[styles.moodLabel, { color: moodConfig.color }]}>{moodConfig.label}</Text>
        <View style={styles.moodBarTrack}>
          <Animated.View style={[styles.moodBarFill, {
            backgroundColor: moodConfig.color,
            width: moodAnim.interpolate({ inputRange: [0,100], outputRange: ['0%','100%'] }),
          }]} />
        </View>
        <Text style={styles.moodPercent}>{avatarMood}%</Text>
        {correctStreak >= 3 && (
          <View style={styles.streakBadge}>
            <Text style={styles.streakText}>🔥 {correctStreak}연속</Text>
          </View>
        )}
      </View>

      <View style={styles.levelBanner}>
        <Text style={styles.levelLabel}>추천 말투:</Text>
        <SpeechLevelBadge level={recommendedLevel} size="small" />
      </View>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.messageList}
          renderItem={renderMessage}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />

        {loading && (
          <View style={styles.loadingRow}>
            <View style={[styles.bubbleAvatar, { backgroundColor: profileBg }]}>
              <Icon name={avatar?.icon || 'user'} size={16} color="#FFFFFF" />
            </View>
            <View style={styles.loadingBubble}>
              <ActivityIndicator size="small" color="#6C3BFF" />
            </View>
          </View>
        )}

        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            placeholder="메시지를 입력하세요..."
            placeholderTextColor="#C0C0D0"
            value={input}
            onChangeText={setInput}
            returnKeyType="send"
            onSubmitEditing={handleSend}
            editable={!loading}
          />
          <TouchableOpacity
            style={[styles.sendBtn, (loading || !input.trim()) && styles.sendBtnDisabled]}
            onPress={handleSend}
            disabled={loading || !input.trim()}
          >
            <Send size={20} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },

  header:          { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#F0F0F8' },
  headerBtn:       { width: 40, alignItems: 'center' },
  headerCenter:    { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerAvatar:    { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  headerName:      { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  headerSituation: { fontSize: 11, color: '#6C6C80' },

  moodBarContainer: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#F7F7FB', paddingVertical: 10, paddingHorizontal: 16 },
  moodLabel:        { fontSize: 12, fontWeight: '600', width: 80 },
  moodBarTrack:     { flex: 1, height: 8, backgroundColor: '#E2E2EC', borderRadius: 4, overflow: 'hidden' },
  moodBarFill:      { height: '100%', borderRadius: 4 },
  moodPercent:      { fontSize: 12, fontWeight: '600', color: '#6C6C80', width: 36, textAlign: 'right' },
  streakBadge:      { backgroundColor: '#FFF3E0', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  streakText:       { fontSize: 11, fontWeight: '600', color: '#E65100' },

  levelBanner: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 8, backgroundColor: '#FFFFFF', borderBottomWidth: 1, borderBottomColor: '#F0F0F8', gap: 8 },
  levelLabel:  { fontSize: 12, color: '#6C6C80' },

  messageList:    { padding: 16, gap: 4 },
  messageWrapper: { marginBottom: 12 },

  bubbleRow:      { flexDirection: 'row', alignItems: 'flex-end' },
  bubbleRowAi:    { justifyContent: 'flex-start' },
  bubbleRowUser:  { justifyContent: 'flex-end' },
  bubbleAvatar:   { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginRight: 8 },
  bubble:         { maxWidth: '75%', paddingHorizontal: 14, paddingVertical: 10, borderRadius: 18 },
  bubbleAi:       { backgroundColor: '#F5F5FA', borderBottomLeftRadius: 4 },
  bubbleUser:     { backgroundColor: '#6C3BFF', borderBottomRightRadius: 4 },
  bubbleWarning:  { borderWidth: 1.5, borderColor: '#F4A261' },
  bubbleText:     { fontSize: 14, color: '#1A1A2E', lineHeight: 20 },
  bubbleTextUser: { color: '#FFFFFF' },

  feedbackCard:      { marginTop: 4, marginLeft: 40, borderRadius: 12, padding: 10, borderWidth: 1 },
  feedbackCardOk:    { backgroundColor: '#F0FFF4', borderColor: '#A5D6A7' },
  feedbackCardError: { backgroundColor: '#FFF8F0', borderColor: '#FFCC80' },

  feedbackSummaryRow:  { flexDirection: 'row', alignItems: 'center', gap: 6 },
  feedbackSummaryText: { flex: 1, fontSize: 12, fontWeight: '600' },
  feedbackScore:       { fontSize: 12, fontWeight: '700', color: '#6C3BFF' },
  feedbackExpand:      { fontSize: 10, color: '#B0B0C5', marginLeft: 4 },

  feedbackDetail:        { marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#F0F0F5' },
  feedbackSummaryNote:   { fontSize: 12, color: '#4B4B63', lineHeight: 18, marginBottom: 10 },
  feedbackEncouragement: { fontSize: 13, color: '#4CAF50', lineHeight: 18 },

  correctionList: { gap: 8, marginBottom: 10 },
  correctionItem: { borderLeftWidth: 3, paddingLeft: 10, paddingVertical: 4 },
  correctionRow:  { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 2 },
  correctionOriginal: { fontSize: 13, color: '#E53935', textDecorationLine: 'line-through' },
  correctionArrow:    { fontSize: 13, color: '#6C6C80' },
  correctionFixed:    { fontSize: 13, color: '#2E7D32', fontWeight: '600' },
  correctionExplain:  { fontSize: 12, color: '#6C6C80', lineHeight: 18 },
  correctionTip:      { fontSize: 11, color: '#6C3BFF', marginTop: 2 },

  alternativesSection:   { backgroundColor: '#F0ECFF', borderRadius: 10, padding: 12 },
  alternativesHeader:    { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10 },
  alternativesTitle:     { fontSize: 12, fontWeight: '700', color: '#6C3BFF' },
  alternativeItem:       { paddingBottom: 8 },
  alternativeItemBorder: { borderBottomWidth: 1, borderBottomColor: '#DDD6FF', marginBottom: 8 },
  alternativeExpression: { fontSize: 15, fontWeight: '700', color: '#3D1F8D', marginBottom: 2 },
  alternativeExplain:    { fontSize: 11, color: '#7B6FB5', lineHeight: 16 },

  loadingRow:    { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 16, paddingBottom: 8 },
  loadingBubble: { backgroundColor: '#F5F5FA', borderRadius: 18, paddingHorizontal: 20, paddingVertical: 12 },

  inputBar:        { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12, borderTopWidth: 1, borderTopColor: '#F0F0F8', backgroundColor: '#FFFFFF', gap: 10 },
  input:           { flex: 1, backgroundColor: '#F5F5FA', borderRadius: 24, paddingHorizontal: 16, paddingVertical: 10, fontSize: 14, color: '#1A1A2E' },
  sendBtn:         { width: 44, height: 44, borderRadius: 22, backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center' },
  sendBtnDisabled: { opacity: 0.5 },
});
