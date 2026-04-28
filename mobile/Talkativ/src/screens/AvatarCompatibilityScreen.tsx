import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator,} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Header, Card, Button, CompatibilityRing, StatusBadge, Tag, Icon } from '../components';
import { SYSTEM_AVATARS } from '../constants';
import { apiService, CompatibilityAvatarInput } from '../services/api';

interface CompatibilityData {
  avatar_id: string;
  score: number;
  chemistry_level: string;
  common_interests: string[];
  suggested_topics: string[];
  recommendation?: string;
}

const normalizeInterest = (value: string) => value.trim().toLowerCase();

const buildDeterministicFallback = (userInterests: string[]): CompatibilityData[] => {
  const normalizedUserInterests = userInterests.map(normalizeInterest);

  return SYSTEM_AVATARS.map((avatar) => {
    const sharedInterests = avatar.interests.filter((interest) =>
      normalizedUserInterests.some((userInterest) =>
        normalizeInterest(interest).includes(userInterest) || userInterest.includes(normalizeInterest(interest))
      )
    );

    const overlapRatio = userInterests.length > 0
      ? sharedInterests.length / Math.max(userInterests.length, avatar.interests.length, 1)
      : 0;

    const baseScore = 48 + Math.round(overlapRatio * 38);
    const interestBonus = Math.min(sharedInterests.length * 7, 21);
    const difficultyBonus = avatar.difficulty === 'easy' ? 8 : avatar.difficulty === 'medium' ? 4 : 0;
    const score = Math.max(42, Math.min(92, baseScore + interestBonus + difficultyBonus));

    return {
      avatar_id: avatar.id,
      score,
      chemistry_level: score >= 85 ? 'excellent' : score >= 70 ? 'good' : score >= 55 ? 'okay' : 'low',
      common_interests: sharedInterests,
      suggested_topics: sharedInterests.length > 0 ? sharedInterests.slice(0, 3) : avatar.interests.slice(0, 3),
      recommendation: sharedInterests.length > 0
        ? `공통 관심사 ${sharedInterests.length}개를 중심으로 대화를 시작하면 자연스러워요.`
        : `${avatar.name_ko}의 대표 관심사로 대화를 시작하면 어색함을 줄일 수 있어요.`,
    };
  }).sort((a, b) => b.score - a.score);
};

const SYSTEM_AVATAR_INPUTS: CompatibilityAvatarInput[] = SYSTEM_AVATARS.map((avatar) => ({
  id: avatar.id,
  name_ko: avatar.name_ko,
  role: avatar.role,
  difficulty: avatar.difficulty,
  interests: avatar.interests,
  dislikes: [],
  personality_traits: [],
}));

export default function AvatarCompatibilityScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const userInterests = useMemo(() => {
    const interests = route.params?.interests;
    return Array.isArray(interests) && interests.length > 0 ? interests : ['K-POP', '카페', '여행'];
  }, [route.params?.interests]);

  const [loading, setLoading] = useState(true);
  const [compatibilityData, setCompatibilityData] = useState<CompatibilityData[]>([]);
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);

  const loadCompatibility = useCallback(async () => {
    try {
      setLoading(true);
      const results = await apiService.batchCompatibility(userInterests, [], SYSTEM_AVATAR_INPUTS);
      setCompatibilityData(results.length > 0 ? results : buildDeterministicFallback(userInterests));
    } catch (error) {
      console.error('Failed to load compatibility:', error);
      setCompatibilityData(buildDeterministicFallback(userInterests));
    } finally {
      setLoading(false);
    }
  }, [userInterests]);

  useEffect(() => {
    loadCompatibility();
  }, [loadCompatibility]);

  const getAvatarById = (id: string) => {
    return SYSTEM_AVATARS.find((a) => a.id === id);
  };

  const getScoreExplanation = (score: number, commonInterestCount: number): string => {
    if (commonInterestCount > 0) {
      return `공통 관심사 ${commonInterestCount}개와 관계 난이도를 함께 반영한 점수예요.`;
    }
    if (score >= 70) {
      return '대화 주제를 넓게 잡아도 무난하게 이어질 가능성이 높아요.';
    }
    if (score >= 55) {
      return '첫 화제를 잘 고르면 편하게 대화를 시작할 수 있어요.';
    }
    return '공통점은 적지만, 추천 주제부터 시작하면 훨씬 수월해질 수 있어요.';
  };

  const getChemistryLabel = (score: number): { text: string; icon: string } => {
    if (score >= 85) return { text: '대화가 잘 통할 가능성이 높아요', icon: 'award' };
    if (score >= 70) return { text: '편하게 대화를 이어가기 좋아요', icon: 'heart' };
    if (score >= 55) return { text: '공통 주제를 잡으면 잘 풀려요', icon: 'handshake' };
    return { text: '첫 화제를 잘 고르면 충분히 괜찮아요', icon: 'target' };
  };

  const handleSelectAvatar = (avatarId: string) => {
    setSelectedAvatar(avatarId);
  };

  const handleNext = () => {
    if (!selectedAvatar) return;
    const avatar = getAvatarById(selectedAvatar);
    const compatibility = compatibilityData.find((c) => c.avatar_id === selectedAvatar);
    navigation.navigate('SituationSelection', { 
      avatar: { ...avatar, compatibility },
    });
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <Header title="아바타 궁합" showBack />
        <View style={styles.loading}>
          <ActivityIndicator size="large" color="#6C3BFF" />
          <Text style={styles.loadingText}>궁합 분석 중...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <Header title="아바타 궁합" showBack />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Your interests */}
        <Text style={styles.sectionTitle}>나의 관심사</Text>
        <View style={styles.interestTags}>
          {userInterests.map((interest: string, i: number) => (
            <Tag key={i} label={interest} selected variant="default" />
          ))}
        </View>

        {/* Compatibility list */}
        <Text style={styles.sectionTitle}>아바타별 궁합</Text>
        <Text style={styles.sectionSubtitle}>대화할 아바타를 선택하세요</Text>

        <View style={styles.avatarList}>
          {compatibilityData.map((item) => {
            const avatar = getAvatarById(item.avatar_id);
            if (!avatar) return null;

            const isSelected = selectedAvatar === item.avatar_id;
            const chemistry = getChemistryLabel(item.score);

            return (
              <Card
                key={item.avatar_id}
                variant={isSelected ? 'outlined' : 'elevated'}
                onPress={() => handleSelectAvatar(item.avatar_id)}
                style={[
                  styles.avatarCard,
                  isSelected && styles.avatarCardSelected,
                ]}
              >
                <View style={styles.avatarRow}>
                  {/* Avatar icon */}
                  <View style={[styles.avatarIcon, { backgroundColor: avatar.avatarBg }]}>
                    <Icon name={avatar.icon} size={28} color="#FFFFFF" />
                  </View>

                  {/* Info */}
                  <View style={styles.avatarInfo}>
                    <View style={styles.avatarNameRow}>
                      <Text style={styles.avatarName}>{avatar.name_ko}</Text>
                      <StatusBadge 
                        status={avatar.difficulty as 'easy' | 'medium' | 'hard'} 
                      />
                    </View>
                    <Text style={styles.avatarRole}>{avatar.description_ko}</Text>
                    
                    {/* Common interests */}
                    {item.common_interests.length > 0 && (
                      <View style={styles.commonInterests}>
                        <Text style={styles.commonLabel}>공통 관심사: </Text>
                        <Text style={styles.commonText}>
                          {item.common_interests.join(', ')}
                        </Text>
                      </View>
                    )}
                  </View>

                  {/* Compatibility ring */}
                  <View style={styles.ringColumn}>
                    <CompatibilityRing percentage={item.score} size={56} />
                    <Text style={styles.ringCaption}>
                      {getScoreExplanation(item.score, item.common_interests.length)}
                    </Text>
                  </View>
                </View>

                {/* Chemistry message */}
                <View style={styles.chemistryRow}>
                  <Icon name={chemistry.icon as any} size={16} color="#6C6C80" />
                  <Text style={styles.chemistryText}>{chemistry.text}</Text>
                </View>

                {item.recommendation ? (
                  <Text style={styles.recommendationText}>{item.recommendation}</Text>
                ) : null}

                {/* Suggested topics */}
                {isSelected && item.suggested_topics.length > 0 && (
                  <View style={styles.suggestedTopics}>
                    <Text style={styles.suggestedLabel}>추천 대화 주제</Text>
                    <View style={styles.topicTags}>
                      {item.suggested_topics.map((topic, i) => (
                        <Tag key={i} label={topic} variant="outline" />
                      ))}
                    </View>
                  </View>
                )}
              </Card>
            );
          })}
        </View>

      </ScrollView>

      {/* Next button */}
      <View style={styles.footer}>
        <Button
          title="다음"
          onPress={handleNext}
          showArrow
          disabled={!selectedAvatar}
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

  sectionTitle: { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginBottom: 8, marginTop: 16 },
  sectionSubtitle: { fontSize: 13, color: '#6C6C80', marginBottom: 16 },

  interestTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },

  avatarList: { gap: 14 },
  avatarCard: { borderColor: '#E2E2EC' },
  avatarCardSelected: { borderColor: '#6C3BFF', borderWidth: 2 },

  avatarRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 14 },
  avatarIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInfo: { flex: 1 },
  ringColumn: { alignItems: 'center', width: 92 },
  ringCaption: { marginTop: 8, fontSize: 10, lineHeight: 14, color: '#7A7A92', textAlign: 'center' },
  avatarNameRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 },
  avatarName: { fontSize: 17, fontWeight: '700', color: '#1A1A2E' },
  avatarRole: { fontSize: 12, color: '#6C6C80', marginBottom: 8 },

  commonInterests: { flexDirection: 'row', flexWrap: 'wrap' },
  commonLabel: { fontSize: 11, color: '#6C3BFF', fontWeight: '600' },
  commonText: { fontSize: 11, color: '#6C3BFF' },

  chemistryRow: { 
    flexDirection: 'row', 
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 12, 
    paddingTop: 12, 
    borderTopWidth: 1, 
    borderTopColor: '#F0F0F5',
  },
  chemistryText: { fontSize: 13, color: '#6C6C80' },
  recommendationText: { marginTop: 10, fontSize: 13, lineHeight: 19, color: '#484860' },

  suggestedTopics: { marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#F0F0F5' },
  suggestedLabel: { fontSize: 12, fontWeight: '600', color: '#1A1A2E', marginBottom: 8 },
  topicTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },

  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});
