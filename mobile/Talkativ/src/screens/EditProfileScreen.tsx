import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity, Image, TextInput,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Camera, User, Sparkles } from 'lucide-react-native';
import { Header, Card, Button, InputField } from '../components';

const KOREAN_LEVELS = [
  { id: 'beginner', label: '초급', labelEn: 'Beginner' },
  { id: 'intermediate', label: '중급', labelEn: 'Intermediate' },
  { id: 'advanced', label: '고급', labelEn: 'Advanced' },
];

const GENDERS = [
  { id: 'male', label: '남성' },
  { id: 'female', label: '여성' },
  { id: 'other', label: '기타' },
];

// Mock user data
const mockUser = {
  name: 'Nunnalin',
  email: 'nunnalin@example.com',
  avatarUrl: 'https://i.pravatar.cc/100?img=47',
  age: '25',
  gender: 'female',
  koreanLevel: 'intermediate',
  memo: '저는 사회적 불안이 있어서 천천히 대화하고 싶어요. 실수해도 친절하게 대해주세요.',
};

export default function EditProfileScreen() {
  const navigation = useNavigation<any>();
  
  const [name, setName] = useState(mockUser.name);
  const [email, setEmail] = useState(mockUser.email);
  const [age, setAge] = useState(mockUser.age);
  const [gender, setGender] = useState(mockUser.gender);
  const [koreanLevel, setKoreanLevel] = useState(mockUser.koreanLevel);
  const [memo, setMemo] = useState(mockUser.memo);
  const [avatarUrl, setAvatarUrl] = useState(mockUser.avatarUrl);

  const handleSave = () => {
    const profileData = {
      name,
      email,
      age: parseInt(age, 10),
      gender,
      korean_level: koreanLevel,
      memo,
      // AI context
      ai_context: {
        user_description: memo,
        language_level: koreanLevel,
        age_group: parseInt(age, 10) < 20 ? 'teen' : parseInt(age, 10) < 30 ? '20s' : parseInt(age, 10) < 40 ? '30s' : 'adult',
      },
    };
    console.log('Saving profile:', profileData);
    navigation.goBack();
  };

  const handleChangePhoto = () => {
    console.log('Change photo');
  };

  return (
    <SafeAreaView style={styles.safe}>
      <Header title="프로필 수정" />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Avatar */}
        <View style={styles.avatarSection}>
          <View style={styles.avatarContainer}>
            {avatarUrl ? (
              <Image source={{ uri: avatarUrl }} style={styles.avatar} />
            ) : (
              <View style={styles.avatarPlaceholder}>
                <User size={40} color="#B0B0C5" />
              </View>
            )}
            <TouchableOpacity style={styles.cameraButton} onPress={handleChangePhoto}>
              <Camera size={18} color="#FFFFFF" />
            </TouchableOpacity>
          </View>
          <TouchableOpacity onPress={handleChangePhoto}>
            <Text style={styles.changePhotoText}>사진 변경</Text>
          </TouchableOpacity>
        </View>

        {/* Basic Info */}
        <Card variant="elevated" style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>기본 정보</Text>
          
          <InputField
            label="이름"
            value={name}
            onChangeText={setName}
            placeholder="이름을 입력하세요"
          />
          
          <InputField
            label="이메일"
            value={email}
            onChangeText={setEmail}
            placeholder="이메일을 입력하세요"
            keyboardType="email-address"
          />

          <InputField
            label="나이"
            value={age}
            onChangeText={setAge}
            placeholder="나이를 입력하세요"
            keyboardType="numeric"
          />

          <Text style={styles.fieldLabel}>성별</Text>
          <View style={styles.genderRow}>
            {GENDERS.map((g) => (
              <TouchableOpacity
                key={g.id}
                style={[
                  styles.genderButton,
                  gender === g.id && styles.genderButtonActive,
                ]}
                onPress={() => setGender(g.id)}
              >
                <Text style={[
                  styles.genderText,
                  gender === g.id && styles.genderTextActive,
                ]}>
                  {g.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </Card>

        {/* Korean Level */}
        <Card variant="elevated" style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>한국어 수준</Text>
          <Text style={styles.sectionSubtitle}>
            현재 한국어 실력에 맞는 수준을 선택하세요
          </Text>
          
          <View style={styles.levelGrid}>
            {KOREAN_LEVELS.map((level) => (
              <TouchableOpacity
                key={level.id}
                style={[
                  styles.levelCard,
                  koreanLevel === level.id && styles.levelCardActive,
                ]}
                onPress={() => setKoreanLevel(level.id)}
              >
                <Text style={[
                  styles.levelLabel,
                  koreanLevel === level.id && styles.levelLabelActive,
                ]}>
                  {level.label}
                </Text>
                <Text style={[
                  styles.levelLabelEn,
                  koreanLevel === level.id && styles.levelLabelEnActive,
                ]}>
                  {level.labelEn}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </Card>

        {/* Memo for AI */}
        <Card variant="elevated" style={styles.sectionCard}>
          <Text style={styles.sectionTitle}>메모 (AI 참고용)</Text>
          <Text style={styles.sectionSubtitle}>
            AI가 당신을 더 잘 이해할 수 있도록 자유롭게 적어주세요
          </Text>
          
          <TextInput
            style={styles.memoInput}
            value={memo}
            onChangeText={setMemo}
            placeholder="예: 저는 사회적 불안이 있어서 천천히 대화하고 싶어요..."
            placeholderTextColor="#B0B0C5"
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />

          <View style={styles.memoTips}>
            <Sparkles size={14} color="#6C3BFF" />
            <Text style={styles.memoTipsText}>
              성격, 학습 목표, 대화 스타일 선호도, 특별한 요청 등을 적어주세요
            </Text>
          </View>
        </Card>

        {/* Danger Zone */}
        <Card variant="outlined" style={styles.dangerCard}>
          <Text style={styles.dangerTitle}>계정 관리</Text>
          <TouchableOpacity style={styles.dangerButton}>
            <Text style={styles.dangerButtonText}>계정 삭제</Text>
          </TouchableOpacity>
        </Card>

      </ScrollView>

      {/* Save Button */}
      <View style={styles.footer}>
        <Button
          title="저장하기"
          onPress={handleSave}
          disabled={!name.trim() || !age.trim()}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  // Avatar
  avatarSection: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  avatarContainer: {
    position: 'relative',
    marginBottom: 12,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#E8E8F0',
  },
  avatarPlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#E8E8F0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cameraButton: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#6C3BFF',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  changePhotoText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6C3BFF',
  },

  // Field
  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1A1A2E',
    marginBottom: 10,
    marginTop: 8,
  },

  // Gender
  genderRow: {
    flexDirection: 'row',
    gap: 10,
  },
  genderButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: '#F5F5FA',
    alignItems: 'center',
  },
  genderButtonActive: {
    backgroundColor: '#6C3BFF',
  },
  genderText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6C6C80',
  },
  genderTextActive: {
    color: '#FFFFFF',
  },

  // Section Card
  sectionCard: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 16,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: '#6C6C80',
    marginTop: -8,
    marginBottom: 16,
  },

  // Level Grid
  levelGrid: {
    flexDirection: 'row',
    gap: 10,
  },
  levelCard: {
    flex: 1,
    backgroundColor: '#F7F7FB',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  levelCardActive: {
    backgroundColor: '#F0EDFF',
    borderColor: '#6C3BFF',
  },
  levelLabel: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 2,
  },
  levelLabelActive: {
    color: '#6C3BFF',
  },
  levelLabelEn: {
    fontSize: 11,
    color: '#6C6C80',
  },
  levelLabelEnActive: {
    color: '#6C3BFF',
  },

  // Memo
  memoInput: {
    backgroundColor: '#F5F5FA',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 14,
    color: '#1A1A2E',
    minHeight: 100,
    lineHeight: 20,
  },
  memoTips: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginTop: 12,
    backgroundColor: '#F0EDFF',
    padding: 12,
    borderRadius: 10,
  },
  memoTipsText: {
    flex: 1,
    fontSize: 12,
    color: '#6C3BFF',
    lineHeight: 18,
  },

  // Danger Zone
  dangerCard: {
    borderColor: '#FFCDD2',
    marginBottom: 16,
  },
  dangerTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#E53935',
    marginBottom: 12,
  },
  dangerButton: {
    backgroundColor: '#FFEBEE',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  dangerButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#E53935',
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
