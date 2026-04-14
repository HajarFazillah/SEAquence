import React from 'react';
import { View, Text, StyleSheet, ScrollView,} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { 
  TrendingUp, CheckCircle, AlertCircle, 
  BookOpen, MessageCircle, Target
} from 'lucide-react-native';
import { Header, Card, Button, ProgressBar, Icon, Tag } from '../components';

// Mock analytics data
const mockAnalytics = {
  speechAccuracy: 0.85,
  vocabularyScore: 0.72,
  naturalness: 0.78,
  improvements: [
    { type: 'good', text: '합쇼체를 잘 사용했어요' },
    { type: 'good', text: '존댓말 사용이 자연스러웠어요' },
    { type: 'improve', text: '"~요"로 끝나는 문장을 더 연습하세요' },
    { type: 'improve', text: '의문문 억양에 주의하세요' },
  ],
  learnedExpressions: [
    '어떻게 지내세요?',
    '좋은 하루 되세요',
    '감사합니다',
    '죄송합니다',
  ],
  suggestedTopics: ['일상 대화', '카페 주문', '자기소개'],
};

export default function AnalyticsScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { avatar, duration, rating } = route.params || {};

  const handleGoHome = () => {
    navigation.navigate('Main', { screen: 'Home' });
  };

  const handlePracticeAgain = () => {
    navigation.navigate('AvatarSelection');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="분석 결과" showBack={false} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Overall Score */}
        <Card variant="elevated" style={styles.overallCard}>
          <Text style={styles.overallLabel}>종합 점수</Text>
          <Text style={styles.overallScore}>
            {Math.round((mockAnalytics.speechAccuracy + mockAnalytics.vocabularyScore + mockAnalytics.naturalness) / 3 * 100)}점
          </Text>
          <Text style={styles.overallDesc}>
            {avatar?.name_ko || '아바타'}와 {duration || '5분'} 동안 대화했어요
          </Text>
        </Card>

        {/* Detailed Scores */}
        <Text style={styles.sectionTitle}>상세 점수</Text>
        <Card variant="elevated" style={styles.scoresCard}>
          <View style={styles.scoreItem}>
            <View style={styles.scoreHeader}>
              <MessageCircle size={18} color="#6C3BFF" />
              <Text style={styles.scoreLabel}>말투 정확도</Text>
              <Text style={styles.scoreValue}>{Math.round(mockAnalytics.speechAccuracy * 100)}%</Text>
            </View>
            <ProgressBar progress={mockAnalytics.speechAccuracy} color="#6C3BFF" />
          </View>

          <View style={styles.scoreItem}>
            <View style={styles.scoreHeader}>
              <BookOpen size={18} color="#4CAF50" />
              <Text style={styles.scoreLabel}>어휘력</Text>
              <Text style={styles.scoreValue}>{Math.round(mockAnalytics.vocabularyScore * 100)}%</Text>
            </View>
            <ProgressBar progress={mockAnalytics.vocabularyScore} color="#4CAF50" />
          </View>

          <View style={styles.scoreItem}>
            <View style={styles.scoreHeader}>
              <TrendingUp size={18} color="#F4A261" />
              <Text style={styles.scoreLabel}>자연스러움</Text>
              <Text style={styles.scoreValue}>{Math.round(mockAnalytics.naturalness * 100)}%</Text>
            </View>
            <ProgressBar progress={mockAnalytics.naturalness} color="#F4A261" />
          </View>
        </Card>

        {/* Improvements */}
        <Text style={styles.sectionTitle}>피드백</Text>
        <Card variant="elevated" style={styles.feedbackCard}>
          {mockAnalytics.improvements.map((item, i) => (
            <View key={i} style={styles.feedbackItem}>
              {item.type === 'good' ? (
                <CheckCircle size={18} color="#4CAF50" />
              ) : (
                <AlertCircle size={18} color="#F4A261" />
              )}
              <Text style={styles.feedbackText}>{item.text}</Text>
            </View>
          ))}
        </Card>

        {/* Learned Expressions */}
        <Text style={styles.sectionTitle}>배운 표현</Text>
        <Card variant="elevated" style={styles.expressionsCard}>
          {mockAnalytics.learnedExpressions.map((exp, i) => (
            <View key={i} style={styles.expressionItem}>
              <View style={styles.expressionBullet} />
              <Text style={styles.expressionText}>{exp}</Text>
            </View>
          ))}
        </Card>

        {/* Next Steps */}
        <Text style={styles.sectionTitle}>다음 추천</Text>
        <View style={styles.suggestedTags}>
          {mockAnalytics.suggestedTopics.map((topic, i) => (
            <Tag key={i} label={topic} variant="outline" />
          ))}
        </View>

      </ScrollView>

      {/* Footer Buttons */}
      <View style={styles.footer}>
        <Button
          title="홈으로"
          onPress={handleGoHome}
          variant="outline"
          style={styles.footerBtnOutline}
        />
        <Button
          title="다시 연습하기"
          onPress={handlePracticeAgain}
          style={styles.footerBtn}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 120 },

  // Overall
  overallCard: {
    alignItems: 'center',
    backgroundColor: '#6C3BFF',
    marginBottom: 24,
  },
  overallLabel: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 8,
  },
  overallScore: {
    fontSize: 48,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
  },
  overallDesc: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
  },

  // Section
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 12,
  },

  // Scores
  scoresCard: {
    marginBottom: 20,
  },
  scoreItem: {
    marginBottom: 16,
  },
  scoreHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  scoreLabel: {
    flex: 1,
    fontSize: 14,
    color: '#1A1A2E',
    marginLeft: 8,
  },
  scoreValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1A1A2E',
  },

  // Feedback
  feedbackCard: {
    marginBottom: 20,
  },
  feedbackItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 12,
  },
  feedbackText: {
    flex: 1,
    fontSize: 14,
    color: '#1A1A2E',
    lineHeight: 20,
  },

  // Expressions
  expressionsCard: {
    marginBottom: 20,
  },
  expressionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  expressionBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#6C3BFF',
    marginRight: 10,
  },
  expressionText: {
    fontSize: 14,
    color: '#1A1A2E',
  },

  // Suggested
  suggestedTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 20,
  },

  // Footer
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
    flexDirection: 'row',
    gap: 12,
  },
  footerBtnOutline: {
    flex: 1,
  },
  footerBtn: {
    flex: 1,
  },
});
