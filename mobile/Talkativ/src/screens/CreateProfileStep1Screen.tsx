import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { User, Users, UserCircle } from 'lucide-react-native';
import { Header, Button, InputField } from '../components';

const GENDERS = [
  { id: 'male', label: '남성', labelEn: 'Male', icon: User },
  { id: 'female', label: '여성', labelEn: 'Female', icon: UserCircle },
  { id: 'other', label: '기타', labelEn: 'Other', icon: Users },
];

const KOREAN_LEVELS = [
  { id: 'beginner', label: '초급', labelEn: 'Beginner', desc: '한글을 읽을 수 있고 기본 인사를 할 수 있어요' },
  { id: 'intermediate', label: '중급', labelEn: 'Intermediate', desc: '일상 대화가 가능하고 간단한 문장을 만들 수 있어요' },
  { id: 'advanced', label: '고급', labelEn: 'Advanced', desc: '복잡한 주제도 대화할 수 있고 뉘앙스를 이해해요' },
];

export default function CreateProfileStep1Screen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();                    // ← FIXED: added useRoute
  const { email, password } = route.params || {};   // ← now works correctly

  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [koreanLevel, setKoreanLevel] = useState('');

  const isValid = name.trim().length > 0 && age.trim().length > 0 && gender && koreanLevel;

  const handleNext = () => {
    navigation.navigate('CreateProfileStep2', {
      email,           // ← FIXED: passing email forward
      password,        // ← FIXED: passing password forward
      name: name.trim(),
      age: age.trim(),
      gender,
      koreanLevel,
    });
  };

  return (
    <SafeAreaView style={styles.safe}>
      <Header title="프로필 만들기" subtitle="1/2" />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Text style={styles.title}>기본 정보를 알려주세요</Text>
          <Text style={styles.subtitle}>
            AI가 당신에게 맞는 대화를 준비하는 데 도움이 됩니다
          </Text>

          <InputField
            label="이름 / 닉네임 *"
            value={name}
            onChangeText={setName}
            placeholder="어떻게 불러드릴까요?"
          />

          <InputField
            label="나이 *"
            value={age}
            onChangeText={setAge}
            placeholder="예: 25"
            keyboardType="numeric"
          />

          <Text style={styles.fieldLabel}>성별 *</Text>
          <View style={styles.genderRow}>
            {GENDERS.map((g) => (
              <TouchableOpacity
                key={g.id}
                style={[styles.genderCard, gender === g.id && styles.genderCardActive]}
                onPress={() => setGender(g.id)}
              >
                <g.icon size={24} color={gender === g.id ? '#FFFFFF' : '#6C6C80'} />
                <Text style={[styles.genderLabel, gender === g.id && styles.genderLabelActive]}>
                  {g.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.fieldLabel}>한국어 수준 *</Text>
          <View style={styles.levelList}>
            {KOREAN_LEVELS.map((level) => (
              <TouchableOpacity
                key={level.id}
                style={[styles.levelCard, koreanLevel === level.id && styles.levelCardActive]}
                onPress={() => setKoreanLevel(level.id)}
              >
                <View style={styles.levelHeader}>
                  <Text style={[styles.levelLabel, koreanLevel === level.id && styles.levelLabelActive]}>
                    {level.label}
                  </Text>
                  <Text style={[styles.levelLabelEn, koreanLevel === level.id && styles.levelLabelEnActive]}>
                    {level.labelEn}
                  </Text>
                </View>
                <Text style={[styles.levelDesc, koreanLevel === level.id && styles.levelDescActive]}>
                  {level.desc}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>

        <View style={styles.footer}>
          <Button title="다음" onPress={handleNext} disabled={!isValid} showArrow />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },
  title: { fontSize: 22, fontWeight: '700', color: '#1A1A2E', marginBottom: 8 },
  subtitle: { fontSize: 14, color: '#6C6C80', marginBottom: 28, lineHeight: 20 },
  fieldLabel: { fontSize: 13, fontWeight: '600', color: '#1A1A2E', marginBottom: 12, marginTop: 8 },
  genderRow: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  genderCard: {
    flex: 1, alignItems: 'center', paddingVertical: 16,
    backgroundColor: '#FFFFFF', borderRadius: 14, borderWidth: 2, borderColor: '#E2E2EC', gap: 8,
  },
  genderCardActive: { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  genderLabel: { fontSize: 14, fontWeight: '600', color: '#6C6C80' },
  genderLabelActive: { color: '#FFFFFF' },
  levelList: { gap: 12 },
  levelCard: {
    backgroundColor: '#FFFFFF', borderRadius: 14, padding: 16, borderWidth: 2, borderColor: '#E2E2EC',
  },
  levelCardActive: { borderColor: '#6C3BFF', backgroundColor: '#F8F6FF' },
  levelHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 6 },
  levelLabel: { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  levelLabelActive: { color: '#6C3BFF' },
  levelLabelEn: { fontSize: 13, color: '#B0B0C5' },
  levelLabelEnActive: { color: '#6C3BFF' },
  levelDesc: { fontSize: 13, color: '#6C6C80', lineHeight: 18 },
  levelDescActive: { color: '#6C3BFF' },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
});