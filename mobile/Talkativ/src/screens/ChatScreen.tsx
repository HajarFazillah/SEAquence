import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  SafeAreaView, FlatList, TextInput, KeyboardAvoidingView, 
  Platform, ActivityIndicator, Animated,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { 
  ChevronLeft, X, Send, Lightbulb, 
  Smile, Meh, Frown, Angry, Heart,
  HelpCircle, MessageCircle,
} from 'lucide-react-native';
import { Card, SpeechLevelBadge, Icon } from '../components';
import { apiService, ChatMessage } from '../services/api';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  feedback?: {
    detected_level: string;
    is_appropriate: boolean;
    feedback_ko?: string;
  };
}

const getMoodConfig = (mood: number) => {
  if (mood >= 80) return { icon: Heart, color: '#E91E63', label: '아주 좋아요!' };
  if (mood >= 60) return { icon: Smile, color: '#4CAF50', label: '좋아요' };
  if (mood >= 40) return { icon: Meh, color: '#F4A261', label: '그저 그래요' };
  if (mood >= 20) return { icon: Frown, color: '#FF9800', label: '조금 힘들어요' };
  return { icon: Angry, color: '#E53935', label: '화나요!' };
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

export default function ChatScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const flatListRef = useRef<FlatList>(null);

  const avatar = route.params?.avatar;
  const situation = route.params?.situation;
  const recommendedLevel = route.params?.recommendedLevel || 'polite';
  const profileName = route.params?.name || avatar?.name_ko || '김수진';
  const profileBg = route.params?.avatarBg || avatar?.avatarBg || '#FFB6C1';

  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      text: avatar?.greeting || `안녕하세요! ${situation?.name_ko || '대화'}를 시작해볼까요?`,
      sender: 'ai',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [showFeedback, setShowFeedback] = useState<Message | null>(null);
  
  const [avatarMood, setAvatarMood] = useState(70);
  const moodAnim = useRef(new Animated.Value(70)).current;
  
  const [showSuggestion, setShowSuggestion] = useState(false);
  const [suggestionIndex, setSuggestionIndex] = useState(0);
  const suggestions = getSuggestionTopics(avatar);
  
  const [lastMessageTime, setLastMessageTime] = useState(Date.now());
  const [startTime] = useState(Date.now());

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  useEffect(() => {
    const timer = setInterval(() => {
      const timeSinceLastMessage = Date.now() - lastMessageTime;
      if (timeSinceLastMessage > 30000 && !showSuggestion && !loading) {
        setShowSuggestion(true);
        setSuggestionIndex(Math.floor(Math.random() * suggestions.length));
      }
    }, 5000);
    return () => clearInterval(timer);
  }, [lastMessageTime, showSuggestion, loading]);

  useEffect(() => {
    Animated.spring(moodAnim, {
      toValue: avatarMood,
      useNativeDriver: false,
      friction: 8,
    }).start();
  }, [avatarMood]);

  const updateMood = (isCorrect: boolean, improvement: boolean) => {
    setAvatarMood((prev) => {
      let change = isCorrect ? (improvement ? 8 : 3) : -10;
      return Math.max(0, Math.min(100, prev + change));
    });
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input.trim(),
      sender: 'user',
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setLastMessageTime(Date.now());
    setShowSuggestion(false);

    try {
      const history: ChatMessage[] = messages.map((m) => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text,
      }));

      const response = await apiService.sendMessage(
        sessionId,
        'user_1',
        userMessage.text,
        avatar || { id: 'sujin_friend', name_ko: profileName },
        situation || { id: 'cafe_chat', name_ko: '카페 대화' },
        history
      );

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.response,
        sender: 'ai',
      };

      if (response.speech_analysis) {
        userMessage.feedback = response.speech_analysis;
        const isAppropriate = response.speech_analysis.is_appropriate;
        const hadMistakes = messages.filter(m => m.sender === 'user' && m.feedback && !m.feedback.is_appropriate).length > 0;
        updateMood(isAppropriate, hadMistakes && isAppropriate);
        
        if (!isAppropriate) {
          setShowFeedback(userMessage);
          setTimeout(() => setShowFeedback(null), 5000);
        }
      } else {
        updateMood(true, false);
      }

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const fallbackMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: '네, 그렇군요! 더 이야기해주세요.',
        sender: 'ai',
      };
      setMessages((prev) => [...prev, fallbackMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleEndChat = () => {
    const duration = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    const durationStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

    navigation.navigate('ConversationSummary', { 
      avatar, 
      duration: durationStr,
      situation,
      conversationHistory: messages,
      finalMood: avatarMood,
    });
  };

  const moodConfig = getMoodConfig(avatarMood);
  const MoodIcon = moodConfig.icon;

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
        
        {item.sender === 'user' && item.feedback && (
          <View style={styles.feedbackBadge}>
            <Text style={[
              styles.feedbackTextSmall,
              item.feedback.is_appropriate ? styles.feedbackGood : styles.feedbackBad,
            ]}>
              {item.feedback.is_appropriate ? '✓' : '!'} {item.feedback.detected_level}
            </Text>
          </View>
        )}
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.safe}>
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

      {/* Mood Bar */}
      <View style={styles.moodBarContainer}>
        <View style={styles.moodBarContent}>
          <MoodIcon size={20} color={moodConfig.color} />
          <Text style={[styles.moodLabel, { color: moodConfig.color }]}>{moodConfig.label}</Text>
          <View style={styles.moodBarTrack}>
            <Animated.View 
              style={[
                styles.moodBarFill,
                { 
                  backgroundColor: moodConfig.color,
                  width: moodAnim.interpolate({
                    inputRange: [0, 100],
                    outputRange: ['0%', '100%'],
                  }),
                },
              ]} 
            />
          </View>
          <Text style={styles.moodPercent}>{avatarMood}%</Text>
        </View>
      </View>

      {/* Recommended speech level banner */}
      <View style={styles.levelBanner}>
        <Text style={styles.levelLabel}>추천 말투:</Text>
        <SpeechLevelBadge level={recommendedLevel} size="small" />
      </View>

      {/* Feedback popup */}
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
        </Card>
      )}

      {/* Suggestion popup */}
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
              onPress={() => setSuggestionIndex((prev) => (prev + 1) % suggestions.length)}
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
        {/* Messages */}
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messageList}
          renderItem={renderMessage}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />

        {/* Loading indicator */}
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

        {/* Help button */}
        {!showSuggestion && (
          <TouchableOpacity 
            style={styles.helpButton}
            onPress={() => setShowSuggestion(true)}
          >
            <HelpCircle size={18} color="#6C3BFF" />
            <Text style={styles.helpButtonText}>도움말</Text>
          </TouchableOpacity>
        )}

        {/* Input bar */}
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
            style={[styles.sendBtn, loading && styles.sendBtnDisabled]} 
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

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F8',
  },
  headerBtn: { width: 40, alignItems: 'center' },
  headerCenter: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerInfo: { alignItems: 'flex-start' },
  headerName: { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  headerSituation: { fontSize: 11, color: '#6C6C80' },

  moodBarContainer: {
    backgroundColor: '#F7F7FB',
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  moodBarContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  moodLabel: {
    fontSize: 12,
    fontWeight: '600',
    width: 80,
  },
  moodBarTrack: {
    flex: 1,
    height: 8,
    backgroundColor: '#E2E2EC',
    borderRadius: 4,
    overflow: 'hidden',
  },
  moodBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  moodPercent: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C6C80',
    width: 36,
    textAlign: 'right',
  },

  levelBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F8',
    gap: 8,
  },
  levelLabel: { fontSize: 12, color: '#6C6C80' },

  feedbackPopup: {
    position: 'absolute',
    top: 160,
    left: 16,
    right: 16,
    zIndex: 100,
    backgroundColor: '#FFF3E0',
    borderLeftWidth: 4,
    borderLeftColor: '#F4A261',
  },
  feedbackHeader: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    gap: 6, 
    marginBottom: 4,
  },
  feedbackTitle: { 
    flex: 1,
    fontSize: 14, 
    fontWeight: '600', 
    color: '#1A1A2E',
  },
  feedbackMessage: { fontSize: 13, color: '#6C6C80', lineHeight: 18 },

  suggestionPopup: {
    position: 'absolute',
    bottom: 100,
    left: 16,
    right: 16,
    zIndex: 100,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
    borderWidth: 1,
    borderColor: '#F0EDFF',
  },
  suggestionContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  suggestionIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F0EDFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  suggestionTextContainer: { flex: 1 },
  suggestionLabel: {
    fontSize: 12,
    color: '#6C6C80',
    marginBottom: 4,
  },
  suggestionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A2E',
    lineHeight: 20,
  },
  suggestionClose: { padding: 4 },
  suggestionActions: {
    flexDirection: 'row',
    gap: 10,
  },
  suggestionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: '#F5F5FA',
  },
  suggestionBtnPrimary: { backgroundColor: '#6C3BFF' },
  suggestionBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6C6C80',
  },

  messageList: { padding: 16, gap: 12 },
  bubbleRow: { flexDirection: 'row', alignItems: 'flex-end' },
  bubbleRowAi: { justifyContent: 'flex-start' },
  bubbleRowUser: { justifyContent: 'flex-end' },
  bubbleAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  bubble: {
    maxWidth: '75%',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 18,
  },
  bubbleAi: { backgroundColor: '#F5F5FA', borderBottomLeftRadius: 4 },
  bubbleUser: { backgroundColor: '#6C3BFF', borderBottomRightRadius: 4 },
  bubbleWarning: { borderWidth: 1, borderColor: '#F4A261' },
  bubbleText: { fontSize: 14, color: '#1A1A2E', lineHeight: 20 },
  bubbleTextUser: { color: '#FFFFFF' },

  feedbackBadge: { marginTop: 4 },
  feedbackTextSmall: { fontSize: 10, fontWeight: '600' },
  feedbackGood: { color: 'rgba(255,255,255,0.7)' },
  feedbackBad: { color: '#FFE0B2' },

  helpButton: {
    position: 'absolute',
    right: 16,
    bottom: 80,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#F0EDFF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
  },
  helpButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C3BFF',
  },

  loadingRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  loadingBubble: {
    backgroundColor: '#F5F5FA',
    borderRadius: 18,
    paddingHorizontal: 20,
    paddingVertical: 12,
  },

  inputBar: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F8',
    backgroundColor: '#FFFFFF',
    gap: 10,
  },
  input: {
    flex: 1,
    backgroundColor: '#F5F5FA',
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 14,
    color: '#1A1A2E',
  },
  sendBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#6C3BFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnDisabled: { opacity: 0.5 },
});
