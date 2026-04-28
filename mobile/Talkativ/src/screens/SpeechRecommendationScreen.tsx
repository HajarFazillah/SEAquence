import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { MapPin, CheckCircle, XCircle, Lightbulb } from 'lucide-react-native';
import { Header, Card, Button, SpeechLevelBadge, Icon } from '../components';
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

// ── 말투 레벨별 정보 ──────────────────────────────────────────────────────────
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

const buildScreenFallbackRecommendation = (
  avatar: any,
  situation: any
): {
  recommended_level: 'formal' | 'polite' | 'informal';
  recommended_level_info: {
    name_ko: string;
    description: string;
    endings: string[];
  };
  reason_ko: string;
  example_expressions: ExampleExpression;
  avoid_expressions: AvoidExpression[];
  tips: string[];
} => {
  const storedLevel = avatar?.formality_from_user || avatar?.recommendedLevel;
  const fallbackLevel: 'formal' | 'polite' | 'informal' =
    storedLevel && LEVEL_INFO[storedLevel as keyof typeof LEVEL_INFO]
      ? storedLevel
      : ['professor', 'boss', 'ceo', 'client', 'doctor'].includes(avatar?.role)
      ? 'formal'
      : ['friend', 'close_friend', 'classmate', 'roommate', 'younger_sibling'].includes(avatar?.role)
      ? 'informal'
      : 'polite';

  const info = LEVEL_INFO[fallbackLevel];

  return {
    recommended_level: fallbackLevel,
    recommended_level_info: {
      name_ko: info.name,
      description: `${info.name}를 사용하세요.`,
      endings: info.endings.split(', '),
    },
    reason_ko: `${avatar?.name_ko || '상대방'}${situation?.name_ko ? `와 ${situation.name_ko} 상황에서` : '와의 대화에서'} 적절한 말투입니다.`,
    example_expressions: {
      greetings: info.examples.slice(0, 2),
      questions: [`${info.examples[0]}?`],
      responses: info.examples.slice(0, 2),
    },
    avoid_expressions: info.avoid.slice(0, 2).map(w => ({
      wrong: w,
      reason: `${info.name} 대화에서는 어색한 표현입니다.`,
    })),
    tips: info.tips,
  };
};

export default function SpeechRecommendationScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();
  const { avatar, situation } = route.params || {};

  const [loading, setLoading] = useState(true);
  const [recommendation, setRecommendation] = useState<{
    recommended_level: 'formal' | 'polite' | 'informal';
    recommended_level_info: {
      name_ko: string;
      description: string;
      endings: string[];
    };
    reason_ko: string;
    example_expressions: ExampleExpression;
    avoid_expressions: AvoidExpression[];
    tips: string[];
  } | null>(null);
  const safeRecommendation = recommendation || buildScreenFallbackRecommendation(avatar, situation);

  const loadRecommendation = useCallback(async () => {
    try {
      setLoading(true);

      const data = await apiService.getSpeechRecommendation(avatar || {}, situation);
      setRecommendation(data);

    } catch (error) {
      console.error('Failed to load recommendation:', error);
      setRecommendation(buildScreenFallbackRecommendation(avatar, situation));
    } finally {
      setLoading(false);
    }
  }, [avatar, situation]);

  useEffect(() => {
    loadRecommendation();
  }, [loadRecommendation]);

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
            <View style={[styles.avatarIcon, { backgroundColor: avatar?.avatarBg || avatar?.avatar_bg || '#FFB6C1' }]}>
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
              level={safeRecommendation.recommended_level}
              size="large"
            />
          </View>
          <Text style={styles.reasonText}>{safeRecommendation.reason_ko}</Text>
        </Card>

        {/* Example expressions */}
        <View style={styles.sectionHeader}>
          <CheckCircle size={20} color="#4CAF50" />
          <Text style={styles.sectionTitle}>이렇게 말해보세요</Text>
        </View>

        <Card variant="elevated" style={styles.exampleCard}>
          <View style={styles.exampleSection}>
            <Text style={styles.exampleLabel}>인사</Text>
            <View style={styles.exampleList}>
              {safeRecommendation.example_expressions.greetings.slice(0, 3).map((exp, i) => (
                <View key={i} style={styles.exampleItem}>
                  <Text style={styles.exampleText}>{exp}</Text>
                </View>
              ))}
            </View>
          </View>

          <View style={styles.exampleSection}>
            <Text style={styles.exampleLabel}>질문</Text>
            <View style={styles.exampleList}>
              {safeRecommendation.example_expressions.questions.slice(0, 3).map((exp, i) => (
                <View key={i} style={styles.exampleItem}>
                  <Text style={styles.exampleText}>{exp}</Text>
                </View>
              ))}
            </View>
          </View>

          <View style={styles.exampleSection}>
            <Text style={styles.exampleLabel}>대답</Text>
            <View style={styles.exampleList}>
              {safeRecommendation.example_expressions.responses.slice(0, 3).map((exp, i) => (
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
          {safeRecommendation.avoid_expressions.slice(0, 3).map((item, i) => (
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
          {safeRecommendation.tips.slice(0, 4).map((tip, i) => (
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
  safe:        { flex: 1, backgroundColor: '#F7F7FB' },
  content:     { paddingHorizontal: 20, paddingBottom: 100 },
  loading:     { flex: 1, alignItems: 'center', justifyContent: 'center' },
  loadingText: { marginTop: 12, fontSize: 14, color: '#6C6C80' },

  contextCard: { marginBottom: 24 },
  contextRow:  { flexDirection: 'row', alignItems: 'center', gap: 16 },
  avatarIcon:  { width: 64, height: 64, borderRadius: 32, alignItems: 'center', justifyContent: 'center' },
  contextInfo: { flex: 1 },
  contextLabel: { fontSize: 11, color: '#B0B0C5', marginBottom: 4 },
  contextName:  { fontSize: 20, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  contextSituationRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  contextSituation:    { fontSize: 13, color: '#6C6C80' },

  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12, marginTop: 8 },
  sectionTitle:  { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },

  recommendCard:   { alignItems: 'center', marginBottom: 20 },
  recommendCenter: { marginBottom: 16 },
  reasonText:      { fontSize: 14, color: '#6C6C80', textAlign: 'center', lineHeight: 20 },

  exampleCard:    { marginBottom: 20 },
  exampleSection: { marginBottom: 16 },
  exampleLabel:   { fontSize: 12, fontWeight: '600', color: '#6C3BFF', marginBottom: 8 },
  exampleList:    { gap: 8 },
  exampleItem:    { backgroundColor: '#F0EDFF', paddingHorizontal: 14, paddingVertical: 10, borderRadius: 10 },
  exampleText:    { fontSize: 14, color: '#1A1A2E' },

  avoidCard: { marginBottom: 20 },
  avoidItem: { marginBottom: 12 },
  avoidWrong: { fontSize: 14, color: '#E53935', fontWeight: '600', marginBottom: 4, textDecorationLine: 'line-through' },
  avoidReason: { fontSize: 12, color: '#6C6C80' },

  tipsCard: { marginBottom: 20 },
  tipItem:  { flexDirection: 'row', alignItems: 'flex-start', marginBottom: 8 },
  tipBullet: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#6C3BFF', marginTop: 6, marginRight: 10 },
  tipText:   { flex: 1, fontSize: 14, color: '#1A1A2E', lineHeight: 20 },

  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
});
