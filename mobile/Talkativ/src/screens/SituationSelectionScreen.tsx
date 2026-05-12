import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, TouchableOpacity, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, useFocusEffect } from '@react-navigation/native';
import { Check, Plus, Pencil, Trash2, Sparkles } from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Header, Card, Button, Icon } from '../components';
import { SITUATION_CATEGORIES } from '../constants';

const CUSTOM_SITUATIONS_KEY = 'custom_situations';

export default function SituationSelectionScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const avatar = route.params?.avatar;

  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSituation, setSelectedSituation] = useState<string | null>(null);
  const [customSituations, setCustomSituations] = useState<any[]>([]);

  // Load custom situations from AsyncStorage
  // useFocusEffect means this runs every time the screen comes into focus
  // So when user creates a new situation and comes back, the list refreshes
  useFocusEffect(
    useCallback(() => {
      const loadCustomSituations = async () => {
        try {
          const stored = await AsyncStorage.getItem(CUSTOM_SITUATIONS_KEY);
          if (stored) {
            setCustomSituations(JSON.parse(stored));
          }
        } catch (error) {
          console.log('Failed to load custom situations:', error);
        }
      };
      loadCustomSituations();
    }, [])
  );

  const avatarId = avatar?.id || avatar?.name_ko || avatar?.name || 'default_avatar';
  const allSituations = customSituations.filter((s) => s.avatarId === avatarId);

  const filteredSituations = selectedCategory === 'all'
    ? allSituations
    : allSituations.filter((s) => s.category === selectedCategory);

  const handleNext = () => {
    if (!selectedSituation) return;
    const situation = allSituations.find((s) => s.id === selectedSituation);
    navigation.navigate('SpeechRecommendation', { avatar, situation });
  };

  const handleCreateSituation = (mode: 'manual' | 'ai') => {
    navigation.navigate('CreateSituation', { avatar, mode });
  };

  const handleEditSituation = (situation: any) => {
    navigation.navigate('CreateSituation', { avatar, editing: situation, mode: 'manual' });
  };

  const handleDeleteSituation = (situation: any) => {
    Alert.alert(
      '상황 삭제',
      `"${situation.name_ko}" 상황을 삭제할까요?`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제',
          style: 'destructive',
          onPress: async () => {
            try {
              const next = customSituations.filter((s) => s.id !== situation.id);
              setCustomSituations(next);
              if (selectedSituation === situation.id) setSelectedSituation(null);
              await AsyncStorage.setItem(CUSTOM_SITUATIONS_KEY, JSON.stringify(next));
            } catch (e) {
              console.log('Failed to delete situation:', e);
              Alert.alert('오류', '삭제에 실패했습니다.');
            }
          },
        },
      ],
    );
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="상황 선택" showBell />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        
        {/* Avatar info */}
        {avatar && (
          <View style={styles.avatarInfo}>
            <View style={[styles.avatarIcon, { backgroundColor: avatar.avatarBg || avatar.avatar_bg || '#6C3BFF' }]}>
              <Icon name={avatar.icon || 'user'} size={24} color="#FFFFFF" />
            </View>
            <View>
              <Text style={styles.avatarName}>{avatar.name_ko}</Text>
              <Text style={styles.avatarRole}>{avatar.description_ko || avatar.description}</Text>
            </View>
          </View>
        )}

        {/* Section title */}
        <Text style={styles.sectionTitle}>어떤 상황에서 대화할까요?</Text>
        <Text style={styles.sectionSubtitle}>
          이 아바타와 어울리는 상황을 직접 만들거나 추천받아 시작하세요.
        </Text>

        {/* Category tabs */}
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false} 
          style={styles.categoryScroll}
          contentContainerStyle={styles.categoryContent}
        >
          {SITUATION_CATEGORIES.map((cat) => (
            <TouchableOpacity
              key={cat.id}
              style={[
                styles.categoryTab,
                selectedCategory === cat.id && styles.categoryTabActive,
              ]}
              onPress={() => setSelectedCategory(cat.id)}
            >
              <Icon 
                name={cat.icon} 
                size={16} 
                color={selectedCategory === cat.id ? '#FFFFFF' : '#6C6C80'} 
              />
              <Text style={[
                styles.categoryLabel,
                selectedCategory === cat.id && styles.categoryLabelActive,
              ]}>
                {cat.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Create New Situation Buttons */}
        <View style={styles.createChoiceRow}>
          <TouchableOpacity style={styles.createButton} onPress={() => handleCreateSituation('manual')}>
            <View style={styles.createIconContainer}>
              <Plus size={20} color="#6C3BFF" />
            </View>
            <View style={styles.createCopy}>
              <Text style={styles.createText}>직접 만들기</Text>
              <Text style={styles.createSubText}>내가 원하는 상황 입력</Text>
            </View>
          </TouchableOpacity>
          <TouchableOpacity style={styles.createButton} onPress={() => handleCreateSituation('ai')}>
            <View style={styles.createIconContainer}>
              <Sparkles size={20} color="#6C3BFF" />
            </View>
            <View style={styles.createCopy}>
              <Text style={styles.createText}>AI 추천</Text>
              <Text style={styles.createSubText}>아바타별 상황 제안</Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Situation list */}
        <View style={styles.situationList}>
          {filteredSituations.length === 0 && (
            <View style={styles.emptyState}>
              <Text style={styles.emptyTitle}>아직 이 아바타의 상황이 없어요</Text>
              <Text style={styles.emptyText}>
                같은 상황을 모든 아바타에게 쓰지 않도록, 먼저 이 관계에 맞는 상황을 만들어 주세요.
              </Text>
            </View>
          )}
          {filteredSituations.map((situation) => (
            <Card
              key={situation.id}
              variant={selectedSituation === situation.id ? 'outlined' : 'elevated'}
              onPress={() => setSelectedSituation(situation.id)}
              style={[
                styles.situationCard,
                selectedSituation === situation.id && styles.situationCardSelected,
              ]}
            >
              <View style={styles.situationRow}>
                <View style={styles.situationIcon}>
                  <Icon name={situation.icon} size={24} color="#6C3BFF" />
                </View>
                <View style={styles.situationInfo}>
                  <View style={styles.situationNameRow}>
                    <Text style={styles.situationName}>{situation.name_ko}</Text>
                    {situation.isCustom && (
                      <View style={styles.customBadge}>
                        <Text style={styles.customBadgeText}>
                          {situation.source === 'ai' ? 'AI 추천' : '내가 만듦'}
                        </Text>
                      </View>
                    )}
                  </View>
                  {!!situation.description_ko?.trim() && (
                    <Text style={styles.situationDesc}>{situation.description_ko}</Text>
                  )}
                </View>

                {situation.isCustom ? (
                  <View style={styles.cardActions}>
                    <TouchableOpacity
                      style={styles.cardActionBtn}
                      onPress={(e) => { e.stopPropagation?.(); handleEditSituation(situation); }}
                      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                    >
                      <Pencil size={16} color="#6C3BFF" />
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.cardActionBtn}
                      onPress={(e) => { e.stopPropagation?.(); handleDeleteSituation(situation); }}
                      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                    >
                      <Trash2 size={16} color="#E53935" />
                    </TouchableOpacity>
                  </View>
                ) : null}

                {selectedSituation === situation.id && (
                  <Check size={24} color="#6C3BFF" />
                )}
              </View>
            </Card>
          ))}
        </View>

      </ScrollView>

      {/* Next button */}
      <View style={styles.footer}>
        <Button
          title="다음"
          onPress={handleNext}
          showArrow
          disabled={!selectedSituation}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  avatarInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
    gap: 14,
  },
  avatarIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarName: { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },
  avatarRole: { fontSize: 13, color: '#6C6C80', marginTop: 2 },

  sectionTitle: { fontSize: 20, fontWeight: '700', color: '#1A1A2E', marginBottom: 6 },
  sectionSubtitle: { fontSize: 14, color: '#6C6C80', marginBottom: 20 },

  categoryScroll: { marginBottom: 16 },
  categoryContent: { gap: 10 },
  categoryTab: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    gap: 6,
    borderWidth: 1,
    borderColor: '#E2E2EC',
  },
  categoryTabActive: {
    backgroundColor: '#6C3BFF',
    borderColor: '#6C3BFF',
  },
  categoryLabel: { fontSize: 13, fontWeight: '500', color: '#6C6C80' },
  categoryLabelActive: { color: '#FFFFFF', fontWeight: '600' },

  createChoiceRow: {
    gap: 10,
    marginBottom: 16,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0EDFF',
    borderRadius: 12,
    padding: 14,
    gap: 10,
  },
  createIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  createText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6C3BFF',
  },
  createCopy: { flex: 1 },
  createSubText: { fontSize: 11, color: '#6C6C80', marginTop: 2 },

  emptyState: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E2EC',
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 6,
  },
  emptyText: {
    fontSize: 13,
    color: '#6C6C80',
    lineHeight: 19,
  },

  situationList: { gap: 12 },
  situationCard: { borderColor: '#E2E2EC' },
  situationCardSelected: { borderColor: '#6C3BFF', borderWidth: 2 },
  situationRow: { flexDirection: 'row', alignItems: 'center' },
  situationIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#F0EDFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  situationInfo: { flex: 1 },
  situationNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  situationName: { fontSize: 16, fontWeight: '600', color: '#1A1A2E' },
  situationDesc: { fontSize: 12, color: '#6C6C80' },
  customBadge: {
    backgroundColor: '#F0EDFF',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  customBadgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#6C3BFF',
  },

  cardActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginLeft: 8,
  },
  cardActionBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F7F7FB',
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
