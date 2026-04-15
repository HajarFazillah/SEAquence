import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput,
  KeyboardAvoidingView, Platform, ActivityIndicator, Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  ChevronLeft, X, Send, Lightbulb,
  Smile, Meh, Frown, Angry, Heart,
  HelpCircle, MessageCircle,
} from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Card, SpeechLevelBadge, Icon } from '../components';

// ─── AI 서버 주소 ────────────────────────────────────────────────
const AI_SERVER = 'http://10.0.2.2:8000'; // EC2 배포 시 IP로 교체

// ─── 타입 ────────────────────────────────────────────────────────
interface Correction {
  original:    string;
  corrected:   string;
  explanation: string;
  severity:    string;
}

interface SpeechAnalysis {
  detected_level:  string;
  is_appropriate:  boolean;
  feedback_ko:     string | null;
  accuracy_score:  number;
  corrections:     Correction[];
  is_mixed:        boolean;
}

interface Message {
  id:              string;
  text:            string;
  sender:          'user' | 'ai';
  feedback?:       SpeechAnalysis;
}

// ─── 기분 설정 ────────────────────────────────────────────────────
const getMoodConfig = (mood: number) => {
  if (mood >= 80) return { icon: Heart,  color: '#E91E63', label: '아주 좋아요!' };
  if (mood >= 60) return { icon: Smile,  color: '#4CAF50', label: '좋아요'       };
  if (mood >= 40) return { icon: Meh,    color: '#F4A261', label: '그저 그래요'  };
  if (mood >= 20) return { icon: Frown,  color: '#FF9800', label: '조금 힘들어요' };
  return           { icon: Angry,  color: '#E53935', label: '화나요!'       };
};

// ─── 제안 주제 ────────────────────────────────────────────────────
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

// ─── AI 서버 호출 함수 ───────────────────────────────────────────
const sendMessageToAI = async (
  text:      string,
  history:   { role: string; content: string }[],
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
        id:                  avatar?.id                 || 'sujin_friend',
        name_ko:             avatar?.name_ko            || '수진',
        role:                avatar?.role               || 'friend',
        personality_traits:  avatar?.personality_traits || [],
        interests:           avatar?.interests          || [],
        dislikes:            avatar?.dislikes           || [],
      },
      situation: situation?.name_ko || situation?.title || null,
      user_id,
    }),
  });

  if (!res.ok) throw new Error(`AI server error: ${res.status}`);

  const data = await res.json();

  // AI 서버 응답 → ChatScreen 포맷 변환
  return {
    message: data.message,
    speech_analysis: data.correction ? {
      detected_level: data.correction.detected_level || 'unknown',
      is_appropriate: !data.correction.has_errors,
      feedback_ko:    data.correction.corrections?.[0]?.explanation || null,
      accuracy_score: data.correction.accuracy_score || 100,
      corrections:    data.correction.corrections   || [],
      is_mixed:       data.correction.is_mixed      || false,
    } as SpeechAnalysis : null,
    mood_change:    data.mood_change    || 0,
    current_mood:   data.current_mood   || 70,
    mood_emoji:     data.mood_emoji     || '😊',
    correct_streak: data.correct_streak || 0,
  };
};

const analyzeSessionWithAI = async (
  avatar:   any,
  history:  { role: string; content: string }[],
) => {
  const res = await fetch(`${AI_SERVER}/api/v1/chat/analyze`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      avatar,
      conversation_history: history,
    }),
  });
  if (!res.ok) throw new Error(`Analyze error: ${res.status}`);
  return await res.json();
};

// ─── ChatScreen ──────────────────────────────────────────────────
export default function ChatScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();

  const avatar          = route.params?.avatar;
  const situation       = route.params?.situation;
  const recommendedLevel = route.params?.recommendedLevel || 'polite';
  const profileName     = route.params?.name    || avatar?.name_ko || '김수진';
  const profileBg       = route.params?.avatarBg || avatar?.avatarBg || '#FFB6C1';

  const flatListRef = useRef<FlatList>(null);

  // ── 상태 ──────────────────────────────────────────────────────
  const [messages, setMessages] = useState<Message[]>([
    {
      id:     '0',
      text:   avatar?.greeting || `안녕하세요! ${situation?.name_ko || '대화'}를 시작해볼까요?`,
      sender: 'ai',
    },
  ]);
  const [input,          setInput]          = useState('');
  const [loading,        setLoading]        = useState(false);
  const [showFeedback,   setShowFeedback]   = useState<Message | null>(null);
  const [avatarMood,     setAvatarMood]     = useState(70);
  const [showSuggestion, setShowSuggestion] = useState(false);
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const [lastMessageTime, setLastMessageTime] = useState(Date.now());
  const [startTime]      = useState(Date.now());
  const [userId,         setUserId]         = useState('test-user-1');
  const [correctStreak,  setCorrectStreak]  = useState(0);

  const moodAnim   = useRef(new Animated.Value(70)).current;
  const suggestions = getSuggestionTopics(avatar);

  // ── user_id 로드 ───────────────────────────────────────────────
  useEffect(() => {
    AsyncStorage.getItem('user_id').then(id => {
      if (id) setUserId(id);
    });
  }, []);

  // ── 스크롤 ────────────────────────────────────────────────────
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
    }
  }, [messages]);

  // ── 30초 비활동 시 제안 팝업 ──────────────────────────────────
  useEffect(() => {
    const timer = setInterval(() => {
      const idle = Date.now() - lastMessageTime;
      if (idle > 30000 && !showSuggestion && !loading) {
        setShowSuggestion(true);
        setSuggestionIndex(Math.floor(Math.random() * suggestions.length));
      }
    }, 5000);
    return () => clearInterval(timer);
  }, [lastMessageTime, showSuggestion, loading]);

  // ── 기분 바 애니메이션 ────────────────────────────────────────
  useEffect(() => {
    Animated.spring(moodAnim, {
      toValue: avatarMood, useNativeDriver: false, friction: 8,
    }).start();
  }, [avatarMood]);

  // ── 기분 업데이트 ─────────────────────────────────────────────
  const updateMoodFromServer = (serverMood: number) => {
    setAvatarMood(serverMood);
  };

  // ── 메시지 전송 ───────────────────────────────────────────────
  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const text = input.trim();
    const userMsg: Message = { id: Date.now().toString(), text, sender: 'user' };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setLastMessageTime(Date.now());
    setShowSuggestion(false);
    setShowFeedback(null);

    try {
      // 대화 기록 (AI 서버 포맷)
      const history = messages.map(m => ({
        role:    m.sender === 'user' ? 'user' : 'assistant',
        content: m.text,
      }));

      const data = await sendMessageToAI(text, history, avatar, situation, userId);

      // 아바타 응답
      const aiMsg: Message = {
        id:     (Date.now() + 1).toString(),
        text:   data.message,
        sender: 'ai',
      };

      // 교정 피드백 처리
      if (data.speech_analysis) {
        userMsg.feedback = data.speech_analysis;

        // 피드백 팝업 (오류 있을 때)
        if (!data.speech_analysis.is_appropriate) {
          setShowFeedback({ ...userMsg });
          setTimeout(() => setShowFeedback(null), 5000);
        }
      }

      // 기분 + 스트릭 업데이트
      updateMoodFromServer(data.current_mood);
      setCorrectStreak(data.correct_streak);

      // 메시지 목록 업데이트
      setMessages(prev => {
        const updated = prev.map(m =>
          m.id === userMsg.id ? { ...m, feedback: userMsg.feedback } : m
        );
        return [...updated, aiMsg];
      });

    } catch (error) {
      console.error('Chat error:', error);
      // 폴백 응답
      setMessages(prev => [...prev, {
        id:     (Date.now() + 1).toString(),
        text:   '네, 그렇군요! 더 이야기해주세요.',
        sender: 'ai',
      }]);
    } finally {
      setLoading(false);
    }
  };

  // ── 세션 종료 ────────────────────────────────────────────────
  const handleEndChat = async () => {
    const duration    = Math.floor((Date.now() - startTime) / 1000);
    const minutes     = Math.floor(duration / 60);
    const seconds     = duration % 60;
    const durationStr = `${String(minutes).padStart(2,'0')}:${String(seconds).padStart(2,'0')}`;

    const history = messages.map(m => ({
      role:    m.sender === 'user' ? 'user' : 'assistant',
      content: m.text,
    }));

    // 세션 분석 리포트 가져오기
    let sessionReport = null;
    try {
      sessionReport = await analyzeSessionWithAI(avatar, history);
    } catch (e) {
      console.error('Analyze error:', e);
    }

    navigation.navigate('ConversationSummary', {
      avatar,
      duration:            durationStr,
      situation,
      conversationHistory: history,
      finalMood:           avatarMood,
      sessionReport,       // ← AI 서버 분석 결과
    });
  };

  // ── 렌더링 ───────────────────────────────────────────────────
  const moodConfig = getMoodConfig(avatarMood);
  const MoodIcon   = moodConfig.icon;

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={[
      styles.bubbleRow,
      item.sender === 'user' ? styles.bubbleRowUser : styles.bubbleRowAi,
    ]}>
      {item.sender === 'ai' && (
        <View style={[styles.bubbleAvatar, { backgroundColor: profileBg }]}>
          <Icon name={avatar?.icon || 'user'} size={16} color="#FFFFFF" />
        </View>
      )}
      <View style={[
        styles.bubble,
        item.sender === 'user' ? styles.bubbleUser : styles.bubbleAi,
        item.feedback && !item.feedback.is_appropriate && styles.bubbleWarning,
      ]}>
        <Text style={[
          styles.bubbleText,
          item.sender === 'user' && styles.bubbleTextUser,
        ]}>
          {item.text}
        </Text>

        {/* 말풍선 내 피드백 배지 */}
        {item.sender === 'user' && item.feedback && (
          <View style={styles.feedbackBadge}>
            <Text style={[
              styles.feedbackTextSmall,
              item.feedback.is_appropriate ? styles.feedbackGood : styles.feedbackBad,
            ]}>
              {item.feedback.is_appropriate ? '✓' : '!'} {item.feedback.detected_level}
              {item.feedback.accuracy_score !== undefined
                ? `  ${item.feedback.accuracy_score}점` : ''}
            </Text>
          </View>
        )}

        {/* 교정 내용 (오류 있을 때) */}
        {item.sender === 'user' && item.feedback && !item.feedback.is_appropriate &&
          item.feedback.corrections?.map((c, i) => (
            <View key={i} style={styles.inlineFix}>
              <Text style={styles.inlineFixText}>
                ✕ "{c.original}" → "{c.corrected}"
              </Text>
            </View>
          ))
        }
      </View>
    </View>
  );

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
          <View style={styles.headerInfo}>
            <Text style={styles.headerName}>{profileName}</Text>
            <Text style={styles.headerSituation}>{situation?.name_ko || '대화'}</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.headerBtn} onPress={handleEndChat}>
          <X size={24} color="#E53935" />
        </TouchableOpacity>
      </View>

      {/* ── 기분 바 ──────────────────────────────────────────── */}
      <View style={styles.moodBarContainer}>
        <View style={styles.moodBarContent}>
          <MoodIcon size={20} color={moodConfig.color} />
          <Text style={[styles.moodLabel, { color: moodConfig.color }]}>
            {moodConfig.label}
          </Text>
          <View style={styles.moodBarTrack}>
            <Animated.View style={[
              styles.moodBarFill,
              {
                backgroundColor: moodConfig.color,
                width: moodAnim.interpolate({
                  inputRange:  [0, 100],
                  outputRange: ['0%', '100%'],
                }),
              },
            ]} />
          </View>
          <Text style={styles.moodPercent}>{avatarMood}%</Text>
          {/* 스트릭 표시 */}
          {correctStreak >= 3 && (
            <View style={styles.streakBadge}>
              <Text style={styles.streakText}>🔥 {correctStreak}연속</Text>
            </View>
          )}
        </View>
      </View>

      {/* ── 추천 말투 배너 ───────────────────────────────────── */}
      <View style={styles.levelBanner}>
        <Text style={styles.levelLabel}>추천 말투:</Text>
        <SpeechLevelBadge level={recommendedLevel} size="small" />
      </View>

      {/* ── 교정 팝업 ────────────────────────────────────────── */}
      {showFeedback && showFeedback.feedback && (
        <Card variant="elevated" style={styles.feedbackPopup}>
          <View style={styles.feedbackHeader}>
            <Lightbulb size={18} color="#F4A261" />
            <Text style={styles.feedbackTitle}>말투 피드백</Text>
            <TouchableOpacity onPress={() => setShowFeedback(null)}>
              <X size={18} color="#6C6C80" />
            </TouchableOpacity>
          </View>
          <Text style={styles.feedbackMessage}>
            {showFeedback.feedback.feedback_ko ||
              `추천 말투(${recommendedLevel})와 다른 말투를 사용했어요.`}
          </Text>
          {showFeedback.feedback.corrections?.map((c, i) => (
            <Text key={i} style={styles.feedbackCorrection}>
              ✕ "{c.original}"  →  "{c.corrected}"
            </Text>
          ))}
          <Text style={styles.feedbackScore}>
            정확도: {showFeedback.feedback.accuracy_score}점
          </Text>
        </Card>
      )}

      {/* ── 제안 팝업 ────────────────────────────────────────── */}
      {showSuggestion && (
        <View style={styles.suggestionPopup}>
          <View style={styles.suggestionContent}>
            <View style={styles.suggestionIcon}>
              <HelpCircle size={20} color="#6C3BFF" />
            </View>
            <View style={styles.suggestionTextContainer}>
              <Text style={styles.suggestionLabel}>무슨 말을 해야 할지 모르겠나요?</Text>
              <Text style={styles.suggestionText}>{suggestions[suggestionIndex]}</Text>
            </View>
            <TouchableOpacity
              style={styles.suggestionClose}
              onPress={() => setShowSuggestion(false)}
            >
              <X size={16} color="#B0B0C5" />
            </TouchableOpacity>
          </View>
          <View style={styles.suggestionActions}>
            <TouchableOpacity
              style={styles.suggestionBtn}
              onPress={() => setSuggestionIndex(prev => (prev + 1) % suggestions.length)}
            >
              <Text style={styles.suggestionBtnText}>다른 제안</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.suggestionBtn, styles.suggestionBtnPrimary]}
              onPress={() => setShowSuggestion(false)}
            >
              <MessageCircle size={14} color="#FFFFFF" />
              <Text style={[styles.suggestionBtnText, { color: '#FFFFFF' }]}>알겠어요</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={0}
      >
        {/* ── 메시지 목록 ──────────────────────────────────── */}
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.messageList}
          renderItem={renderMessage}
          onContentSizeChange={() =>
            flatListRef.current?.scrollToEnd({ animated: true })
          }
        />

        {/* ── 로딩 ─────────────────────────────────────────── */}
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

        {/* ── 도움말 버튼 ──────────────────────────────────── */}
        {!showSuggestion && (
          <TouchableOpacity
            style={styles.helpButton}
            onPress={() => setShowSuggestion(true)}
          >
            <HelpCircle size={18} color="#6C3BFF" />
            <Text style={styles.helpButtonText}>도움말</Text>
          </TouchableOpacity>
        )}

        {/* ── 입력창 ───────────────────────────────────────── */}
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

// ─── 스타일 ──────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },

  header: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16, paddingVertical: 12,
    borderBottomWidth: 1, borderBottomColor: '#F0F0F8',
  },
  headerBtn:       { width: 40, alignItems: 'center' },
  headerCenter:    { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerAvatar:    { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  headerInfo:      { alignItems: 'flex-start' },
  headerName:      { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  headerSituation: { fontSize: 11, color: '#6C6C80' },

  moodBarContainer: { backgroundColor: '#F7F7FB', paddingVertical: 10, paddingHorizontal: 16 },
  moodBarContent:   { flexDirection: 'row', alignItems: 'center', gap: 10 },
  moodLabel:        { fontSize: 12, fontWeight: '600', width: 80 },
  moodBarTrack:     { flex: 1, height: 8, backgroundColor: '#E2E2EC', borderRadius: 4, overflow: 'hidden' },
  moodBarFill:      { height: '100%', borderRadius: 4 },
  moodPercent:      { fontSize: 12, fontWeight: '600', color: '#6C6C80', width: 36, textAlign: 'right' },
  streakBadge:      { backgroundColor: '#FFF3E0', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  streakText:       { fontSize: 11, fontWeight: '600', color: '#E65100' },

  levelBanner: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    paddingVertical: 8, backgroundColor: '#FFFFFF',
    borderBottomWidth: 1, borderBottomColor: '#F0F0F8', gap: 8,
  },
  levelLabel: { fontSize: 12, color: '#6C6C80' },

  feedbackPopup: {
    position: 'absolute', top: 160, left: 16, right: 16, zIndex: 100,
    backgroundColor: '#FFF3E0', borderLeftWidth: 4, borderLeftColor: '#F4A261',
  },
  feedbackHeader:     { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 },
  feedbackTitle:      { flex: 1, fontSize: 14, fontWeight: '600', color: '#1A1A2E' },
  feedbackMessage:    { fontSize: 13, color: '#6C6C80', lineHeight: 18 },
  feedbackCorrection: { fontSize: 12, color: '#D85A30', marginTop: 4 },
  feedbackScore:      { fontSize: 11, color: '#999', marginTop: 4 },

  suggestionPopup: {
    position: 'absolute', bottom: 100, left: 16, right: 16, zIndex: 100,
    backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15, shadowRadius: 12, elevation: 8,
    borderWidth: 1, borderColor: '#F0EDFF',
  },
  suggestionContent:       { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 12 },
  suggestionIcon:          { width: 36, height: 36, borderRadius: 18, backgroundColor: '#F0EDFF', alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  suggestionTextContainer: { flex: 1 },
  suggestionLabel:         { fontSize: 12, color: '#6C6C80', marginBottom: 4 },
  suggestionText:          { fontSize: 14, fontWeight: '600', color: '#1A1A2E', lineHeight: 20 },
  suggestionClose:         { padding: 4 },
  suggestionActions:       { flexDirection: 'row', gap: 10 },
  suggestionBtn:           { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingVertical: 10, borderRadius: 10, backgroundColor: '#F5F5FA' },
  suggestionBtnPrimary:    { backgroundColor: '#6C3BFF' },
  suggestionBtnText:       { fontSize: 13, fontWeight: '600', color: '#6C6C80' },

  messageList: { padding: 16, gap: 12 },
  bubbleRow:      { flexDirection: 'row', alignItems: 'flex-end' },
  bubbleRowAi:    { justifyContent: 'flex-start' },
  bubbleRowUser:  { justifyContent: 'flex-end' },
  bubbleAvatar:   { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginRight: 8 },
  bubble:         { maxWidth: '75%', paddingHorizontal: 14, paddingVertical: 10, borderRadius: 18 },
  bubbleAi:       { backgroundColor: '#F5F5FA', borderBottomLeftRadius: 4 },
  bubbleUser:     { backgroundColor: '#6C3BFF', borderBottomRightRadius: 4 },
  bubbleWarning:  { borderWidth: 1, borderColor: '#F4A261' },
  bubbleText:     { fontSize: 14, color: '#1A1A2E', lineHeight: 20 },
  bubbleTextUser: { color: '#FFFFFF' },

  feedbackBadge:     { marginTop: 4 },
  feedbackTextSmall: { fontSize: 10, fontWeight: '600' },
  feedbackGood:      { color: 'rgba(255,255,255,0.7)' },
  feedbackBad:       { color: '#FFE0B2' },

  inlineFix:     { marginTop: 4, backgroundColor: 'rgba(255,255,255,0.15)', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  inlineFixText: { fontSize: 10, color: '#FFE0B2' },

  helpButton: {
    position: 'absolute', right: 16, bottom: 80,
    flexDirection: 'row', alignItems: 'center', gap: 4,
    backgroundColor: '#F0EDFF', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20,
  },
  helpButtonText: { fontSize: 12, fontWeight: '600', color: '#6C3BFF' },

  loadingRow:    { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 16, paddingBottom: 8 },
  loadingBubble: { backgroundColor: '#F5F5FA', borderRadius: 18, paddingHorizontal: 20, paddingVertical: 12 },

  inputBar: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 12,
    borderTopWidth: 1, borderTopColor: '#F0F0F8',
    backgroundColor: '#FFFFFF', gap: 10,
  },
  input:          { flex: 1, backgroundColor: '#F5F5FA', borderRadius: 24, paddingHorizontal: 16, paddingVertical: 10, fontSize: 14, color: '#1A1A2E' },
  sendBtn:        { width: 44, height: 44, borderRadius: 22, backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center' },
  sendBtnDisabled:{ opacity: 0.5 },
});