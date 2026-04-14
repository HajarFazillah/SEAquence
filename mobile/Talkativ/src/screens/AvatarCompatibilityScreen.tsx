import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator,} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Header, Card, Button, CompatibilityRing, StatusBadge, Tag, Icon } from '../components';
import { SYSTEM_AVATARS } from '../constants';
import { apiService } from '../services/api';
import { getMyAvatars, createAvatar, updateAvatar, deleteAvatar, UserAvatar } from '../services/apiUser';

interface CompatibilityData {
  avatar_id: string;
  score: number;
  chemistry_level: string;
  common_interests: string[];
  suggested_topics: string[];
}

export default function AvatarCompatibilityScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const userInterests = route.params?.interests || ['K-POP', '카페', '여행'];

  const [loading, setLoading] = useState(true);
  const [compatibilityData, setCompatibilityData] = useState<CompatibilityData[]>([]);
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);

  useEffect(() => {
    loadCompatibility();
  }, []);

  const loadCompatibility = async () => {
    try {
      setLoading(true);
      const results = await apiService.batchCompatibility(userInterests, []);
      setCompatibilityData(results);
    } catch (error) {
      console.error('Failed to load compatibility:', error);
      // Use mock data as fallback
      const mockData = SYSTEM_AVATARS.map((avatar) => ({
        avatar_id: avatar.id,
        score: Math.floor(Math.random() * 40) + 60,
        chemistry_level: 'good',
        common_interests: avatar.interests.filter((i) => 
          userInterests.some((ui: string) => 
            i.toLowerCase().includes(ui.toLowerCase()) || 
            ui.toLowerCase().includes(i.toLowerCase())
          )
        ),
        suggested_topics: avatar.interests.slice(0, 3),
      }));
      setCompatibilityData(mockData.sort((a, b) => b.score - a.score));
    } finally {
      setLoading(false);
    }
  };

  const getAvatarById = (id: string) => {
    return SYSTEM_AVATARS.find((a) => a.id === id);
  };

  const getChemistryLabel = (score: number): { text: string; icon: string } => {
    if (score >= 80) return { text: '최고의 궁합!', icon: 'award' };
    if (score >= 60) return { text: '좋은 궁합', icon: 'heart' };
    if (score >= 40) return { text: '보통 궁합', icon: 'handshake' };
    return { text: '도전해보세요', icon: 'target' };
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
                  <CompatibilityRing percentage={item.score} size={56} />
                </View>

                {/* Chemistry message */}
                <View style={styles.chemistryRow}>
                  <Icon name={chemistry.icon as any} size={16} color="#6C6C80" />
                  <Text style={styles.chemistryText}>{chemistry.text}</Text>
                </View>

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
