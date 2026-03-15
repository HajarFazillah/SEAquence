import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity, KeyboardAvoidingView, Platform,
  TextInput, ActivityIndicator,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { 
  ChevronLeft, Check, User, Users, 
  GraduationCap, Briefcase, Building2, Plus, X, Sparkles,
} from 'lucide-react-native';
import { Header, Card, Button, InputField, Tag, Icon } from '../components';
import { AVATAR_COLORS, SPEECH_LEVELS } from '../constants';

interface AvatarFormData {
  name_ko: string;
  name_en: string;
  age: string;
  gender: 'male' | 'female' | 'other';
  avatarType: 'fictional' | 'real'; // 가상 인물 vs 실제 인물
  role: string; // expanded roles
  relationship_description: string;
  personality_traits: string[];
  speaking_style: string;
  interests: string[];
  dislikes: string[];
  avatarBg: string;
  icon: string;
  difficulty: 'easy' | 'medium' | 'hard';
  memo: string; // AI context memo
  description: string; // 아바타 관련 설명 (descriptive prompt for AI)
}

const STEPS = [
  { id: 1, title: '기본 정보', subtitle: 'Basic Info' },
  { id: 2, title: '관계 설정', subtitle: 'Relationship' },
  { id: 3, title: '성격 & 관심사', subtitle: 'Personality' },
  { id: 4, title: '말투 확인', subtitle: 'Speech Level' },
];

const ROLES = [
  // Casual relationships
  { id: 'friend', label: '친구', labelEn: 'Friend', icon: Users, color: '#6C3BFF', speechToUser: 'informal', speechFromUser: 'informal' },
  { id: 'close_friend', label: '절친', labelEn: 'Best Friend', icon: Users, color: '#E91E63', speechToUser: 'informal', speechFromUser: 'informal' },
  { id: 'classmate', label: '동기', labelEn: 'Classmate', icon: Users, color: '#00BCD4', speechToUser: 'informal', speechFromUser: 'informal' },
  { id: 'roommate', label: '룸메이트', labelEn: 'Roommate', icon: Users, color: '#FF9800', speechToUser: 'informal', speechFromUser: 'informal' },
  
  // Hierarchy - Lower
  { id: 'junior', label: '후배', labelEn: 'Junior', icon: GraduationCap, color: '#4CAF50', speechToUser: 'polite', speechFromUser: 'informal' },
  { id: 'younger_sibling', label: '동생', labelEn: 'Younger Sibling', icon: User, color: '#8BC34A', speechToUser: 'informal', speechFromUser: 'informal' },
  
  // Hierarchy - Higher
  { id: 'senior', label: '선배', labelEn: 'Senior', icon: User, color: '#F4A261', speechToUser: 'informal', speechFromUser: 'polite' },
  { id: 'older_sibling', label: '형/누나/오빠/언니', labelEn: 'Older Sibling', icon: User, color: '#FF7043', speechToUser: 'informal', speechFromUser: 'polite' },
  
  // Professional - Equal
  { id: 'colleague', label: '동료', labelEn: 'Colleague', icon: Briefcase, color: '#607D8B', speechToUser: 'polite', speechFromUser: 'polite' },
  { id: 'teammate', label: '팀원', labelEn: 'Teammate', icon: Briefcase, color: '#795548', speechToUser: 'polite', speechFromUser: 'polite' },
  
  // Professional - Formal
  { id: 'boss', label: '상사/팀장', labelEn: 'Boss', icon: Building2, color: '#E53935', speechToUser: 'polite', speechFromUser: 'formal' },
  { id: 'professor', label: '교수님', labelEn: 'Professor', icon: GraduationCap, color: '#2196F3', speechToUser: 'polite', speechFromUser: 'formal' },
  { id: 'teacher', label: '선생님', labelEn: 'Teacher', icon: GraduationCap, color: '#3F51B5', speechToUser: 'polite', speechFromUser: 'formal' },
  { id: 'client', label: '고객/클라이언트', labelEn: 'Client', icon: Briefcase, color: '#9C27B0', speechToUser: 'formal', speechFromUser: 'formal' },
  
  // Service
  { id: 'staff', label: '직원/점원', labelEn: 'Staff', icon: User, color: '#009688', speechToUser: 'polite', speechFromUser: 'polite' },
  { id: 'stranger', label: '처음 만난 사람', labelEn: 'Stranger', icon: User, color: '#78909C', speechToUser: 'polite', speechFromUser: 'polite' },
];

const PERSONALITY_TRAITS = [
  '친절한', '유쾌한', '차분한', '활발한', '진지한', '따뜻한',
  '엄격한', '재미있는', '꼼꼼한', '열정적인', '조용한', '사교적인',
];

const INTEREST_OPTIONS = [
  'K-POP', '영화', '드라마', '음악', '독서', '여행', '카페', '음식',
  '운동', '게임', '패션', '사진', '요리', '미술', '역사', '과학',
];

const AVATAR_ICONS = [
  { id: 'user', icon: User },
  { id: 'users', icon: Users },
  { id: 'graduationCap', icon: GraduationCap },
  { id: 'briefcase', icon: Briefcase },
  { id: 'building', icon: Building2 },
];

export default function CreateAvatarScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const existingAvatar = route.params?.avatar;
  const isEdit = route.params?.isEdit || false;
  const template = route.params?.template;

  const [currentStep, setCurrentStep] = useState(1);
  const [generatingBio, setGeneratingBio] = useState(false);
  const [generatedBio, setGeneratedBio] = useState('');
  
  // Custom input states
  const [customInterest, setCustomInterest] = useState('');
  const [customDislike, setCustomDislike] = useState('');
  const [customTrait, setCustomTrait] = useState('');

  const initialData = existingAvatar || template || {
    name_ko: '',
    name_en: '',
    age: '',
    gender: 'other',
    avatarType: 'fictional', // default to fictional
    role: 'friend',
    relationship_description: '',
    personality_traits: [],
    speaking_style: '',
    interests: [],
    dislikes: [],
    avatarBg: AVATAR_COLORS.purple,
    icon: 'user',
    difficulty: 'medium',
    memo: '',
    description: '', // 아바타 관련 설명
  };

  const [formData, setFormData] = useState<AvatarFormData>(initialData);

  const updateField = <K extends keyof AvatarFormData>(field: K, value: AvatarFormData[K]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleArrayItem = (field: 'interests' | 'dislikes' | 'personality_traits', item: string) => {
    setFormData((prev) => {
      const arr = prev[field];
      if (arr.includes(item)) {
        return { ...prev, [field]: arr.filter((i) => i !== item) };
      } else {
        return { ...prev, [field]: [...arr, item] };
      }
    });
  };

  const addCustomItem = (field: 'interests' | 'dislikes' | 'personality_traits', value: string, setValue: (v: string) => void) => {
    const trimmed = value.trim();
    if (trimmed && !formData[field].includes(trimmed)) {
      setFormData((prev) => ({ ...prev, [field]: [...prev[field], trimmed] }));
      setValue('');
    }
  };

  // Get recommended speech levels based on role
  const getRecommendedSpeech = () => {
    const role = ROLES.find((r) => r.id === formData.role);
    return {
      toUser: role?.speechToUser || 'polite',
      fromUser: role?.speechFromUser || 'polite',
    };
  };

  // Generate AI bio when entering step 4
  useEffect(() => {
    if (currentStep === 4 && !generatedBio) {
      generateAvatarBio();
    }
  }, [currentStep]);

  const generateAvatarBio = async () => {
    setGeneratingBio(true);
    
    // Simulate AI generation (in real app, call API)
    await new Promise((resolve) => setTimeout(resolve, 1500));
    
    const roleInfo = ROLES.find((r) => r.id === formData.role);
    const traits = formData.personality_traits.join(', ');
    const interests = formData.interests.slice(0, 3).join(', ');
    const avoidTopics = formData.dislikes.length > 0 
      ? formData.dislikes.join(', ')
      : '특별히 없음';
    
    const speech = getRecommendedSpeech();
    const speechToUserLabel = SPEECH_LEVELS[speech.toUser]?.name_ko || '해요체';
    const speechFromUserLabel = SPEECH_LEVELS[speech.fromUser]?.name_ko || '해요체';
    
    // Generate bio based on inputs
    const bio = `${formData.name_ko || '이 아바타'}는 ${roleInfo?.label || '친구'} 관계입니다. ` +
      `성격은 ${traits || '친절한'} 편이며, ${interests || '다양한 주제'}에 관심이 많습니다.\n\n` +
      `💬 대화 팁:\n` +
      `• ${formData.name_ko || '아바타'}는 ${speechToUserLabel}(으)로 말합니다\n` +
      `• 당신은 ${speechFromUserLabel}(으)로 대화하세요\n` +
      `• ${formData.speaking_style || '편하게 대화해도 좋습니다'}\n\n` +
      `⚠️ 피해야 할 주제:\n${avoidTopics}`;
    
    setGeneratedBio(bio);
    setGeneratingBio(false);
  };

  const handleNext = () => {
    if (currentStep < STEPS.length) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSave();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    } else {
      navigation.goBack();
    }
  };

  const handleSave = async () => {
    const speech = getRecommendedSpeech();
    const avatarData = {
      ...formData,
      formality_to_user: speech.toUser,
      formality_from_user: speech.fromUser,
      bio: generatedBio,
    };
    
    console.log('Saving avatar:', avatarData);
    navigation.navigate('Main', { screen: 'Avatar' });
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 1:
        return formData.name_ko.trim().length > 0;
      case 2:
        return formData.role !== undefined;
      case 3:
        return formData.personality_traits.length > 0 && formData.interests.length > 0;
      case 4:
        return true;
      default:
        return false;
    }
  };

  // Render Step 1: Basic Info
  const renderStep1 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>아바타의 기본 정보를 입력하세요</Text>

      {/* Avatar Type Selection */}
      <Text style={styles.fieldLabel}>아바타 유형 *</Text>
      <View style={styles.avatarTypeRow}>
        <TouchableOpacity
          style={[
            styles.avatarTypeCard,
            formData.avatarType === 'fictional' && styles.avatarTypeCardActive,
            formData.avatarType === 'fictional' && { borderColor: '#9C27B0' },
          ]}
          onPress={() => updateField('avatarType', 'fictional')}
        >
          <View style={[styles.avatarTypeIcon, { backgroundColor: '#F3E5F5' }]}>
            <Sparkles size={24} color="#9C27B0" />
          </View>
          <Text style={[styles.avatarTypeLabel, formData.avatarType === 'fictional' && { color: '#9C27B0' }]}>
            가상 인물
          </Text>
          <Text style={styles.avatarTypeDesc}>상상 속 캐릭터</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[
            styles.avatarTypeCard,
            formData.avatarType === 'real' && styles.avatarTypeCardActive,
            formData.avatarType === 'real' && { borderColor: '#2196F3' },
          ]}
          onPress={() => updateField('avatarType', 'real')}
        >
          <View style={[styles.avatarTypeIcon, { backgroundColor: '#E3F2FD' }]}>
            <User size={24} color="#2196F3" />
          </View>
          <Text style={[styles.avatarTypeLabel, formData.avatarType === 'real' && { color: '#2196F3' }]}>
            실제 인물
          </Text>
          <Text style={styles.avatarTypeDesc}>실제 아는 사람</Text>
        </TouchableOpacity>
      </View>
      
      <InputField
        label="이름 (한국어) *"
        value={formData.name_ko}
        onChangeText={(v) => updateField('name_ko', v)}
        placeholder="예: 김지원"
      />
      
      <InputField
        label="이름 (영어)"
        value={formData.name_en}
        onChangeText={(v) => updateField('name_en', v)}
        placeholder="예: Jiwon"
      />
      
      <InputField
        label="나이"
        value={formData.age}
        onChangeText={(v) => updateField('age', v)}
        placeholder="예: 25"
        keyboardType="numeric"
      />

      <Text style={styles.fieldLabel}>성별</Text>
      <View style={styles.optionRow}>
        {['male', 'female', 'other'].map((g) => (
          <TouchableOpacity
            key={g}
            style={[styles.optionButton, formData.gender === g && styles.optionButtonActive]}
            onPress={() => updateField('gender', g as any)}
          >
            <Text style={[styles.optionText, formData.gender === g && styles.optionTextActive]}>
              {g === 'male' ? '남성' : g === 'female' ? '여성' : '기타'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.fieldLabel}>아바타 색상</Text>
      <View style={styles.colorRow}>
        {Object.entries(AVATAR_COLORS).map(([key, color]) => (
          <TouchableOpacity
            key={key}
            style={[styles.colorButton, { backgroundColor: color }, formData.avatarBg === color && styles.colorButtonActive]}
            onPress={() => updateField('avatarBg', color)}
          >
            {formData.avatarBg === color && <Check size={18} color="#FFFFFF" />}
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.fieldLabel}>아바타 아이콘</Text>
      <View style={styles.iconRow}>
        {AVATAR_ICONS.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={[styles.iconButton, formData.icon === item.id && styles.iconButtonActive]}
            onPress={() => updateField('icon', item.id)}
          >
            <item.icon size={24} color={formData.icon === item.id ? '#FFFFFF' : '#6C6C80'} />
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  // Render Step 2: Role & Relationship
  const renderStep2 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>아바타와의 관계를 설정하세요</Text>
      <Text style={styles.stepSubtitle}>관계에 따라 적절한 말투가 자동으로 설정됩니다</Text>

      {/* Role Categories */}
      <Text style={styles.fieldLabel}>관계 선택 *</Text>
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false}
        style={styles.roleScrollView}
        contentContainerStyle={styles.roleScrollContent}
      >
        {ROLES.map((role) => (
          <TouchableOpacity
            key={role.id}
            style={[
              styles.roleChip,
              formData.role === role.id && styles.roleChipActive,
              formData.role === role.id && { backgroundColor: role.color },
            ]}
            onPress={() => updateField('role', role.id)}
          >
            <role.icon size={16} color={formData.role === role.id ? '#FFFFFF' : role.color} />
            <Text style={[
              styles.roleChipText,
              formData.role === role.id && styles.roleChipTextActive,
            ]}>
              {role.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <InputField
        label="관계 설명"
        value={formData.relationship_description}
        onChangeText={(v) => updateField('relationship_description', v)}
        placeholder="예: 같은 동아리 후배, 회사에서 만난 팀장님, 학교 동기"
        multiline
        numberOfLines={2}
      />

      {/* Avatar Description - AI Prompt */}
      <Text style={styles.fieldLabel}>아바타 관련 설명</Text>
      <TextInput
        style={styles.descriptionInput}
        value={formData.description}
        onChangeText={(v) => updateField('description', v)}
        placeholder="이 아바타에 대해 자세히 설명해주세요. AI가 대화할 때 참고합니다.&#10;&#10;예: 이 사람은 항상 밝고 에너지가 넘치며, 말을 빠르게 하는 편입니다. 농담을 자주 하고 웃음이 많습니다."
        placeholderTextColor="#B0B0C5"
        multiline
        numberOfLines={4}
        textAlignVertical="top"
      />
      <View style={styles.descriptionHint}>
        <Sparkles size={14} color="#6C3BFF" />
        <Text style={styles.descriptionHintText}>
          AI가 아바타의 말투, 성격, 행동 패턴을 이해하는 데 도움이 됩니다
        </Text>
      </View>

      <Text style={styles.fieldLabel}>난이도</Text>
      <View style={styles.optionRow}>
        {[
          { id: 'easy', label: '쉬움', color: '#4CAF50' },
          { id: 'medium', label: '보통', color: '#F4A261' },
          { id: 'hard', label: '어려움', color: '#E53935' },
        ].map((d) => (
          <TouchableOpacity
            key={d.id}
            style={[styles.optionButton, formData.difficulty === d.id && styles.optionButtonActive, formData.difficulty === d.id && { backgroundColor: d.color, borderColor: d.color }]}
            onPress={() => updateField('difficulty', d.id as any)}
          >
            <Text style={[styles.optionText, formData.difficulty === d.id && styles.optionTextActive]}>{d.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  // Render Step 3: Personality & Interests (same style as user profile)
  const renderStep3 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>성격과 관심사를 선택하세요</Text>

      {/* Personality Traits */}
      <Text style={styles.fieldLabel}>성격 특성 (최소 1개) *</Text>
      <View style={styles.tagGrid}>
        {PERSONALITY_TRAITS.map((trait) => (
          <Tag
            key={trait}
            label={trait}
            selected={formData.personality_traits.includes(trait)}
            onPress={() => toggleArrayItem('personality_traits', trait)}
          />
        ))}
      </View>
      
      {/* Custom trait input */}
      <View style={styles.customInputRow}>
        <TextInput
          style={styles.customInput}
          value={customTrait}
          onChangeText={setCustomTrait}
          placeholder="직접 입력..."
          placeholderTextColor="#B0B0C5"
          onSubmitEditing={() => addCustomItem('personality_traits', customTrait, setCustomTrait)}
        />
        <TouchableOpacity 
          style={[styles.addButton, !customTrait.trim() && styles.addButtonDisabled]}
          onPress={() => addCustomItem('personality_traits', customTrait, setCustomTrait)}
          disabled={!customTrait.trim()}
        >
          <Plus size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <InputField
        label="말하는 스타일"
        value={formData.speaking_style}
        onChangeText={(v) => updateField('speaking_style', v)}
        placeholder="예: 차분하게 말하는 편, 유머를 섞어서 말함"
        multiline
        numberOfLines={2}
      />

      {/* Interests */}
      <Text style={styles.fieldLabel}>관심사 (최소 1개) *</Text>
      <View style={styles.tagGrid}>
        {INTEREST_OPTIONS.map((interest) => (
          <Tag
            key={interest}
            label={interest}
            selected={formData.interests.includes(interest)}
            onPress={() => toggleArrayItem('interests', interest)}
          />
        ))}
      </View>
      
      {/* Custom interest input */}
      <View style={styles.customInputRow}>
        <TextInput
          style={styles.customInput}
          value={customInterest}
          onChangeText={setCustomInterest}
          placeholder="직접 입력 (예: 보드게임, 재즈)"
          placeholderTextColor="#B0B0C5"
          onSubmitEditing={() => addCustomItem('interests', customInterest, setCustomInterest)}
        />
        <TouchableOpacity 
          style={[styles.addButton, !customInterest.trim() && styles.addButtonDisabled]}
          onPress={() => addCustomItem('interests', customInterest, setCustomInterest)}
          disabled={!customInterest.trim()}
        >
          <Plus size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Dislikes */}
      <Text style={styles.fieldLabel}>싫어하는 주제</Text>
      <View style={styles.tagGrid}>
        {INTEREST_OPTIONS.filter((i) => !formData.interests.includes(i)).slice(0, 10).map((interest) => (
          <Tag
            key={interest}
            label={interest}
            selected={formData.dislikes.includes(interest)}
            onPress={() => toggleArrayItem('dislikes', interest)}
            variant="outline"
          />
        ))}
      </View>
      
      {/* Custom dislike input */}
      <View style={styles.customInputRow}>
        <TextInput
          style={styles.customInput}
          value={customDislike}
          onChangeText={setCustomDislike}
          placeholder="직접 입력 (예: 정치, 종교)"
          placeholderTextColor="#B0B0C5"
          onSubmitEditing={() => addCustomItem('dislikes', customDislike, setCustomDislike)}
        />
        <TouchableOpacity 
          style={[styles.addButton, styles.addButtonGray, !customDislike.trim() && styles.addButtonDisabled]}
          onPress={() => addCustomItem('dislikes', customDislike, setCustomDislike)}
          disabled={!customDislike.trim()}
        >
          <Plus size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      {/* Memo for AI */}
      <Text style={styles.fieldLabel}>메모 (AI 참고용)</Text>
      <TextInput
        style={styles.memoInput}
        value={formData.memo}
        onChangeText={(v) => updateField('memo', v)}
        placeholder="예: 이 캐릭터는 말이 빠르고 자주 웃어요. 약간 장난기가 있습니다."
        placeholderTextColor="#B0B0C5"
        multiline
        numberOfLines={3}
        textAlignVertical="top"
      />
      <View style={styles.memoHint}>
        <Sparkles size={14} color="#6C3BFF" />
        <Text style={styles.memoHintText}>
          AI가 아바타의 말투와 성격을 더 잘 표현할 수 있도록 도와줍니다
        </Text>
      </View>
    </View>
  );

  // Render Step 4: AI-generated Bio & Speech Level Confirmation
  const renderStep4 = () => {
    const speech = getRecommendedSpeech();
    const roleInfo = ROLES.find((r) => r.id === formData.role);

    return (
      <View style={styles.stepContent}>
        <Text style={styles.stepTitle}>아바타 정보 확인</Text>
        <Text style={styles.stepSubtitle}>AI가 분석한 대화 가이드를 확인하세요</Text>

        {/* Speech Level Recommendation */}
        <Card variant="elevated" style={styles.speechRecommendCard}>
          <View style={styles.speechRecommendHeader}>
            <Sparkles size={20} color="#6C3BFF" />
            <Text style={styles.speechRecommendTitle}>추천 말투</Text>
          </View>
          <Text style={styles.speechRecommendSubtitle}>
            {roleInfo?.label} 관계에 맞는 말투입니다
          </Text>
          
          <View style={styles.speechLevelRow}>
            <View style={styles.speechLevelItem}>
              <Text style={styles.speechLevelLabel}>아바타 → 나</Text>
              <View style={[styles.speechBadge, { backgroundColor: SPEECH_LEVELS[speech.toUser]?.color + '20' }]}>
                <Text style={[styles.speechBadgeText, { color: SPEECH_LEVELS[speech.toUser]?.color }]}>
                  {SPEECH_LEVELS[speech.toUser]?.name_ko}
                </Text>
              </View>
            </View>
            <View style={styles.speechLevelItem}>
              <Text style={styles.speechLevelLabel}>나 → 아바타</Text>
              <View style={[styles.speechBadge, { backgroundColor: SPEECH_LEVELS[speech.fromUser]?.color + '20' }]}>
                <Text style={[styles.speechBadgeText, { color: SPEECH_LEVELS[speech.fromUser]?.color }]}>
                  {SPEECH_LEVELS[speech.fromUser]?.name_ko}
                </Text>
              </View>
            </View>
          </View>
        </Card>

        {/* AI Generated Bio */}
        <Card variant="elevated" style={styles.bioCard}>
          <View style={styles.bioHeader}>
            <Sparkles size={20} color="#F4A261" />
            <Text style={styles.bioTitle}>대화 가이드</Text>
          </View>
          
          {generatingBio ? (
            <View style={styles.bioLoading}>
              <ActivityIndicator size="small" color="#6C3BFF" />
              <Text style={styles.bioLoadingText}>AI가 분석 중...</Text>
            </View>
          ) : (
            <Text style={styles.bioText}>{generatedBio}</Text>
          )}
          
          <TouchableOpacity style={styles.regenerateBtn} onPress={generateAvatarBio}>
            <Sparkles size={14} color="#6C3BFF" />
            <Text style={styles.regenerateBtnText}>다시 생성</Text>
          </TouchableOpacity>
        </Card>

        {/* Avatar Preview */}
        <View style={styles.avatarPreview}>
          <View style={[styles.previewAvatar, { backgroundColor: formData.avatarBg }]}>
            <Icon name={formData.icon as any || 'user'} size={32} color="#FFFFFF" />
          </View>
          <Text style={styles.previewName}>{formData.name_ko || '이름 없음'}</Text>
          <Text style={styles.previewRole}>
            {roleInfo?.label} · {formData.difficulty === 'easy' ? '쉬움' : formData.difficulty === 'medium' ? '보통' : '어려움'}
          </Text>
        </View>
      </View>
    );
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1: return renderStep1();
      case 2: return renderStep2();
      case 3: return renderStep3();
      case 4: return renderStep4();
      default: return null;
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <TouchableOpacity onPress={handleBack} style={styles.headerBtn}>
          <ChevronLeft size={24} color="#1A1A2E" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{isEdit ? '아바타 수정' : '새 아바타 만들기'}</Text>
        <View style={styles.headerBtn} />
      </View>

      <View style={styles.stepsRow}>
        {STEPS.map((step, index) => (
          <View key={step.id} style={styles.stepIndicator}>
            <View style={[styles.stepDot, currentStep >= step.id && styles.stepDotActive, currentStep === step.id && styles.stepDotCurrent]}>
              {currentStep > step.id ? <Check size={14} color="#FFFFFF" /> : <Text style={[styles.stepNumber, currentStep >= step.id && styles.stepNumberActive]}>{step.id}</Text>}
            </View>
            {index < STEPS.length - 1 && <View style={[styles.stepLine, currentStep > step.id && styles.stepLineActive]} />}
          </View>
        ))}
      </View>

      <View style={styles.stepInfo}>
        <Text style={styles.stepInfoTitle}>{STEPS[currentStep - 1].title}</Text>
        <Text style={styles.stepInfoSubtitle}>{STEPS[currentStep - 1].subtitle}</Text>
      </View>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          {renderCurrentStep()}
        </ScrollView>

        <View style={styles.footer}>
          <Button
            title={currentStep === STEPS.length ? '완료' : '다음'}
            onPress={handleNext}
            showArrow={currentStep < STEPS.length}
            disabled={!isStepValid()}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  headerBtn: { width: 36 },
  headerTitle: { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },
  stepsRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingHorizontal: 40, marginBottom: 16 },
  stepIndicator: { flexDirection: 'row', alignItems: 'center' },
  stepDot: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#E2E2EC', alignItems: 'center', justifyContent: 'center' },
  stepDotActive: { backgroundColor: '#6C3BFF' },
  stepDotCurrent: { backgroundColor: '#6C3BFF', borderWidth: 3, borderColor: '#C8B4F8' },
  stepNumber: { fontSize: 12, fontWeight: '600', color: '#6C6C80' },
  stepNumberActive: { color: '#FFFFFF' },
  stepLine: { width: 40, height: 2, backgroundColor: '#E2E2EC', marginHorizontal: 4 },
  stepLineActive: { backgroundColor: '#6C3BFF' },
  stepInfo: { alignItems: 'center', marginBottom: 20 },
  stepInfoTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  stepInfoSubtitle: { fontSize: 12, color: '#6C6C80' },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 100 },
  stepContent: {},
  stepTitle: { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginBottom: 8 },
  stepSubtitle: { fontSize: 13, color: '#6C6C80', marginBottom: 20, lineHeight: 18 },
  fieldLabel: { fontSize: 13, fontWeight: '600', color: '#1A1A2E', marginBottom: 10, marginTop: 16 },
  optionRow: { flexDirection: 'row', gap: 10, marginBottom: 8 },
  optionButton: { flex: 1, paddingVertical: 12, borderRadius: 12, borderWidth: 1.5, borderColor: '#E2E2EC', backgroundColor: '#FFFFFF', alignItems: 'center' },
  optionButtonActive: { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  optionText: { fontSize: 14, fontWeight: '600', color: '#6C6C80' },
  optionTextActive: { color: '#FFFFFF' },
  colorRow: { flexDirection: 'row', gap: 12, marginBottom: 8 },
  colorButton: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  colorButtonActive: { borderWidth: 3, borderColor: '#1A1A2E' },
  iconRow: { flexDirection: 'row', gap: 12, marginBottom: 8 },
  iconButton: { width: 48, height: 48, borderRadius: 12, backgroundColor: '#FFFFFF', borderWidth: 1.5, borderColor: '#E2E2EC', alignItems: 'center', justifyContent: 'center' },
  iconButtonActive: { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  
  // Avatar Type
  avatarTypeRow: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  avatarTypeCard: { flex: 1, backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, alignItems: 'center', borderWidth: 2, borderColor: '#E2E2EC' },
  avatarTypeCardActive: { borderWidth: 2 },
  avatarTypeIcon: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginBottom: 10 },
  avatarTypeLabel: { fontSize: 15, fontWeight: '700', color: '#1A1A2E', marginBottom: 2 },
  avatarTypeDesc: { fontSize: 11, color: '#6C6C80' },

  // Role Chips (horizontal scroll)
  roleScrollView: { marginBottom: 16, marginHorizontal: -20 },
  roleScrollContent: { paddingHorizontal: 20, gap: 8, flexDirection: 'row' },
  roleChip: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 20, backgroundColor: '#FFFFFF', borderWidth: 1.5, borderColor: '#E2E2EC' },
  roleChipActive: { borderColor: 'transparent' },
  roleChipText: { fontSize: 13, fontWeight: '600', color: '#6C6C80' },
  roleChipTextActive: { color: '#FFFFFF' },

  // Description input
  descriptionInput: { backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 14, color: '#1A1A2E', borderWidth: 1, borderColor: '#E2E2EC', minHeight: 100, lineHeight: 20 },
  descriptionHint: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginTop: 10, backgroundColor: '#F0EDFF', padding: 12, borderRadius: 10 },
  descriptionHintText: { flex: 1, fontSize: 12, color: '#6C3BFF', lineHeight: 18 },

  roleGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 20 },
  roleCard: { width: '47%', backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, alignItems: 'center', borderWidth: 2, borderColor: '#E2E2EC', position: 'relative' },
  roleCardActive: { borderWidth: 2 },
  roleIconContainer: { width: 56, height: 56, borderRadius: 28, alignItems: 'center', justifyContent: 'center', marginBottom: 10 },
  roleLabel: { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  roleLabelEn: { fontSize: 12, color: '#6C6C80' },
  roleCheck: { position: 'absolute', top: 8, right: 8, width: 22, height: 22, borderRadius: 11, alignItems: 'center', justifyContent: 'center' },
  tagGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  customInputRow: { flexDirection: 'row', gap: 10, marginTop: 8, marginBottom: 8 },
  customInput: { flex: 1, backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 12, fontSize: 14, color: '#1A1A2E', borderWidth: 1, borderColor: '#E2E2EC' },
  addButton: { width: 48, height: 48, borderRadius: 12, backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center' },
  addButtonGray: { backgroundColor: '#6C6C80' },
  addButtonDisabled: { opacity: 0.5 },
  memoInput: { backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 14, color: '#1A1A2E', borderWidth: 1, borderColor: '#E2E2EC', minHeight: 80, lineHeight: 20 },
  memoHint: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginTop: 10, backgroundColor: '#F0EDFF', padding: 12, borderRadius: 10 },
  memoHintText: { flex: 1, fontSize: 12, color: '#6C3BFF', lineHeight: 18 },
  speechRecommendCard: { marginBottom: 16 },
  speechRecommendHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 },
  speechRecommendTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  speechRecommendSubtitle: { fontSize: 13, color: '#6C6C80', marginBottom: 16 },
  speechLevelRow: { flexDirection: 'row', gap: 16 },
  speechLevelItem: { flex: 1, alignItems: 'center' },
  speechLevelLabel: { fontSize: 12, color: '#6C6C80', marginBottom: 8 },
  speechBadge: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12 },
  speechBadgeText: { fontSize: 14, fontWeight: '600' },
  bioCard: { marginBottom: 16 },
  bioHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  bioTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  bioLoading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 20 },
  bioLoadingText: { fontSize: 14, color: '#6C6C80' },
  bioText: { fontSize: 14, color: '#1A1A2E', lineHeight: 22 },
  regenerateBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 16, paddingVertical: 10, backgroundColor: '#F0EDFF', borderRadius: 10 },
  regenerateBtnText: { fontSize: 13, fontWeight: '600', color: '#6C3BFF' },
  avatarPreview: { alignItems: 'center', paddingVertical: 20 },
  previewAvatar: { width: 64, height: 64, borderRadius: 32, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  previewName: { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  previewRole: { fontSize: 13, color: '#6C6C80' },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
});
