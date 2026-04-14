import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { MapPin, CheckCircle, XCircle, Lightbulb } from 'lucide-react-native';
import { Header, Card, Button, SpeechLevelBadge, AvatarCircle, Icon } from '../components';
import { apiService } from '../services/api';

interface ExampleExpression {
  greetings: string[];
  questions: string[];
  responses: string[];
}

interface AvoidExpression {
  wrong: string;
  reason: string;
}

export default function SpeechRecommendationScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { avatar, situation } = route.params || {};

  const [loading, setLoading] = useState(true);
  const [recommendation, setRecommendation] = useState<{
    recommended_level: 'formal' | 'polite' | 'informal';
    reason_ko: string;
    example_expressions: ExampleExpression;
    avoid_expressions: AvoidExpression[];
    tips: string[];
  } | null>(null);

  useEffect(() => {
    loadRecommendation();
  }, []);

  const loadRecommendation = async () => {
    try {
      setLoading(true);
      const data = await apiService.getSpeechRecommendation(
        avatar?.id || 'sujin_friend',
        situation?.id || 'cafe_chat'
      );
      setRecommendation(data);
    } catch (error) {
      console.error('Failed to load recommendation:', error);
      // Use fallback data
      setRecommendation({
        recommended_level: avatar?.role === 'professor' || avatar?.role === 'boss' 
          ? 'formal' 
          : avatar?.role === 'friend' || avatar?.role === 'junior'
            ? 'informal'
            : 'polite',
        reason_ko: `${avatar?.name_ko || '상대방'}과의 대화에서 적절한 말투입니다.`,
        example_expressions: {
          greetings: ['안녕하세요', '반갑습니다'],
          questions: ['어떻게 지내세요?', '뭐 하세요?'],
          responses: ['네, 알겠습니다', '좋아요'],
        },
        avoid_expressions: [
          { wrong: '야, 뭐해?', reason: '너무 격식 없는 표현입니다.' },
        ],
        tips: ['자연스럽게 대화하세요', '상대방의 말투에 맞춰보세요'],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStartChat = () => {
    navigation.navigate('Chat', {
      avatar,
      situation,
      recommendedLevel: recommendation?.recommended_level,
    });
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <Header title="추천 말투" />
        <View style={styles.loading}>
          <ActivityIndicator size="large" color="#6C3BFF" />
          <Text style={styles.loadingText}>분석 중...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="추천 말투" />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Context card */}
        <Card variant="elevated" style={styles.contextCard}>
          <View style={styles.contextRow}>
            <View style={[styles.avatarIcon, { backgroundColor: avatar?.avatarBg || '#FFB6C1' }]}>
              <Icon name={avatar?.icon || 'user'} size={32} color="#FFFFFF" />
            </View>
            <View style={styles.contextInfo}>
              <Text style={styles.contextLabel}>대화 상대</Text>
              <Text style={styles.contextName}>{avatar?.name_ko || '상대방'}</Text>
              <View style={styles.contextSituationRow}>
                <MapPin size={14} color="#6C6C80" />
                <Text style={styles.contextSituation}>
                  {situation?.name_ko || '일상 대화'}
                </Text>
              </View>
            </View>
          </View>
        </Card>

        {/* Recommended speech level */}
        <Text style={styles.sectionTitle}>추천 말투</Text>
        
        <Card variant="elevated" style={styles.recommendCard}>
          <View style={styles.recommendCenter}>
            <SpeechLevelBadge 
              level={recommendation?.recommended_level || 'polite'} 
              size="large" 
            />
          </View>
          <Text style={styles.reasonText}>{recommendation?.reason_ko}</Text>
        </Card>

        {/* Example expressions */}
        <View style={styles.sectionHeader}>
          <CheckCircle size={20} color="#4CAF50" />
          <Text style={styles.sectionTitle}>이렇게 말해보세요</Text>
        </View>
        
        <Card variant="elevated" style={styles.exampleCard}>
          {/* Greetings */}
          <View style={styles.exampleSection}>
            <Text style={styles.exampleLabel}>인사</Text>
            <View style={styles.exampleList}>
              {recommendation?.example_expressions.greetings.slice(0, 3).map((exp, i) => (
                <View key={i} style={styles.exampleItem}>
                  <Text style={styles.exampleText}>{exp}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Questions */}
          <View style={styles.exampleSection}>
            <Text style={styles.exampleLabel}>질문</Text>
            <View style={styles.exampleList}>
              {recommendation?.example_expressions.questions.slice(0, 3).map((exp, i) => (
                <View key={i} style={styles.exampleItem}>
                  <Text style={styles.exampleText}>{exp}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* Responses */}
          <View style={styles.exampleSection}>
            <Text style={styles.exampleLabel}>대답</Text>
            <View style={styles.exampleList}>
              {recommendation?.example_expressions.responses.slice(0, 3).map((exp, i) => (
                <View key={i} style={styles.exampleItem}>
                  <Text style={styles.exampleText}>{exp}</Text>
                </View>
              ))}
            </View>
          </View>
        </Card>

        {/* Avoid expressions */}
        <View style={styles.sectionHeader}>
          <XCircle size={20} color="#E53935" />
          <Text style={styles.sectionTitle}>피해야 할 표현</Text>
        </View>
        
        <Card variant="elevated" style={styles.avoidCard}>
          {recommendation?.avoid_expressions.slice(0, 3).map((item, i) => (
            <View key={i} style={styles.avoidItem}>
              <Text style={styles.avoidWrong}>{item.wrong}</Text>
              <Text style={styles.avoidReason}>{item.reason}</Text>
            </View>
          ))}
        </Card>

        {/* Tips */}
        <View style={styles.sectionHeader}>
          <Lightbulb size={20} color="#F4A261" />
          <Text style={styles.sectionTitle}>팁</Text>
        </View>
        
        <Card variant="elevated" style={styles.tipsCard}>
          {recommendation?.tips.slice(0, 4).map((tip, i) => (
            <View key={i} style={styles.tipItem}>
              <View style={styles.tipBullet} />
              <Text style={styles.tipText}>{tip}</Text>
            </View>
          ))}
        </Card>

      </ScrollView>

      {/* Start chat button */}
      <View style={styles.footer}>
        <Button
          title="대화 시작하기"
          onPress={handleStartChat}
          showArrow
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  loading: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  loadingText: { marginTop: 12, fontSize: 14, color: '#6C6C80' },

  contextCard: { marginBottom: 24 },
  contextRow: { flexDirection: 'row', alignItems: 'center', gap: 16 },
  avatarIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  contextInfo: { flex: 1 },
  contextLabel: { fontSize: 11, color: '#B0B0C5', marginBottom: 4 },
  contextName: { fontSize: 20, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  contextSituationRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  contextSituation: { fontSize: 13, color: '#6C6C80' },

  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12, marginTop: 8 },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },

  recommendCard: { alignItems: 'center', marginBottom: 20 },
  recommendCenter: { marginBottom: 16 },
  reasonText: { fontSize: 14, color: '#6C6C80', textAlign: 'center', lineHeight: 20 },

  exampleCard: { marginBottom: 20 },
  exampleSection: { marginBottom: 16 },
  exampleLabel: { fontSize: 12, fontWeight: '600', color: '#6C3BFF', marginBottom: 8 },
  exampleList: { gap: 8 },
  exampleItem: {
    backgroundColor: '#F0EDFF',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 10,
  },
  exampleText: { fontSize: 14, color: '#1A1A2E' },

  avoidCard: { marginBottom: 20 },
  avoidItem: { marginBottom: 12 },
  avoidWrong: {
    fontSize: 14,
    color: '#E53935',
    fontWeight: '600',
    marginBottom: 4,
    textDecorationLine: 'line-through',
  },
  avoidReason: { fontSize: 12, color: '#6C6C80' },

  tipsCard: { marginBottom: 20 },
  tipItem: { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 8 },
  tipBullet: { 
    width: 6, 
    height: 6, 
    borderRadius: 3, 
    backgroundColor: '#6C3BFF', 
    marginTop: 6,
    marginRight: 10,
  },
  tipText: { flex: 1, fontSize: 14, color: '#1A1A2E', lineHeight: 20 },

  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});
