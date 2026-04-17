import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput,
  KeyboardAvoidingView, Platform, ActivityIndicator, Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  ChevronLeft, X, Send, Smile, Meh, Frown, Angry, Heart,
  HelpCircle, MessageCircle, CheckCircle, AlertCircle,
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

interface SpeechAnalysis {
  detected_speech_level: string;
  speech_level_correct:  boolean;
  expected_speech_level: string;
  has_errors:            boolean;
  accuracy_score:        number;
  corrections:           Correction[];
  encouragement?:        string;
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

const getSuggestionTopics = (avatar: any) => {
  const interests = avatar?.interests || ['일상', '취미', '음식'];
  return [
    `${avatar?.name_ko || '상대방'}에게 오늘 뭐 했는지 물어보세요`,
    `좋아하는 ${interests[0] || '취미'}에 대해 이야기해보세요`,
    `주말 계획에 대해 물어보세요`,
    `요즘 관심사에 대해 이야기해보세요`,
    `${interests[1] || '음식'} 추천을 부탁해보세요`,
  ];
};

const buildHistoryFromMessages = (messages: Message[]): HistoryItem[] =>
  messages
    .map(m => ({ role: (m.sender === 'user' ? 'user' : 'assistant') as HistoryRole, content: m.text }))
    .filter(m => m.content.trim().length > 0);

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
  const speech_analysis: SpeechAnalysis | null = correction ? {
    detected_speech_level: correction.detected_speech_level || '',
    speech_level_correct:  correction.speech_level_correct  ?? true,
    expected_speech_level: correction.expected_speech_level || '',
    has_errors:            correction.has_errors            ?? false,
    accuracy_score:        correction.accuracy_score        ?? 100,
    corrections:           correction.corrections           || [],
    encouragement:         correction.encouragement         || '',
  } : null;

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
  const [showSuggestion,   setShowSuggestion]   = useState(false);
  const [suggestionIndex,  setSuggestionIndex]  = useState(0);
  const [lastMessageTime,  setLastMessageTime]  = useState(Date.now());
  const [startTime]        = useState(Date.now());
  const [userId,           setUserId]           = useState('test-user-1');
  const [correctStreak,    setCorrectStreak]    = useState(0);
  const [expandedFeedback, setExpandedFeedback] = useState<Record<string, boolean>>({});

  const moodAnim    = useRef(new Animated.Value(70)).current;
  const suggestions = getSuggestionTopics(avatar);

  useEffect(() => {
    AsyncStorage.getItem('user_id').then(id => { if (id) setUserId(id); });
  }, []);

  useEffect(() => {
    if (messages.length > 0)
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
  }, [messages]);

  useEffect(() => {
    const timer = setInterval(() => {
      if (Date.now() - lastMessageTime > 30000 && !showSuggestion && !loading)
        setShowSuggestion(true);
    }, 5000);
    return () => clearInterval(timer);
  }, [lastMessageTime, showSuggestion, loading]);

  useEffect(() => {
    Animated.spring(moodAnim, { toValue: avatarMood, useNativeDriver: false, friction: 8 }).start();
  }, [avatarMood]);

  // ── 메시지 전송 ───────────────────────────────────────────────
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const text    = input.trim();
    const userMsg: Message = { id: Date.now().toString(), text, sender: 'user' };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setLastMessageTime(Date.now());
    setShowSuggestion(false);

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

      if (data.speech_analysis?.has_errors)
        setExpandedFeedback(prev => ({ ...prev, [userMsg.id]: true }));

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

  // ── 세션 종료 — 피드백 데이터 함께 전달 ─────────────────────
  const handleEndChat = async () => {
    const duration    = Math.floor((Date.now() - startTime) / 1000);
    const durationStr = `${String(Math.floor(duration/60)).padStart(2,'0')}:${String(duration%60).padStart(2,'0')}`;
    const history     = buildHistoryFromMessages(messages);

    // 채팅 중 수집된 교정 데이터 추출
    const sessionCorrections = messages
      .filter(m => m.sender === 'user' && m.feedback)
      .map(m => ({
        message:         m.text,
        accuracy_score:  m.feedback!.accuracy_score,
        has_errors:      m.feedback!.has_errors,
        corrections:     m.feedback!.corrections,
        detected_level:  m.feedback!.detected_speech_level,
        encouragement:   m.feedback!.encouragement,
      }));

    const avgScore = sessionCorrections.length > 0
      ? Math.round(sessionCorrections.reduce((sum, c) => sum + c.accuracy_score, 0) / sessionCorrections.length)
      : 100;

    let sessionReport = null;
    try { sessionReport = await analyzeSessionWithAI(avatar, history); } catch {}

    navigation.navigate('ConversationSummary', {
      avatar,
      duration:            durationStr,
      situation,
      conversationHistory: history,
      finalMood:           avatarMood,
      sessionReport,
      sessionCorrections,   // ← 채팅 중 수집된 교정 데이터
      avgScore,             // ← 평균 정확도
    });
  };

  // ── 피드백 카드 ───────────────────────────────────────────────
  const renderFeedbackCard = (item: Message) => {
    if (!item.feedback) return null;
    const fb       = item.feedback;
    const expanded = expandedFeedback[item.id];
    const hasError = fb.has_errors;

    return (
      <TouchableOpacity
        style={[styles.feedbackCard, hasError ? styles.feedbackCardError : styles.feedbackCardOk]}
        onPress={() => setExpandedFeedback(prev => ({ ...prev, [item.id]: !prev[item.id] }))}
        activeOpacity={0.8}
      >
        <View style={styles.feedbackSummaryRow}>
          {hasError
            ? <AlertCircle size={14} color="#E53935" />
            : <CheckCircle size={14} color="#4CAF50" />}
          <Text style={[styles.feedbackSummaryText, { color: hasError ? '#E53935' : '#4CAF50' }]}>
            {fb.detected_speech_level
              ? `${fb.detected_speech_level} 감지`
              : fb.expected_speech_level || '말투 분석'}
          </Text>
          <Text style={styles.feedbackScore}>{fb.accuracy_score}점</Text>
          <Text style={styles.feedbackExpand}>{expanded ? '▲' : '▼'}</Text>
        </View>

        {expanded && (
          <View style={styles.feedbackDetail}>
            {fb.encouragement
              ? <Text style={styles.feedbackEncouragement}>{fb.encouragement}</Text>
              : null}
            {fb.corrections.length > 0 && (
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
      {/* Header */}
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

      {/* 기분 바 */}
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

      {/* 추천 말투 배너 */}
      <View style={styles.levelBanner}>
        <Text style={styles.levelLabel}>추천 말투:</Text>
        <SpeechLevelBadge level={recommendedLevel} size="small" />
      </View>

      {/* 제안 팝업 */}
      {showSuggestion && (
        <View style={styles.suggestionPopup}>
          <View style={styles.suggestionContent}>
            <View style={styles.suggestionIcon}>
              <HelpCircle size={20} color="#6C3BFF" />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.suggestionLabel}>무슨 말을 해야 할지 모르겠나요?</Text>
              <Text style={styles.suggestionText}>{suggestions[suggestionIndex]}</Text>
            </View>
            <TouchableOpacity onPress={() => setShowSuggestion(false)}>
              <X size={16} color="#B0B0C5" />
            </TouchableOpacity>
          </View>
          <View style={styles.suggestionActions}>
            <TouchableOpacity style={styles.suggestionBtn}
              onPress={() => setSuggestionIndex(prev => (prev + 1) % suggestions.length)}>
              <Text style={styles.suggestionBtnText}>다른 제안</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.suggestionBtn, styles.suggestionBtnPrimary]}
              onPress={() => setShowSuggestion(false)}>
              <MessageCircle size={14} color="#FFFFFF" />
              <Text style={[styles.suggestionBtnText, { color: '#FFFFFF' }]}>알겠어요</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

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

        {!showSuggestion && (
          <TouchableOpacity style={styles.helpButton} onPress={() => setShowSuggestion(true)}>
            <HelpCircle size={18} color="#6C3BFF" />
            <Text style={styles.helpButtonText}>도움말</Text>
          </TouchableOpacity>
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

  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#F0F0F8' },
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

  suggestionPopup: { position: 'absolute', bottom: 100, left: 16, right: 16, zIndex: 100, backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, shadowColor: '#000', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.15, shadowRadius: 12, elevation: 8, borderWidth: 1, borderColor: '#F0EDFF' },
  suggestionContent: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 12 },
  suggestionIcon:    { width: 36, height: 36, borderRadius: 18, backgroundColor: '#F0EDFF', alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  suggestionLabel:   { fontSize: 12, color: '#6C6C80', marginBottom: 4 },
  suggestionText:    { fontSize: 14, fontWeight: '600', color: '#1A1A2E', lineHeight: 20 },
  suggestionActions: { flexDirection: 'row', gap: 10 },
  suggestionBtn:     { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingVertical: 10, borderRadius: 10, backgroundColor: '#F5F5FA' },
  suggestionBtnPrimary: { backgroundColor: '#6C3BFF' },
  suggestionBtnText: { fontSize: 13, fontWeight: '600', color: '#6C6C80' },

  messageList:    { padding: 16, gap: 4 },
  messageWrapper: { marginBottom: 12 },

  bubbleRow:     { flexDirection: 'row', alignItems: 'flex-end' },
  bubbleRowAi:   { justifyContent: 'flex-start' },
  bubbleRowUser: { justifyContent: 'flex-end' },
  bubbleAvatar:  { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginRight: 8 },
  bubble:        { maxWidth: '75%', paddingHorizontal: 14, paddingVertical: 10, borderRadius: 18 },
  bubbleAi:      { backgroundColor: '#F5F5FA', borderBottomLeftRadius: 4 },
  bubbleUser:    { backgroundColor: '#6C3BFF', borderBottomRightRadius: 4 },
  bubbleWarning: { borderWidth: 1.5, borderColor: '#F4A261' },
  bubbleText:    { fontSize: 14, color: '#1A1A2E', lineHeight: 20 },
  bubbleTextUser: { color: '#FFFFFF' },

  feedbackCard:      { marginTop: 4, marginLeft: 40, borderRadius: 12, padding: 10, borderWidth: 1 },
  feedbackCardOk:    { backgroundColor: '#F0FFF4', borderColor: '#A5D6A7' },
  feedbackCardError: { backgroundColor: '#FFF8F0', borderColor: '#FFCC80' },

  feedbackSummaryRow:  { flexDirection: 'row', alignItems: 'center', gap: 6 },
  feedbackSummaryText: { flex: 1, fontSize: 12, fontWeight: '600' },
  feedbackScore:       { fontSize: 12, fontWeight: '700', color: '#6C3BFF' },
  feedbackExpand:      { fontSize: 10, color: '#B0B0C5', marginLeft: 4 },

  feedbackDetail:       { marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#F0F0F5' },
  feedbackEncouragement: { fontSize: 13, color: '#4CAF50', marginBottom: 8, lineHeight: 18 },

  correctionList: { gap: 8 },
  correctionItem: { borderLeftWidth: 3, paddingLeft: 10, paddingVertical: 4 },
  correctionRow:  { flexDirection: 'row', alignItems: 'center', gap: 6, flexWrap: 'wrap', marginBottom: 2 },
  correctionOriginal: { fontSize: 13, color: '#E53935', textDecorationLine: 'line-through' },
  correctionArrow:    { fontSize: 13, color: '#6C6C80' },
  correctionFixed:    { fontSize: 13, color: '#2E7D32', fontWeight: '600' },
  correctionExplain:  { fontSize: 12, color: '#6C6C80', lineHeight: 18 },
  correctionTip:      { fontSize: 11, color: '#6C3BFF', marginTop: 2 },

  loadingRow:    { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 16, paddingBottom: 8 },
  loadingBubble: { backgroundColor: '#F5F5FA', borderRadius: 18, paddingHorizontal: 20, paddingVertical: 12 },

  helpButton:     { position: 'absolute', right: 16, bottom: 80, flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: '#F0EDFF', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20 },
  helpButtonText: { fontSize: 12, fontWeight: '600', color: '#6C3BFF' },

  inputBar:        { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12, borderTopWidth: 1, borderTopColor: '#F0F0F8', backgroundColor: '#FFFFFF', gap: 10 },
  input:           { flex: 1, backgroundColor: '#F5F5FA', borderRadius: 24, paddingHorizontal: 16, paddingVertical: 10, fontSize: 14, color: '#1A1A2E' },
  sendBtn:         { width: 44, height: 44, borderRadius: 22, backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center' },
  sendBtnDisabled: { opacity: 0.5 },
});