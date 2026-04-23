import React, { useState } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, TouchableOpacity, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { 
  Coffee, Briefcase, GraduationCap, ShoppingBag,
  UtensilsCrossed, Users, Building2, Handshake, PartyPopper,
  MapPin,
} from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Header, Card, Button, InputField, Tag } from '../components';
import type { IconName } from '../components/Icon';

const CUSTOM_SITUATIONS_KEY = 'custom_situations';

const SITUATION_ICONS = [
  { id: 'coffee', icon: Coffee, label: '카페' },
  { id: 'utensils', icon: UtensilsCrossed, label: '식당' },
  { id: 'shoppingBag', icon: ShoppingBag, label: '쇼핑' },
  { id: 'graduationCap', icon: GraduationCap, label: '학교' },
  { id: 'briefcase', icon: Briefcase, label: '회사' },
  { id: 'building', icon: Building2, label: '사무실' },
  { id: 'users', icon: Users, label: '모임' },
  { id: 'handshake', icon: Handshake, label: '미팅' },
  { id: 'party', icon: PartyPopper, label: '파티' },
  { id: 'mapPin', icon: MapPin, label: '장소' },
];

const CATEGORIES = [
  { id: 'casual', label: '일상' },
  { id: 'service', label: '서비스' },
  { id: 'formal', label: '격식' },
  { id: 'work', label: '업무' },
];

const CONTEXT_SUGGESTIONS = [
  '처음 만나는 상황',
  '도움을 요청하는 상황',
  '주문하는 상황',
  '질문하는 상황',
  '인사하는 상황',
  '약속을 잡는 상황',
  '감사를 표현하는 상황',
  '사과하는 상황',
];

export default function CreateSituationScreen() {
  const navigation = useNavigation<any>();

  const [name, setName] = useState('');
  const [nameEn, setNameEn] = useState('');
  const [description, setDescription] = useState('');
  const [selectedIcon, setSelectedIcon] = useState('coffee');
  const [selectedCategory, setSelectedCategory] = useState('casual');
  const [contexts, setContexts] = useState<string[]>([]);
  const [customContext, setCustomContext] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const toggleContext = (context: string) => {
    if (contexts.includes(context)) {
      setContexts(contexts.filter((c) => c !== context));
    } else {
      setContexts([...contexts, context]);
    }
  };

  const addCustomContext = () => {
    if (customContext.trim() && !contexts.includes(customContext.trim())) {
      setContexts([...contexts, customContext.trim()]);
      setCustomContext('');
    }
  };

  const handleCreate = async () => {
    if (!name.trim() || !description.trim()) return;

    setIsSaving(true);

    try {
      // Build new situation object matching the SITUATIONS data structure
      const newSituation = {
        id: `custom_${Date.now()}`,
        name_ko: name.trim(),
        name_en: nameEn.trim(),
        description_ko: description.trim(),
        icon: selectedIcon as IconName,
        category: selectedCategory,
        contexts,
        isCustom: true,
      };

      // Load existing custom situations from AsyncStorage
      const existing = await AsyncStorage.getItem(CUSTOM_SITUATIONS_KEY);
      const existingList = existing ? JSON.parse(existing) : [];

      // Add new situation to the list
      const updatedList = [...existingList, newSituation];

      // Save back to AsyncStorage
      await AsyncStorage.setItem(CUSTOM_SITUATIONS_KEY, JSON.stringify(updatedList));

      Alert.alert('완료', `"${name}" 상황이 저장되었습니다.`, [
        { text: '확인', onPress: () => navigation.goBack() },
      ]);
    } catch (error) {
      console.log('Failed to save situation:', error);
      Alert.alert('오류', '상황 저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsSaving(false);
    }
  };

  const isValid = name.trim().length > 0 && description.trim().length > 0;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="새 상황 만들기" />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Name */}
        <InputField
          label="상황 이름 (한국어) *"
          value={name}
          onChangeText={setName}
          placeholder="예: 도서관에서 공부"
        />

        <InputField
          label="상황 이름 (영어)"
          value={nameEn}
          onChangeText={setNameEn}
          placeholder="예: Studying at Library"
        />

        {/* Description */}
        <InputField
          label="상황 설명 *"
          value={description}
          onChangeText={setDescription}
          placeholder="이 상황에서 어떤 대화가 이루어지나요?"
          multiline
          numberOfLines={3}
        />

        {/* Icon Selection */}
        <Text style={styles.fieldLabel}>아이콘 선택</Text>
        <View style={styles.iconGrid}>
          {SITUATION_ICONS.map((item) => (
            <TouchableOpacity
              key={item.id}
              style={[
                styles.iconButton,
                selectedIcon === item.id && styles.iconButtonActive,
              ]}
              onPress={() => setSelectedIcon(item.id)}
            >
              <item.icon 
                size={24} 
                color={selectedIcon === item.id ? '#FFFFFF' : '#6C6C80'} 
              />
              <Text style={[
                styles.iconLabel,
                selectedIcon === item.id && styles.iconLabelActive,
              ]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Category */}
        <Text style={styles.fieldLabel}>카테고리</Text>
        <View style={styles.categoryRow}>
          {CATEGORIES.map((cat) => (
            <TouchableOpacity
              key={cat.id}
              style={[
                styles.categoryButton,
                selectedCategory === cat.id && styles.categoryButtonActive,
              ]}
              onPress={() => setSelectedCategory(cat.id)}
            >
              <Text style={[
                styles.categoryText,
                selectedCategory === cat.id && styles.categoryTextActive,
              ]}>
                {cat.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Context Suggestions */}
        <Text style={styles.fieldLabel}>상황 맥락 (선택)</Text>
        <Text style={styles.fieldHint}>AI가 더 자연스러운 대화를 생성하는 데 도움이 됩니다</Text>
        
        <View style={styles.contextGrid}>
          {CONTEXT_SUGGESTIONS.map((context) => (
            <Tag
              key={context}
              label={context}
              selected={contexts.includes(context)}
              onPress={() => toggleContext(context)}
            />
          ))}
        </View>

        {/* Custom Context Input */}
        <View style={styles.customContextRow}>
          <View style={styles.customContextInput}>
            <InputField
              value={customContext}
              onChangeText={setCustomContext}
              placeholder="직접 입력..."
            />
          </View>
          <TouchableOpacity 
            style={styles.addButton}
            onPress={addCustomContext}
          >
            <Text style={styles.addButtonText}>추가</Text>
          </TouchableOpacity>
        </View>

        {/* Selected Contexts */}
        {contexts.length > 0 && (
          <View style={styles.selectedContexts}>
            <Text style={styles.selectedLabel}>선택된 맥락:</Text>
            <View style={styles.contextGrid}>
              {contexts.map((context) => (
                <Tag
                  key={context}
                  label={context}
                  selected
                  onPress={() => toggleContext(context)}
                />
              ))}
            </View>
          </View>
        )}

        {/* Preview */}
        <Text style={styles.fieldLabel}>미리보기</Text>
        <Card variant="elevated" style={styles.previewCard}>
          <View style={styles.previewRow}>
            <View style={[styles.previewIcon, { backgroundColor: '#6C3BFF' }]}>
              {SITUATION_ICONS.find((i) => i.id === selectedIcon)?.icon && 
                React.createElement(
                  SITUATION_ICONS.find((i) => i.id === selectedIcon)!.icon,
                  { size: 24, color: '#FFFFFF' }
                )
              }
            </View>
            <View style={styles.previewInfo}>
              <Text style={styles.previewName}>{name || '상황 이름'}</Text>
              <Text style={styles.previewDesc}>{description || '상황 설명'}</Text>
            </View>
          </View>
        </Card>

      </ScrollView>

      {/* Create Button */}
      <View style={styles.footer}>
        <Button
          title={isSaving ? '저장 중...' : '상황 만들기'}
          onPress={handleCreate}
          disabled={!isValid || isSaving}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1A1A2E',
    marginBottom: 10,
    marginTop: 16,
  },
  fieldHint: {
    fontSize: 12,
    color: '#6C6C80',
    marginTop: -6,
    marginBottom: 12,
  },

  iconGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 8,
  },
  iconButton: {
    width: '18%',
    aspectRatio: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#E2E2EC',
  },
  iconButtonActive: {
    backgroundColor: '#6C3BFF',
    borderColor: '#6C3BFF',
  },
  iconLabel: {
    fontSize: 10,
    color: '#6C6C80',
    marginTop: 4,
  },
  iconLabelActive: {
    color: '#FFFFFF',
  },

  categoryRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 8,
  },
  categoryButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E2EC',
    alignItems: 'center',
  },
  categoryButtonActive: {
    backgroundColor: '#6C3BFF',
    borderColor: '#6C3BFF',
  },
  categoryText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6C6C80',
  },
  categoryTextActive: {
    color: '#FFFFFF',
  },

  contextGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  customContextRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
    alignItems: 'flex-start',
  },
  customContextInput: {
    flex: 1,
  },
  addButton: {
    backgroundColor: '#6C3BFF',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 8,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  selectedContexts: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#F0EDFF',
    borderRadius: 12,
  },
  selectedLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C3BFF',
    marginBottom: 8,
  },

  previewCard: {
    marginTop: 8,
    marginBottom: 20,
  },
  previewRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  previewIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  previewInfo: {
    flex: 1,
  },
  previewName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A2E',
    marginBottom: 2,
  },
  previewDesc: {
    fontSize: 13,
    color: '#6C6C80',
  },

  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});