import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity, TextInput, KeyboardAvoidingView, Platform, Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Heart, ThumbsDown, Plus, Sparkles, MessageSquare } from 'lucide-react-native';
import { Header, Card, Button, Tag } from '../components';
import { registerUser } from '../services/apiAuth';

const INTEREST_OPTIONS = [
  'K-POP', '영화', '드라마', '음악', '독서', '여행', '카페', '음식',
  '운동', '게임', '패션', '사진', '요리', '미술', '역사', '과학',
  '비즈니스', '기술', '경제', '스포츠', '자기계발', '애니메이션',
];

const DISLIKE_OPTIONS = [
  '정치', '종교', '논쟁', '스포츠', '연예인 가십', '학업 스트레스',
  '취업 압박', '결혼/연애 압박', '외모 이야기', '돈 이야기',
];

export default function CreateProfileStep2Screen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  // ← FIXED: added email + password from params
  const { name, age, gender, koreanLevel, email, password } = route.params || {};

  const [interests, setInterests] = useState<string[]>([]);
  const [dislikes, setDislikes] = useState<string[]>([]);
  const [customInterest, setCustomInterest] = useState('');
  const [customDislike, setCustomDislike] = useState('');
  const [memo, setMemo] = useState('');

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
    if (trimmed && !interests.includes(trimmed)) {
      setInterests([...interests, trimmed]);
      setCustomInterest('');
    }
  };

  const addCustomDislike = () => {
    const trimmed = customDislike.trim();
    if (trimmed && !dislikes.includes(trimmed)) {
      setDislikes([...dislikes, trimmed]);
      setCustomDislike('');
    }
  };

  const isValid = interests.length > 0;

  // ← FIXED: now calls backend registerUser
  const handleComplete = async () => {
    try {
      await registerUser(name, email, password);
      navigation.navigate('Main');
    } catch (error: any) {
      Alert.alert('Registration Failed', error.message);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <Header title="프로필 만들기" subtitle="2/2" />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.title}>관심사와 메모를 추가해주세요</Text>
          <Text style={styles.subtitle}>
            AI가 당신의 관심사에 맞는 대화 주제를 준비합니다
          </Text>

          {/* Interests Section */}
          <Card variant="elevated" style={styles.sectionCard}>
            <View style={styles.sectionHeader}>
              <Heart size={20} color="#E53935" />
              <Text style={styles.sectionTitle}>관심사 *</Text>
              <View style={styles.countBadge}>
                <Text style={styles.countText}>{interests.length}</Text>
              </View>
            </View>
            <Text style={styles.sectionHint}>좋아하는 주제를 선택하세요 (최소 1개)</Text>
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
            <View style={styles.customInputRow}>
              <TextInput
                style={styles.customInput}
                value={customInterest}
                onChangeText={setCustomInterest}
                placeholder="직접 입력..."
                placeholderTextColor="#B0B0C5"
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
            <Text style={styles.sectionHint}>대화에서 피하고 싶은 주제를 선택하세요 (선택사항)</Text>
            <View style={styles.tagGrid}>
              {DISLIKE_OPTIONS.map((item) => (
                <Tag
                  key={item}
                  label={item}
                  selected={dislikes.includes(item)}
                  onPress={() => toggleDislike(item)}
                  variant="outline"
                />
              ))}
            </View>
            <View style={styles.customInputRow}>
              <TextInput
                style={styles.customInput}
                value={customDislike}
                onChangeText={setCustomDislike}
                placeholder="직접 입력..."
                placeholderTextColor="#B0B0C5"
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
          </Card>

          {/* Memo Section */}
          <Card variant="elevated" style={styles.sectionCard}>
            <View style={styles.sectionHeader}>
              <MessageSquare size={20} color="#6C3BFF" />
              <Text style={styles.sectionTitle}>메모 (AI 참고용)</Text>
            </View>
            <Text style={styles.sectionHint}>
              AI가 당신을 더 잘 이해할 수 있도록 자유롭게 적어주세요
            </Text>
            <TextInput
              style={styles.memoInput}
              value={memo}
              onChangeText={setMemo}
              placeholder="예: 저는 사회적 불안이 있어서 천천히 대화하고 싶어요. 실수해도 친절하게 대해주세요."
              placeholderTextColor="#B0B0C5"
              multiline
              numberOfLines={4}
              textAlignVertical="top"
            />
            <View style={styles.memoTips}>
              <Sparkles size={14} color="#6C3BFF" />
              <Text style={styles.memoTipsText}>
                작성 팁: 성격, 학습 목표, 대화 스타일 선호도 등을 적어주세요
              </Text>
            </View>
          </Card>

          {/* Preview */}
          <Card variant="outlined" style={styles.previewCard}>
            <Text style={styles.previewTitle}>프로필 요약</Text>
            <View style={styles.previewRow}>
              <Text style={styles.previewLabel}>이름:</Text>
              <Text style={styles.previewValue}>{name}</Text>
            </View>
            <View style={styles.previewRow}>
              <Text style={styles.previewLabel}>나이:</Text>
              <Text style={styles.previewValue}>{age}세</Text>
            </View>
            <View style={styles.previewRow}>
              <Text style={styles.previewLabel}>한국어 수준:</Text>
              <Text style={styles.previewValue}>
                {koreanLevel === 'beginner' ? '초급' : koreanLevel === 'intermediate' ? '중급' : '고급'}
              </Text>
            </View>
            <View style={styles.previewRow}>
              <Text style={styles.previewLabel}>관심사:</Text>
              <Text style={styles.previewValue}>
                {interests.slice(0, 3).join(', ')}{interests.length > 3 ? ` 외 ${interests.length - 3}개` : ''}
              </Text>
            </View>
          </Card>

        </ScrollView>

        <View style={styles.footer}>
          <Button title="완료" onPress={handleComplete} disabled={!isValid} />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },
  title: { fontSize: 22, fontWeight: '700', color: '#1A1A2E', marginBottom: 8 },
  subtitle: { fontSize: 14, color: '#6C6C80', marginBottom: 24, lineHeight: 20 },
  sectionCard: { marginBottom: 16 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  sectionTitle: { flex: 1, fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  sectionHint: { fontSize: 13, color: '#6C6C80', marginBottom: 14, lineHeight: 18 },
  countBadge: { backgroundColor: '#FFEBEE', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  countText: { fontSize: 13, fontWeight: '600', color: '#E53935' },
  countBadgeGray: { backgroundColor: '#E2E2EC', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  countTextGray: { fontSize: 13, fontWeight: '600', color: '#6C6C80' },
  tagGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  customInputRow: { flexDirection: 'row', gap: 10 },
  customInput: {
    flex: 1, backgroundColor: '#F5F5FA', borderRadius: 12,
    paddingHorizontal: 16, paddingVertical: 12, fontSize: 14, color: '#1A1A2E',
  },
  addButton: { width: 48, height: 48, borderRadius: 12, backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center' },
  addButtonGray: { backgroundColor: '#6C6C80' },
  addButtonDisabled: { opacity: 0.5 },
  memoInput: {
    backgroundColor: '#F5F5FA', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14,
    fontSize: 14, color: '#1A1A2E', minHeight: 100, lineHeight: 20,
  },
  memoTips: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginTop: 12, backgroundColor: '#F0EDFF', padding: 12, borderRadius: 10 },
  memoTipsText: { flex: 1, fontSize: 12, color: '#6C3BFF', lineHeight: 18 },
  previewCard: { marginBottom: 20, borderColor: '#6C3BFF' },
  previewTitle: { fontSize: 14, fontWeight: '700', color: '#6C3BFF', marginBottom: 12 },
  previewRow: { flexDirection: 'row', marginBottom: 8 },
  previewLabel: { width: 80, fontSize: 13, color: '#6C6C80' },
  previewValue: { flex: 1, fontSize: 13, color: '#1A1A2E', fontWeight: '500' },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
});