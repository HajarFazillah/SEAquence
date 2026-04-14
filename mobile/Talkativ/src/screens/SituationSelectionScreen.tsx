import React, { useState } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Check, Plus } from 'lucide-react-native';
import { Header, Card, Button, Icon } from '../components';
import { SITUATIONS, SITUATION_CATEGORIES } from '../constants';

// Mock custom situations
const mockCustomSituations = [
  {
    id: 'custom_1',
    name_ko: '도서관에서 공부',
    name_en: 'Library Study',
    description_ko: '도서관에서 친구와 함께 공부하는 상황',
    icon: 'book' as const,
    category: 'casual',
    isCustom: true,
  },
];

export default function SituationSelectionScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const avatar = route.params?.avatar;

  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedSituation, setSelectedSituation] = useState<string | null>(null);

  const allSituations = [...SITUATIONS, ...mockCustomSituations];

  const filteredSituations = selectedCategory === 'all'
    ? allSituations
    : allSituations.filter((s) => s.category === selectedCategory);

  const handleNext = () => {
    if (!selectedSituation) return;
    const situation = allSituations.find((s) => s.id === selectedSituation);
    navigation.navigate('SpeechRecommendation', { avatar, situation });
  };

  const handleCreateSituation = () => {
    navigation.navigate('CreateSituation');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="상황 선택" showBell />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        
        {/* Avatar info */}
        {avatar && (
          <View style={styles.avatarInfo}>
            <View style={[styles.avatarIcon, { backgroundColor: avatar.avatarBg }]}>
              <Icon name={avatar.icon || 'user'} size={24} color="#FFFFFF" />
            </View>
            <View>
              <Text style={styles.avatarName}>{avatar.name_ko}</Text>
              <Text style={styles.avatarRole}>{avatar.description_ko}</Text>
            </View>
          </View>
        )}

        {/* Section title */}
        <Text style={styles.sectionTitle}>어떤 상황에서 대화할까요?</Text>
        <Text style={styles.sectionSubtitle}>상황에 맞는 말투를 연습해보세요</Text>

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

        {/* Create New Situation Button */}
        <TouchableOpacity style={styles.createButton} onPress={handleCreateSituation}>
          <View style={styles.createIconContainer}>
            <Plus size={20} color="#6C3BFF" />
          </View>
          <Text style={styles.createText}>새 상황 만들기</Text>
        </TouchableOpacity>

        {/* Situation list */}
        <View style={styles.situationList}>
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
                    {(situation as any).isCustom && (
                      <View style={styles.customBadge}>
                        <Text style={styles.customBadgeText}>내가 만듦</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.situationDesc}>{situation.description_ko}</Text>
                </View>
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

  // Create Button
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F0EDFF',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
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

  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});
