import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Check } from 'lucide-react-native';
import { Header, Card, Button, StatusBadge, SearchBar, Icon } from '../components';
import { SYSTEM_AVATARS } from '../constants';

const DIFFICULTY_ORDER = { easy: 0, medium: 1, hard: 2 };

export default function AvatarSelectionScreen() {
  const navigation = useNavigation<any>();
  const [search, setSearch] = useState('');
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);
  const [filterDifficulty, setFilterDifficulty] = useState<string | null>(null);

  const filteredAvatars = SYSTEM_AVATARS
    .filter((avatar) => {
      const matchesSearch = 
        avatar.name_ko.includes(search) || 
        avatar.name_en.toLowerCase().includes(search.toLowerCase()) ||
        avatar.description_ko.includes(search);
      const matchesDifficulty = !filterDifficulty || avatar.difficulty === filterDifficulty;
      return matchesSearch && matchesDifficulty;
    })
    .sort((a, b) => 
      DIFFICULTY_ORDER[a.difficulty as keyof typeof DIFFICULTY_ORDER] - 
      DIFFICULTY_ORDER[b.difficulty as keyof typeof DIFFICULTY_ORDER]
    );

  const handleNext = () => {
    if (!selectedAvatar) return;
    const avatar = SYSTEM_AVATARS.find((a) => a.id === selectedAvatar);
    navigation.navigate('SituationSelection', { avatar });
  };

  return (
    <SafeAreaView style={styles.safe}>
      <Header title="아바타 선택" showBack showBell />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Search */}
        <SearchBar
          value={search}
          onChangeText={setSearch}
          placeholder="아바타 검색"
          style={styles.searchBar}
        />

        {/* Difficulty filter */}
        <View style={styles.filterRow}>
          {['easy', 'medium', 'hard'].map((diff) => (
            <Button
              key={diff}
              title={diff === 'easy' ? '쉬움' : diff === 'medium' ? '보통' : '어려움'}
              variant={filterDifficulty === diff ? 'primary' : 'outline'}
              size="small"
              showArrow={false}
              onPress={() => setFilterDifficulty(filterDifficulty === diff ? null : diff)}
            />
          ))}
        </View>

        {/* Instructions */}
        <Text style={styles.instructions}>
          대화할 아바타를 선택하세요. 각 아바타는 다른 관계와 말투를 연습할 수 있습니다.
        </Text>

        {/* Avatar list */}
        <View style={styles.avatarList}>
          {filteredAvatars.map((avatar) => {
            const isSelected = selectedAvatar === avatar.id;

            return (
              <Card
                key={avatar.id}
                variant={isSelected ? 'outlined' : 'elevated'}
                onPress={() => setSelectedAvatar(avatar.id)}
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
                    <Text style={styles.avatarNameEn}>{avatar.name_en}</Text>
                    <Text style={styles.avatarDesc}>{avatar.description_ko}</Text>
                  </View>

                  {/* Checkmark */}
                  {isSelected && (
                    <Check size={24} color="#6C3BFF" />
                  )}
                </View>

                {/* Interests */}
                <View style={styles.interestsRow}>
                  <Text style={styles.interestsLabel}>관심사: </Text>
                  <Text style={styles.interestsText}>
                    {avatar.interests.join(', ')}
                  </Text>
                </View>
              </Card>
            );
          })}
        </View>

        {/* Empty state */}
        {filteredAvatars.length === 0 && (
          <View style={styles.emptyState}>
            <Icon name="search" size={48} color="#B0B0C5" />
            <Text style={styles.emptyText}>검색 결과가 없습니다</Text>
          </View>
        )}

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

  searchBar: { marginBottom: 16 },

  filterRow: { flexDirection: 'row', gap: 10, marginBottom: 16 },

  instructions: { fontSize: 13, color: '#6C6C80', lineHeight: 20, marginBottom: 20 },

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
  avatarNameRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 2 },
  avatarName: { fontSize: 17, fontWeight: '700', color: '#1A1A2E' },
  avatarNameEn: { fontSize: 12, color: '#B0B0C5', marginBottom: 4 },
  avatarDesc: { fontSize: 13, color: '#6C6C80' },

  interestsRow: { 
    flexDirection: 'row', 
    marginTop: 12, 
    paddingTop: 12, 
    borderTopWidth: 1, 
    borderTopColor: '#F0F0F5',
    flexWrap: 'wrap',
  },
  interestsLabel: { fontSize: 12, color: '#6C6C80', fontWeight: '600' },
  interestsText: { fontSize: 12, color: '#6C6C80', flex: 1 },

  emptyState: { alignItems: 'center', paddingVertical: 40 },
  emptyText: { fontSize: 14, color: '#6C6C80', marginTop: 12 },

  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});
