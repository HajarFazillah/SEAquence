import React, { useState } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, TextInput, TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Heart, ThumbsDown, Plus, X, Sparkles } from 'lucide-react-native';
import { Header, Card, Button, Tag } from '../components';

const INTEREST_OPTIONS = [
  'K-POP', '영화', '드라마', '음악', '독서', '여행', '카페', '음식',
  '운동', '게임', '패션', '사진', '요리', '미술', '역사', '과학',
  '비즈니스', '기술', '경제', '스포츠', '자기계발', '애니메이션',
];

export default function EditInterestsScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  
  const [interests, setInterests] = useState<string[]>(route.params?.interests || []);
  const [dislikes, setDislikes] = useState<string[]>(route.params?.dislikes || []);
  
  // Custom input states
  const [customInterest, setCustomInterest] = useState('');
  const [customDislike, setCustomDislike] = useState('');
  
  // Track custom added items
  const [customInterests, setCustomInterests] = useState<string[]>([]);
  const [customDislikes, setCustomDislikes] = useState<string[]>([]);

  const toggleInterest = (item: string) => {
    if (interests.includes(item)) {
      setInterests(interests.filter((i) => i !== item));
    } else {
      setDislikes(dislikes.filter((i) => i !== item));
      setInterests([...interests, item]);
    }
  };

  const toggleDislike = (item: string) => {
    if (dislikes.includes(item)) {
      setDislikes(dislikes.filter((i) => i !== item));
    } else {
      setInterests(interests.filter((i) => i !== item));
      setDislikes([...dislikes, item]);
    }
  };

  const addCustomInterest = () => {
    const trimmed = customInterest.trim();
    if (trimmed && !interests.includes(trimmed) && !INTEREST_OPTIONS.includes(trimmed)) {
      setInterests([...interests, trimmed]);
      setCustomInterests([...customInterests, trimmed]);
      setCustomInterest('');
    }
  };

  const addCustomDislike = () => {
    const trimmed = customDislike.trim();
    if (trimmed && !dislikes.includes(trimmed) && !INTEREST_OPTIONS.includes(trimmed)) {
      setDislikes([...dislikes, trimmed]);
      setCustomDislikes([...customDislikes, trimmed]);
      setCustomDislike('');
    }
  };

  const removeCustomInterest = (item: string) => {
    setInterests(interests.filter((i) => i !== item));
    setCustomInterests(customInterests.filter((i) => i !== item));
  };

  const removeCustomDislike = (item: string) => {
    setDislikes(dislikes.filter((i) => i !== item));
    setCustomDislikes(customDislikes.filter((i) => i !== item));
  };

  const handleSave = () => {
    // TODO: Save to API - custom keywords will be analyzed by LLM
    console.log('Saving:', { 
      interests, 
      dislikes,
      customInterests,
      customDislikes,
    });
    navigation.goBack();
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="관심사 수정" />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* AI Analysis Info */}
        <Card variant="elevated" style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Sparkles size={20} color="#6C3BFF" />
            <Text style={styles.infoText}>
              직접 입력한 키워드는 AI가 비슷한 주제를 분석하여 대화에 반영합니다.
            </Text>
          </View>
        </Card>

        {/* Interests Section */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <Heart size={20} color="#E53935" />
            <Text style={styles.sectionTitle}>관심사</Text>
            <View style={styles.countBadge}>
              <Text style={styles.countText}>{interests.length}</Text>
            </View>
          </View>
          <Text style={styles.sectionSubtitle}>
            좋아하는 주제를 선택하거나 직접 입력하세요
          </Text>
          
          {/* Preset tags */}
          <View style={styles.tagGrid}>
            {INTEREST_OPTIONS.map((item) => (
              <Tag
                key={item}
                label={item}
                selected={interests.includes(item)}
                onPress={() => toggleInterest(item)}
              />
            ))}
          </View>

          {/* Custom input */}
          <View style={styles.customInputRow}>
            <TextInput
              style={styles.customInput}
              value={customInterest}
              onChangeText={setCustomInterest}
              placeholder="직접 입력 (예: 보드게임, 재즈)"
              placeholderTextColor="#B0B0C5"
              returnKeyType="done"
              onSubmitEditing={addCustomInterest}
            />
            <TouchableOpacity 
              style={[styles.addButton, !customInterest.trim() && styles.addButtonDisabled]}
              onPress={addCustomInterest}
              disabled={!customInterest.trim()}
            >
              <Plus size={20} color="#FFFFFF" />
            </TouchableOpacity>
          </View>

          {/* Custom added interests */}
          {customInterests.length > 0 && (
            <View style={styles.customTagsSection}>
              <Text style={styles.customTagsLabel}>직접 추가한 관심사:</Text>
              <View style={styles.customTagsRow}>
                {customInterests.map((item) => (
                  <View key={item} style={styles.customTag}>
                    <Text style={styles.customTagText}>{item}</Text>
                    <TouchableOpacity onPress={() => removeCustomInterest(item)}>
                      <X size={14} color="#6C3BFF" />
                    </TouchableOpacity>
                  </View>
                ))}
              </View>
            </View>
          )}
        </Card>

        {/* Dislikes Section */}
        <Card variant="elevated" style={styles.sectionCard}>
          <View style={styles.sectionHeader}>
            <ThumbsDown size={20} color="#6C6C80" />
            <Text style={styles.sectionTitle}>피하고 싶은 주제</Text>
            <View style={styles.countBadgeGray}>
              <Text style={styles.countTextGray}>{dislikes.length}</Text>
            </View>
          </View>
          <Text style={styles.sectionSubtitle}>
            대화에서 피하고 싶은 주제를 선택하거나 직접 입력하세요
          </Text>
          
          {/* Preset tags (excluding selected interests) */}
          <View style={styles.tagGrid}>
            {INTEREST_OPTIONS.filter((i) => !interests.includes(i)).map((item) => (
              <Tag
                key={item}
                label={item}
                selected={dislikes.includes(item)}
                onPress={() => toggleDislike(item)}
                variant="outline"
              />
            ))}
          </View>

          {/* Custom input */}
          <View style={styles.customInputRow}>
            <TextInput
              style={styles.customInput}
              value={customDislike}
              onChangeText={setCustomDislike}
              placeholder="직접 입력 (예: 정치, 종교)"
              placeholderTextColor="#B0B0C5"
              returnKeyType="done"
              onSubmitEditing={addCustomDislike}
            />
            <TouchableOpacity 
              style={[styles.addButton, styles.addButtonGray, !customDislike.trim() && styles.addButtonDisabled]}
              onPress={addCustomDislike}
              disabled={!customDislike.trim()}
            >
              <Plus size={20} color="#FFFFFF" />
            </TouchableOpacity>
          </View>

          {/* Custom added dislikes */}
          {customDislikes.length > 0 && (
            <View style={styles.customTagsSection}>
              <Text style={styles.customTagsLabelGray}>직접 추가한 주제:</Text>
              <View style={styles.customTagsRow}>
                {customDislikes.map((item) => (
                  <View key={item} style={[styles.customTag, styles.customTagGray]}>
                    <Text style={[styles.customTagText, styles.customTagTextGray]}>{item}</Text>
                    <TouchableOpacity onPress={() => removeCustomDislike(item)}>
                      <X size={14} color="#6C6C80" />
                    </TouchableOpacity>
                  </View>
                ))}
              </View>
            </View>
          )}
        </Card>

      </ScrollView>

      {/* Save Button */}
      <View style={styles.footer}>
        <Button
          title="저장하기"
          onPress={handleSave}
          disabled={interests.length === 0}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  // Info Card
  infoCard: {
    backgroundColor: '#F0EDFF',
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#6C3BFF',
    lineHeight: 18,
  },

  // Section
  sectionCard: {
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A2E',
    flex: 1,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#6C6C80',
    marginBottom: 16,
    lineHeight: 18,
  },
  countBadge: {
    backgroundColor: '#FFEBEE',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  countText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#E53935',
  },
  countBadgeGray: {
    backgroundColor: '#E2E2EC',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  countTextGray: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6C6C80',
  },

  // Tags
  tagGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },

  // Custom Input
  customInputRow: {
    flexDirection: 'row',
    gap: 10,
  },
  customInput: {
    flex: 1,
    backgroundColor: '#F5F5FA',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 14,
    color: '#1A1A2E',
  },
  addButton: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#6C3BFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  addButtonGray: {
    backgroundColor: '#6C6C80',
  },
  addButtonDisabled: {
    opacity: 0.5,
  },

  // Custom Tags Section
  customTagsSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F5',
  },
  customTagsLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C3BFF',
    marginBottom: 8,
  },
  customTagsLabelGray: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C6C80',
    marginBottom: 8,
  },
  customTagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  customTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#F0EDFF',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
  },
  customTagGray: {
    backgroundColor: '#E2E2EC',
  },
  customTagText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#6C3BFF',
  },
  customTagTextGray: {
    color: '#6C6C80',
  },

  // Footer
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});
