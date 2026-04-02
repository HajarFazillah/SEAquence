import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity, TextInput,
  KeyboardAvoidingView, Platform, ActivityIndicator, Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  ChevronLeft, Check, Plus, RefreshCw, Sparkles,
  User, Users, GraduationCap, Building2, Briefcase,
  Heart, Baby, Crown, Smile,
} from 'lucide-react-native';
import { Header, Card, Button, InputField, Tag, Icon, IconName } from '../components';
import { AVATAR_COLORS, SPEECH_LEVELS } from '../constants';
import { createAvatar, updateAvatar } from '../services/apiUser';
import { Star } from 'lucide-react-native';

// 5 Steps
const STEPS = [
  { id: 1, title: '기본 정보', subtitle: 'Basic Info' },
  { id: 2, title: '관계 선택', subtitle: 'Relationship' },
  { id: 3, title: '상세 설명', subtitle: 'Description' },
  { id: 4, title: '성격 & 관심사', subtitle: 'Personality' },
  { id: 5, title: '확인', subtitle: 'Preview' },
];

const AVATAR_ICONS = [
  { id: 'user', icon: User },
  { id: 'users', icon: Users },
  { id: 'smile', icon: Smile },
  { id: 'userCircle', icon: User },
  { id: 'crown', icon: Crown },
  { id: 'baby', icon: Baby },
  { id: 'graduationCap', icon: GraduationCap },
  { id: 'briefcase', icon: Briefcase },
  { id: 'building', icon: Building2 },
  { id: 'heart', icon: Heart },
  { id: 'star', icon: Star },
  { id: 'sparkles', icon: Sparkles },
];

const RELATIONSHIP_CATEGORIES = [
  {
    category: '친구/동기',
    roles: [
      { id: 'friend', label: '친구', speechToUser: 'informal', speechFromUser: 'informal' },
      { id: 'close_friend', label: '절친', speechToUser: 'informal', speechFromUser: 'informal' },
      { id: 'classmate', label: '동기', speechToUser: 'informal', speechFromUser: 'informal' },
      { id: 'roommate', label: '룸메이트', speechToUser: 'informal', speechFromUser: 'informal' },
      { id: 'club_member', label: '동아리 멤버', speechToUser: 'informal', speechFromUser: 'informal' },
    ],
  },
  {
    category: '가족',
    roles: [
      { id: 'younger_sibling', label: '동생', speechToUser: 'informal', speechFromUser: 'informal' },
      { id: 'older_brother', label: '형/오빠', speechToUser: 'informal', speechFromUser: 'polite' },
      { id: 'older_sister', label: '누나/언니', speechToUser: 'informal', speechFromUser: 'polite' },
      { id: 'cousin', label: '사촌', speechToUser: 'informal', speechFromUser: 'informal' },
      { id: 'parent', label: '부모님', speechToUser: 'polite', speechFromUser: 'formal' },
      { id: 'grandparent', label: '조부모님', speechToUser: 'polite', speechFromUser: 'formal' },
    ],
  },
  {
    category: '학교',
    roles: [
      { id: 'junior', label: '후배', speechToUser: 'polite', speechFromUser: 'informal' },
      { id: 'senior', label: '선배', speechToUser: 'informal', speechFromUser: 'polite' },
      { id: 'professor', label: '교수님', speechToUser: 'polite', speechFromUser: 'formal' },
      { id: 'teacher', label: '선생님', speechToUser: 'polite', speechFromUser: 'formal' },
      { id: 'tutor', label: '튜터/과외선생', speechToUser: 'polite', speechFromUser: 'polite' },
      { id: 'classmate_formal', label: '같은 반 친구', speechToUser: 'informal', speechFromUser: 'informal' },
    ],
  },
  {
    category: '직장',
    roles: [
      { id: 'colleague', label: '동료', speechToUser: 'polite', speechFromUser: 'polite' },
      { id: 'teammate', label: '팀원', speechToUser: 'polite', speechFromUser: 'polite' },
      { id: 'team_leader', label: '팀장', speechToUser: 'polite', speechFromUser: 'formal' },
      { id: 'boss', label: '상사/부장', speechToUser: 'polite', speechFromUser: 'formal' },
      { id: 'ceo', label: '대표/사장님', speechToUser: 'formal', speechFromUser: 'formal' },
      { id: 'intern', label: '인턴', speechToUser: 'polite', speechFromUser: 'informal' },
      { id: 'client', label: '고객/클라이언트', speechToUser: 'formal', speechFromUser: 'formal' },
    ],
  },
  {
    category: '서비스/기타',
    roles: [
      { id: 'staff', label: '직원/점원', speechToUser: 'polite', speechFromUser: 'polite' },
      { id: 'stranger', label: '처음 만난 사람', speechToUser: 'polite', speechFromUser: 'polite' },
      { id: 'neighbor', label: '이웃', speechToUser: 'polite', speechFromUser: 'polite' },
      { id: 'doctor', label: '의사', speechToUser: 'polite', speechFromUser: 'formal' },
      { id: 'delivery', label: '배달원', speechToUser: 'polite', speechFromUser: 'polite' },
      { id: 'taxi_driver', label: '택시기사', speechToUser: 'polite', speechFromUser: 'polite' },
    ],
  },
];

const ALL_ROLES = RELATIONSHIP_CATEGORIES.flatMap(c => c.roles);

const PERSONALITY_TRAITS = [
  '친절한', '유쾌한', '차분한', '활발한', '내성적인', '외향적인',
  '진지한', '유머러스', '다정한', '쿨한', '열정적인', '느긋한',
  '꼼꼼한', '대충대충', '긍정적인', '현실적인', '감성적인', '이성적인',
];

const INTEREST_OPTIONS = [
  'K-POP', '영화', '드라마', '음악', '독서', '여행', '카페', '음식',
  '운동', '게임', '패션', '사진', '요리', '미술', '역사', '과학',
];

interface AvatarFormData {
  name_ko: string;
  name_en: string;
  age: string;
  gender: 'male' | 'female' | 'other';
  avatarType: 'fictional' | 'real';
  role: string;
  customRole: string;
  relationship_description: string;
  description: string;
  personality_traits: string[];
  speaking_style: string;
  interests: string[];
  dislikes: string[];
  avatarBg: string;
  icon: IconName;
  difficulty: 'easy' | 'medium' | 'hard';
  memo: string;
}

export default function CreateAvatarScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { avatar: existingAvatar, template, isEdit, mode } = route.params || {};

  const [currentStep, setCurrentStep] = useState(1);
  const [generatedBio, setGeneratedBio] = useState('');
  const [generatingBio, setGeneratingBio] = useState(false);
  const [saving, setSaving] = useState(false); // ← new

  const [customTrait, setCustomTrait] = useState('');
  const [customInterest, setCustomInterest] = useState('');
  const [customDislike, setCustomDislike] = useState('');

  const initialData: AvatarFormData = {
    name_ko: '',
    name_en: '',
    age: '',
    gender: 'other',
    avatarType: 'fictional',
    role: '',
    customRole: '',
    relationship_description: '',
    description: '',
    personality_traits: [],
    speaking_style: '',
    interests: [],
    dislikes: [],
    avatarBg: Object.values(AVATAR_COLORS)[0],
    icon: 'user' as IconName,
    difficulty: 'medium',
    memo: '',
    ...(existingAvatar || template || {}),
  };

  const [formData, setFormData] = useState<AvatarFormData>(initialData);

  const updateField = <K extends keyof AvatarFormData>(key: K, value: AvatarFormData[K]) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const toggleArrayItem = (key: 'personality_traits' | 'interests' | 'dislikes', item: string) => {
    const arr = formData[key];
    if (arr.includes(item)) {
      updateField(key, arr.filter(i => i !== item));
    } else {
      updateField(key, [...arr, item]);
    }
  };

  const addCustomItem = (
    key: 'personality_traits' | 'interests' | 'dislikes',
    value: string,
    setter: (v: string) => void
  ) => {
    const trimmed = value.trim();
    if (trimmed && !formData[key].includes(trimmed)) {
      updateField(key, [...formData[key], trimmed]);
      setter('');
    }
  };

  const getRecommendedSpeech = () => {
    const roleData = ALL_ROLES.find(r => r.id === formData.role);
    if (roleData) {
      return {
        toUser: roleData.speechToUser as 'formal' | 'polite' | 'informal',
        fromUser: roleData.speechFromUser as 'formal' | 'polite' | 'informal',
      };
    }
    return { toUser: 'polite' as const, fromUser: 'polite' as const };
  };

  useEffect(() => {
    if (currentStep === 5 && !generatedBio) {
      generateBio();
    }
  }, [currentStep]);

  const generateBio = () => {
    setGeneratingBio(true);
    setTimeout(() => {
      const roleLabel = ALL_ROLES.find(r => r.id === formData.role)?.label || formData.customRole || '지인';
      const traits = formData.personality_traits.slice(0, 3).join(', ') || '친절한';
      const interests = formData.interests.slice(0, 3).join(', ') || '다양한 주제';
      const avoidTopics = formData.dislikes.length > 0
        ? formData.dislikes.join(', ')
        : '특별히 없음';

      const speech = getRecommendedSpeech();
      const speechToUserLabel = SPEECH_LEVELS[speech.toUser]?.name_ko || '해요체';
      const speechFromUserLabel = SPEECH_LEVELS[speech.fromUser]?.name_ko || '해요체';

      const bio =
        `${formData.name_ko || '이 아바타'}는 ${roleLabel} 관계입니다. ` +
        `성격은 ${traits} 편이며, ${interests}에 관심이 많습니다.\n\n` +
        `💬 대화 팁:\n` +
        `• ${formData.name_ko || '아바타'}는 ${speechToUserLabel}(으)로 말합니다\n` +
        `• 당신은 ${speechFromUserLabel}(으)로 대화하세요\n` +
        `• ${formData.speaking_style || '자연스럽게 대화해도 좋습니다'}\n\n` +
        `⚠️ 피해야 할 주제:\n${avoidTopics}`;

      setGeneratedBio(bio);
      setGeneratingBio(false);
    }, 1000);
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

  // ── UPDATED handleSave ────────────────────────────────────────────────────
  const handleSave = async () => {
    const speech = getRecommendedSpeech();
    const avatarData = {
      ...formData,
      name_ko: formData.name_ko.trim(),
      role: formData.role || formData.customRole,
      formality_to_user: speech.toUser,
      formality_from_user: speech.fromUser,
      bio: generatedBio,
    };
    console.log('🚀 Saving:', avatarData);

    try {
      setSaving(true);
      if (isEdit && existingAvatar?.id) {
        await updateAvatar(String(existingAvatar.id), avatarData);
      } else {
        await createAvatar(avatarData);
      }
      navigation.navigate('Main', { screen: 'Avatar' });
      // useFocusEffect in AvatarScreen auto-refreshes the list ✅
    } catch (e) {
      Alert.alert('오류', '저장에 실패했어요. 다시 시도해주세요.');
    } finally {
      setSaving(false);
    }
  };
  // ─────────────────────────────────────────────────────────────────────────

  const isStepValid = () => {
    switch (currentStep) {
      case 1: return formData.name_ko.trim().length > 0;
      case 2: case 2: return (formData.role ?? '').length > 0 || (formData.customRole ?? '').trim().length > 0;
      case 3: return true;
      case 4: return formData.personality_traits.length > 0 && formData.interests.length > 0;
      case 5: return true;
      default: return false;
    }
  };

  const colorPalette = Object.entries(AVATAR_COLORS);

  const renderStep1 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>아바타의 기본 정보를 입력하세요</Text>
      <Text style={styles.fieldLabel}>아바타 유형 *</Text>
      <View style={styles.typeRow}>
        <TouchableOpacity
          style={[styles.typeCard, formData.avatarType === 'fictional' && styles.typeCardActive]}
          onPress={() => updateField('avatarType', 'fictional')}
        >
          <Sparkles size={24} color={formData.avatarType === 'fictional' ? '#9C27B0' : '#B0B0C5'} />
          <Text style={[styles.typeLabel, formData.avatarType === 'fictional' && { color: '#9C27B0' }]}>가상 인물</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.typeCard, formData.avatarType === 'real' && styles.typeCardActive, formData.avatarType === 'real' && { borderColor: '#2196F3' }]}
          onPress={() => updateField('avatarType', 'real')}
        >
          <User size={24} color={formData.avatarType === 'real' ? '#2196F3' : '#B0B0C5'} />
          <Text style={[styles.typeLabel, formData.avatarType === 'real' && { color: '#2196F3' }]}>실제 인물</Text>
        </TouchableOpacity>
      </View>
      <InputField label="이름 (한국어) *" value={formData.name_ko} onChangeText={(v) => updateField('name_ko', v)} placeholder="예: 김지원" />
      <InputField label="이름 (영어)" value={formData.name_en} onChangeText={(v) => updateField('name_en', v)} placeholder="예: Jiwon" />
      <InputField label="나이" value={formData.age} onChangeText={(v) => updateField('age', v)} placeholder="예: 25" keyboardType="numeric" />
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
      <View style={styles.colorGrid}>
        {colorPalette.map(([key, color]) => (
          <TouchableOpacity
            key={key}
            style={[styles.colorButton, { backgroundColor: color }, formData.avatarBg === color && styles.colorButtonActive]}
            onPress={() => updateField('avatarBg', color)}
          >
            {formData.avatarBg === color && <Check size={16} color="#FFFFFF" />}
          </TouchableOpacity>
        ))}
      </View>
      <Text style={styles.fieldLabel}>아바타 아이콘</Text>
      <View style={styles.iconGrid}>
        {AVATAR_ICONS.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={[styles.iconButton, formData.icon === item.id && styles.iconButtonActive]}
            onPress={() => updateField('icon', item.id as IconName)}
          >
            <item.icon size={22} color={formData.icon === item.id ? '#FFFFFF' : '#6C6C80'} />
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderStep2 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>아바타와의 관계를 설정하세요</Text>
      <Text style={styles.stepSubtitle}>관계에 따라 적절한 말투가 자동으로 설정됩니다</Text>
      {RELATIONSHIP_CATEGORIES.map((category) => (
        <View key={category.category} style={styles.roleCategory}>
          <Text style={styles.roleCategoryTitle}>{category.category}</Text>
          <View style={styles.roleGrid}>
            {category.roles.map((role) => (
              <TouchableOpacity
                key={role.id}
                style={[styles.roleButton, formData.role === role.id && styles.roleButtonActive]}
                onPress={() => { updateField('role', role.id); updateField('customRole', ''); }}
              >
                <Text style={[styles.roleButtonText, formData.role === role.id && styles.roleButtonTextActive]}>
                  {role.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      ))}
      <View style={styles.customRoleSection}>
        <Text style={styles.fieldLabel}>직접 입력</Text>
        <View style={styles.customRoleRow}>
          <TextInput
            style={styles.customRoleInput}
            value={formData.customRole}
            onChangeText={(v) => { updateField('customRole', v); if (v.trim()) updateField('role', ''); }}
            placeholder="위에 없는 관계를 직접 입력하세요"
            placeholderTextColor="#B0B0C5"
          />
        </View>
        {(formData.customRole ?? '').trim().length > 0 && (
          <View style={styles.customRoleSelected}>
            <Check size={16} color="#4CAF50" />
            <Text style={styles.customRoleSelectedText}>직접 입력: {formData.customRole}</Text>
          </View>
        )}
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
            style={[
              styles.optionButton,
              formData.difficulty === d.id && styles.optionButtonActive,
              formData.difficulty === d.id && { backgroundColor: d.color, borderColor: d.color },
            ]}
            onPress={() => updateField('difficulty', d.id as any)}
          >
            <Text style={[styles.optionText, formData.difficulty === d.id && styles.optionTextActive]}>
              {d.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderStep3 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>아바타에 대해 설명해주세요</Text>
      <Text style={styles.stepSubtitle}>AI가 더 자연스러운 대화를 만드는 데 도움이 됩니다</Text>
      <Text style={styles.fieldLabel}>관계 설명</Text>
      <TextInput
        style={styles.descInput}
        value={formData.relationship_description}
        onChangeText={(v) => updateField('relationship_description', v)}
        placeholder="이 아바타와 어떤 관계인지 설명해주세요&#10;&#10;예: 같은 동아리에서 만난 후배"
        placeholderTextColor="#B0B0C5"
        multiline
        numberOfLines={3}
        textAlignVertical="top"
      />
      <Text style={styles.fieldLabel}>아바타 관련 설명 (AI 프롬프트)</Text>
      <TextInput
        style={styles.descInputLarge}
        value={formData.description}
        onChangeText={(v) => updateField('description', v)}
        placeholder="이 아바타의 성격, 말투, 특징을 자세히 설명해주세요"
        placeholderTextColor="#B0B0C5"
        multiline
        numberOfLines={5}
        textAlignVertical="top"
      />
      <View style={styles.descHint}>
        <Sparkles size={14} color="#6C3BFF" />
        <Text style={styles.descHintText}>이 설명을 바탕으로 AI가 아바타의 말투와 성격을 표현합니다</Text>
      </View>
    </View>
  );

  const renderStep4 = () => (
    <View style={styles.stepContent}>
      <Text style={styles.stepTitle}>성격과 관심사를 선택하세요</Text>
      <Text style={styles.fieldLabel}>성격 특성 (최소 1개) *</Text>
      <View style={styles.tagGrid}>
        {PERSONALITY_TRAITS.map((trait) => (
          <Tag key={trait} label={trait} selected={formData.personality_traits.includes(trait)} onPress={() => toggleArrayItem('personality_traits', trait)} />
        ))}
      </View>
      <View style={styles.customInputRow}>
        <TextInput style={styles.customInput} value={customTrait} onChangeText={setCustomTrait} placeholder="직접 입력..." placeholderTextColor="#B0B0C5" onSubmitEditing={() => addCustomItem('personality_traits', customTrait, setCustomTrait)} />
        <TouchableOpacity style={[styles.addButton, !customTrait.trim() && styles.addButtonDisabled]} onPress={() => addCustomItem('personality_traits', customTrait, setCustomTrait)} disabled={!customTrait.trim()}>
          <Plus size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
      <InputField label="말하는 스타일" value={formData.speaking_style} onChangeText={(v) => updateField('speaking_style', v)} placeholder="예: 차분하게 말하는 편, 유머를 섞어서 말함" multiline numberOfLines={2} />
      <Text style={styles.fieldLabel}>관심사 (최소 1개) *</Text>
      <View style={styles.tagGrid}>
        {INTEREST_OPTIONS.map((interest) => (
          <Tag key={interest} label={interest} selected={formData.interests.includes(interest)} onPress={() => toggleArrayItem('interests', interest)} />
        ))}
      </View>
      <View style={styles.customInputRow}>
        <TextInput style={styles.customInput} value={customInterest} onChangeText={setCustomInterest} placeholder="직접 입력..." placeholderTextColor="#B0B0C5" onSubmitEditing={() => addCustomItem('interests', customInterest, setCustomInterest)} />
        <TouchableOpacity style={[styles.addButton, !customInterest.trim() && styles.addButtonDisabled]} onPress={() => addCustomItem('interests', customInterest, setCustomInterest)} disabled={!customInterest.trim()}>
          <Plus size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
      <Text style={styles.fieldLabel}>싫어하는 주제</Text>
      <View style={styles.tagGrid}>
        {['정치', '종교', '논쟁', '스포츠', '연예인', '학업', '취업', '결혼', '외모', '돈'].map((item) => (
          <Tag key={item} label={item} selected={formData.dislikes.includes(item)} onPress={() => toggleArrayItem('dislikes', item)} variant="outline" />
        ))}
      </View>
      <View style={styles.customInputRow}>
        <TextInput style={styles.customInput} value={customDislike} onChangeText={setCustomDislike} placeholder="직접 입력..." placeholderTextColor="#B0B0C5" onSubmitEditing={() => addCustomItem('dislikes', customDislike, setCustomDislike)} />
        <TouchableOpacity style={[styles.addButton, styles.addButtonGray, !customDislike.trim() && styles.addButtonDisabled]} onPress={() => addCustomItem('dislikes', customDislike, setCustomDislike)} disabled={!customDislike.trim()}>
          <Plus size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
      <Text style={styles.fieldLabel}>추가 메모 (AI 참고용)</Text>
      <TextInput style={styles.memoInput} value={formData.memo} onChangeText={(v) => updateField('memo', v)} placeholder="AI에게 전달할 추가 정보..." placeholderTextColor="#B0B0C5" multiline numberOfLines={2} textAlignVertical="top" />
    </View>
  );

  const renderStep5 = () => {
    const speech = getRecommendedSpeech();
    const roleLabel = ALL_ROLES.find(r => r.id === formData.role)?.label || formData.customRole || '지인';
    return (
      <View style={styles.stepContent}>
        <Text style={styles.stepTitle}>아바타 정보 확인</Text>
        <Text style={styles.stepSubtitle}>AI가 분석한 대화 가이드를 확인하세요</Text>
        <View style={styles.avatarPreview}>
          <View style={[styles.previewAvatar, { backgroundColor: formData.avatarBg }]}>
            <Icon name={formData.icon as any || 'user'} size={40} color="#FFFFFF" />
          </View>
          <Text style={styles.previewName}>{formData.name_ko || '아바타'}</Text>
          <Text style={styles.previewRole}>{roleLabel} · {formData.age ? `${formData.age}세` : ''}</Text>
          <View style={styles.previewTypeBadge}>
            {formData.avatarType === 'fictional' ? (
              <><Sparkles size={12} color="#9C27B0" /><Text style={[styles.previewTypeText, { color: '#9C27B0' }]}>가상 인물</Text></>
            ) : (
              <><User size={12} color="#2196F3" /><Text style={[styles.previewTypeText, { color: '#2196F3' }]}>실제 인물</Text></>
            )}
          </View>
        </View>
        <Card variant="elevated" style={styles.speechCard}>
          <View style={styles.speechHeader}>
            <Sparkles size={18} color="#6C3BFF" />
            <Text style={styles.speechTitle}>추천 말투</Text>
          </View>
          <View style={styles.speechRow}>
            <View style={styles.speechItem}>
              <Text style={styles.speechLabel}>아바타 → 나</Text>
              <View style={[styles.speechBadge, { backgroundColor: SPEECH_LEVELS[speech.toUser]?.color + '20' }]}>
                <Text style={[styles.speechBadgeText, { color: SPEECH_LEVELS[speech.toUser]?.color }]}>{SPEECH_LEVELS[speech.toUser]?.name_ko}</Text>
              </View>
            </View>
            <View style={styles.speechItem}>
              <Text style={styles.speechLabel}>나 → 아바타</Text>
              <View style={[styles.speechBadge, { backgroundColor: SPEECH_LEVELS[speech.fromUser]?.color + '20' }]}>
                <Text style={[styles.speechBadgeText, { color: SPEECH_LEVELS[speech.fromUser]?.color }]}>{SPEECH_LEVELS[speech.fromUser]?.name_ko}</Text>
              </View>
            </View>
          </View>
        </Card>
        <Card variant="elevated" style={styles.bioCard}>
          <View style={styles.bioHeader}><Text style={styles.bioTitle}>대화 가이드</Text></View>
          {generatingBio ? (
            <View style={styles.bioLoading}>
              <ActivityIndicator size="small" color="#6C3BFF" />
              <Text style={styles.bioLoadingText}>AI가 분석 중...</Text>
            </View>
          ) : (
            <>
              <Text style={styles.bioText}>{generatedBio}</Text>
              <TouchableOpacity style={styles.regenerateBtn} onPress={generateBio}>
                <RefreshCw size={16} color="#6C3BFF" />
                <Text style={styles.regenerateBtnText}>다시 생성</Text>
              </TouchableOpacity>
            </>
          )}
        </Card>
      </View>
    );
  };

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1: return renderStep1();
      case 2: return renderStep2();
      case 3: return renderStep3();
      case 4: return renderStep4();
      case 5: return renderStep5();
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
            <View style={[styles.stepDot, currentStep > step.id && styles.stepDotActive, currentStep === step.id && styles.stepDotCurrent]}>
              {currentStep > step.id ? (
                <Check size={14} color="#FFFFFF" />
              ) : (
                <Text style={[styles.stepNumber, currentStep >= step.id && styles.stepNumberActive]}>{step.id}</Text>
              )}
            </View>
            {index < STEPS.length - 1 && (
              <View style={[styles.stepLine, currentStep > step.id && styles.stepLineActive]} />
            )}
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
          {/* Show spinner on final step while saving */}
          {saving ? (
            <ActivityIndicator size="large" color="#6C3BFF" />
          ) : (
            <Button
              title={currentStep === STEPS.length ? '완료' : '다음'}
              onPress={handleNext}
              showArrow={currentStep < STEPS.length}
              disabled={!isStepValid()}
            />
          )}
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
  stepsRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingHorizontal: 20, marginBottom: 16 },
  stepIndicator: { flexDirection: 'row', alignItems: 'center' },
  stepDot: { width: 26, height: 26, borderRadius: 13, backgroundColor: '#E2E2EC', alignItems: 'center', justifyContent: 'center' },
  stepDotActive: { backgroundColor: '#6C3BFF' },
  stepDotCurrent: { backgroundColor: '#6C3BFF', borderWidth: 3, borderColor: '#C8B4F8' },
  stepNumber: { fontSize: 11, fontWeight: '600', color: '#6C6C80' },
  stepNumberActive: { color: '#FFFFFF' },
  stepLine: { width: 24, height: 2, backgroundColor: '#E2E2EC', marginHorizontal: 2 },
  stepLineActive: { backgroundColor: '#6C3BFF' },
  stepInfo: { alignItems: 'center', marginBottom: 16 },
  stepInfoTitle: { fontSize: 15, fontWeight: '700', color: '#1A1A2E' },
  stepInfoSubtitle: { fontSize: 11, color: '#6C6C80' },
  scrollContent: { paddingHorizontal: 20, paddingBottom: 100 },
  stepContent: {},
  stepTitle: { fontSize: 17, fontWeight: '700', color: '#1A1A2E', marginBottom: 6 },
  stepSubtitle: { fontSize: 13, color: '#6C6C80', marginBottom: 18, lineHeight: 18 },
  fieldLabel: { fontSize: 13, fontWeight: '600', color: '#1A1A2E', marginBottom: 10, marginTop: 14 },
  typeRow: { flexDirection: 'row', gap: 12, marginBottom: 8 },
  typeCard: { flex: 1, alignItems: 'center', paddingVertical: 16, backgroundColor: '#FFFFFF', borderRadius: 14, borderWidth: 2, borderColor: '#E2E2EC', gap: 8 },
  typeCardActive: { borderColor: '#9C27B0', backgroundColor: '#FAF5FF' },
  typeLabel: { fontSize: 14, fontWeight: '600', color: '#6C6C80' },
  optionRow: { flexDirection: 'row', gap: 10, marginBottom: 8 },
  optionButton: { flex: 1, paddingVertical: 12, borderRadius: 12, borderWidth: 1.5, borderColor: '#E2E2EC', backgroundColor: '#FFFFFF', alignItems: 'center' },
  optionButtonActive: { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  optionText: { fontSize: 14, fontWeight: '600', color: '#6C6C80' },
  optionTextActive: { color: '#FFFFFF' },
  colorGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 8 },
  colorButton: { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  colorButtonActive: { borderWidth: 3, borderColor: '#1A1A2E' },
  iconGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 8 },
  iconButton: { width: 44, height: 44, borderRadius: 12, backgroundColor: '#FFFFFF', borderWidth: 1.5, borderColor: '#E2E2EC', alignItems: 'center', justifyContent: 'center' },
  iconButtonActive: { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  roleCategory: { marginBottom: 16 },
  roleCategoryTitle: { fontSize: 12, fontWeight: '600', color: '#6C3BFF', marginBottom: 10, textTransform: 'uppercase' },
  roleGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  roleButton: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 20, backgroundColor: '#FFFFFF', borderWidth: 1.5, borderColor: '#E2E2EC' },
  roleButtonActive: { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  roleButtonText: { fontSize: 14, fontWeight: '500', color: '#6C6C80' },
  roleButtonTextActive: { color: '#FFFFFF' },
  customRoleSection: { marginTop: 8, paddingTop: 16, borderTopWidth: 1, borderTopColor: '#E2E2EC' },
  customRoleRow: { flexDirection: 'row', gap: 10 },
  customRoleInput: { flex: 1, backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 14, color: '#1A1A2E', borderWidth: 1, borderColor: '#E2E2EC' },
  customRoleSelected: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 10, backgroundColor: '#E8F5E9', padding: 10, borderRadius: 10 },
  customRoleSelectedText: { fontSize: 13, color: '#4CAF50', fontWeight: '500' },
  descInput: { backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 14, color: '#1A1A2E', borderWidth: 1, borderColor: '#E2E2EC', minHeight: 80, lineHeight: 20, marginBottom: 16 },
  descInputLarge: { backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 14, color: '#1A1A2E', borderWidth: 1, borderColor: '#E2E2EC', minHeight: 120, lineHeight: 20 },
  descHint: { flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginTop: 10, backgroundColor: '#F0EDFF', padding: 12, borderRadius: 10 },
  descHintText: { flex: 1, fontSize: 12, color: '#6C3BFF', lineHeight: 18 },
  tagGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  customInputRow: { flexDirection: 'row', gap: 10, marginTop: 4, marginBottom: 8 },
  customInput: { flex: 1, backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 12, fontSize: 14, color: '#1A1A2E', borderWidth: 1, borderColor: '#E2E2EC' },
  addButton: { width: 48, height: 48, borderRadius: 12, backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center' },
  addButtonGray: { backgroundColor: '#6C6C80' },
  addButtonDisabled: { opacity: 0.5 },
  memoInput: { backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 14, color: '#1A1A2E', borderWidth: 1, borderColor: '#E2E2EC', minHeight: 60, lineHeight: 20 },
  avatarPreview: { alignItems: 'center', paddingVertical: 20 },
  previewAvatar: { width: 80, height: 80, borderRadius: 40, alignItems: 'center', justifyContent: 'center', marginBottom: 12 },
  previewName: { fontSize: 20, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  previewRole: { fontSize: 14, color: '#6C6C80', marginBottom: 8 },
  previewTypeBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 6, borderRadius: 12, backgroundColor: '#F5F5FA' },
  previewTypeText: { fontSize: 12, fontWeight: '600' },
  speechCard: { marginBottom: 16 },
  speechHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  speechTitle: { fontSize: 15, fontWeight: '700', color: '#1A1A2E' },
  speechRow: { flexDirection: 'row', gap: 16 },
  speechItem: { flex: 1, alignItems: 'center' },
  speechLabel: { fontSize: 12, color: '#6C6C80', marginBottom: 8 },
  speechBadge: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12 },
  speechBadgeText: { fontSize: 14, fontWeight: '600' },
  bioCard: { marginBottom: 16 },
  bioHeader: { marginBottom: 12 },
  bioTitle: { fontSize: 15, fontWeight: '700', color: '#1A1A2E' },
  bioLoading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 20 },
  bioLoadingText: { fontSize: 14, color: '#6C6C80' },
  bioText: { fontSize: 14, color: '#1A1A2E', lineHeight: 22 },
  regenerateBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, marginTop: 16, paddingVertical: 10, backgroundColor: '#F0EDFF', borderRadius: 10 },
  regenerateBtnText: { fontSize: 13, fontWeight: '600', color: '#6C3BFF' },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
});