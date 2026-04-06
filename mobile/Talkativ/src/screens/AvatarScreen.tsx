import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity, Modal, Alert, ActivityIndicator,
} from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { Plus, ChevronRight, Wand2, Shuffle, X, Edit, Trash2, Sparkles, User } from 'lucide-react-native';
import { Header, Card, SearchBar, StatusBadge, Tag, Icon } from '../components';
import { AVATAR_COLORS } from '../constants';
import { getMyAvatars, deleteAvatar, UserAvatar } from '../services/apiUser';

export default function AvatarScreen() {
  const navigation = useNavigation<any>();
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [avatars, setAvatars] = useState<UserAvatar[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<'all' | 'fictional' | 'real'>('all');

  // Re-fetches every time screen is focused (after create / edit / delete)
  useFocusEffect(
    useCallback(() => {
      const load = async () => {
        try {
          setLoading(true);
          const data = await getMyAvatars();
          setAvatars(data);
        } catch (e) {
          console.error('Failed to load avatars:', e);
        } finally {
          setLoading(false);
        }
      };
      load();
    }, [])
  );

  const filteredAvatars = avatars.filter((avatar) => {
    const matchesSearch =
      (avatar.name_ko ?? '').includes(search) ||
      (avatar.name_en ?? '').toLowerCase().includes(search.toLowerCase()) ||
      (avatar.relationship_description ?? '').includes(search);
    const matchesFilter = filterType === 'all' || avatar.avatar_type === filterType;
    return matchesSearch && matchesFilter;
  });

  const handleAvatarPress = (avatar: UserAvatar) => {
    navigation.navigate('AvatarDetail', { avatar });
  };

  const handleCreateFromScratch = () => {
    setShowCreateModal(false);
    navigation.navigate('CreateAvatar', { mode: 'scratch' });
  };

  const handleCreateRandom = () => {
    setShowCreateModal(false);
    const randomNames = ['박서연', '김민준', '이하윤', '정서준', '최지우'];
    const randomRoles = ['junior', 'friend', 'senior', 'colleague', 'classmate'];
    const randomInterests = [
      ['영화', '음악', '카페'],
      ['게임', '운동', 'K-POP'],
      ['독서', '요리', '여행'],
    ];
    const randomColors = Object.values(AVATAR_COLORS);

    const randomAvatar = {
      name_ko: randomNames[Math.floor(Math.random() * randomNames.length)],
      name_en: '',
      age: String(Math.floor(Math.random() * 20) + 20),
      role: randomRoles[Math.floor(Math.random() * randomRoles.length)],
      interests: randomInterests[Math.floor(Math.random() * randomInterests.length)],
      personality_traits: ['친절한', '유쾌한'],
      avatar_bg: randomColors[Math.floor(Math.random() * randomColors.length)],  // fixed
      difficulty: 'medium',
      avatar_type: 'fictional',                                                    // fixed
    };

    navigation.navigate('CreateAvatar', {
      mode: 'random',
      template: randomAvatar,
    });
  };

  const handleEditAvatar = (avatar: UserAvatar) => {
    navigation.navigate('CreateAvatar', { avatar, isEdit: true });
  };

  const handleDeleteAvatar = (avatar: UserAvatar) => {
    Alert.alert(
      '아바타 삭제',
      `${avatar.name_ko}을(를) 삭제하시겠습니까?`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteAvatar(String(avatar.id));
              setAvatars((prev) => prev.filter((a) => a.id !== avatar.id));
            } catch {
              Alert.alert('오류', '삭제에 실패했어요. 다시 시도해주세요.');
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.safe}>
      <Header title="아바타" showBack={false} showBell />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Search */}
        <SearchBar
          value={search}
          onChangeText={setSearch}
          placeholder="아바타 검색"
          style={styles.searchBar}
        />

        {/* Filter Tabs */}
        <View style={styles.filterRow}>
          <TouchableOpacity
            style={[styles.filterTab, filterType === 'all' && styles.filterTabActive]}
            onPress={() => setFilterType('all')}
          >
            <Text style={[styles.filterText, filterType === 'all' && styles.filterTextActive]}>
              전체 ({avatars.length})
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.filterTab, filterType === 'fictional' && styles.filterTabActive]}
            onPress={() => setFilterType('fictional')}
          >
            <Sparkles size={14} color={filterType === 'fictional' ? '#FFFFFF' : '#6C6C80'} />
            <Text style={[styles.filterText, filterType === 'fictional' && styles.filterTextActive]}>
              가상 인물
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.filterTab, filterType === 'real' && styles.filterTabActive]}
            onPress={() => setFilterType('real')}
          >
            <User size={14} color={filterType === 'real' ? '#FFFFFF' : '#6C6C80'} />
            <Text style={[styles.filterText, filterType === 'real' && styles.filterTextActive]}>
              실제 인물
            </Text>
          </TouchableOpacity>
        </View>

        {/* Create New Avatar Button */}
        <TouchableOpacity style={styles.createButton} onPress={() => setShowCreateModal(true)}>
          <View style={styles.createIconContainer}>
            <Plus size={24} color="#6C3BFF" />
          </View>
          <View style={styles.createTextContainer}>
            <Text style={styles.createTitle}>새 아바타 만들기</Text>
            <Text style={styles.createSubtitle}>나만의 대화 상대를 만들어보세요</Text>
          </View>
          <ChevronRight size={20} color="#6C3BFF" />
        </TouchableOpacity>

        {/* Avatar List */}
        <View style={styles.avatarList}>
          {loading ? (
            <ActivityIndicator size="large" color="#6C3BFF" style={{ marginTop: 40 }} />
          ) : (
            <>
              {filteredAvatars.map((avatar) => (
                <Card
                  key={avatar.id}
                  variant="elevated"
                  style={styles.avatarCard}
                  onPress={() => handleAvatarPress(avatar)}
                >
                  <View style={styles.avatarRow}>
                    <View style={[styles.avatarIcon, { backgroundColor: avatar.avatar_bg }]}>
                      <Icon name={avatar.icon || 'user'} size={28} color="#FFFFFF" />
                    </View>
                    <View style={styles.avatarInfo}>
                      <View style={styles.avatarNameRow}>
                        <Text style={styles.avatarName}>{avatar.name_ko}</Text>
                        <StatusBadge status={avatar.difficulty as 'easy' | 'medium' | 'hard'} />
                      </View>
                      <Text style={styles.avatarMeta}>
                        {avatar.name_en}{avatar.age ? ` · ${avatar.age}세` : ''}
                      </Text>
                      <Text style={styles.avatarDesc}>{avatar.relationship_description}</Text>
                    </View>
                  </View>

                  {/* Avatar Type Badge */}
                  <View style={styles.typeBadgeRow}>
                    <View style={[
                      styles.typeBadge,
                      avatar.avatar_type === 'fictional' ? styles.typeBadgeFictional : styles.typeBadgeReal,
                    ]}>
                      {avatar.avatar_type === 'fictional' ? (
                        <Sparkles size={12} color="#9C27B0" />
                      ) : (
                        <User size={12} color="#2196F3" />
                      )}
                      <Text style={[
                        styles.typeBadgeText,
                        avatar.avatar_type === 'fictional' ? styles.typeBadgeTextFictional : styles.typeBadgeTextReal,
                      ]}>
                        {avatar.avatar_type === 'fictional' ? '가상 인물' : '실제 인물'}
                      </Text>
                    </View>
                  </View>

                  {/* Interests */}
                  <View style={styles.interestsRow}>
                    {(avatar.interests ?? []).slice(0, 4).map((interest, i) => (
                      <Tag key={i} label={interest} variant="outline" />
                    ))}
                  </View>

                  {/* Action buttons */}
                  <View style={styles.actionButtons}>
                    <TouchableOpacity
                      style={styles.actionBtn}
                      onPress={() => handleEditAvatar(avatar)}
                    >
                      <Edit size={16} color="#6C3BFF" />
                      <Text style={styles.actionBtnText}>수정</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.actionBtn, styles.actionBtnDanger]}
                      onPress={() => handleDeleteAvatar(avatar)}
                    >
                      <Trash2 size={16} color="#E53935" />
                      <Text style={[styles.actionBtnText, styles.actionBtnTextDanger]}>삭제</Text>
                    </TouchableOpacity>
                  </View>
                </Card>
              ))}

              {/* Empty state */}
              {filteredAvatars.length === 0 && (
                <View style={styles.emptyState}>
                  <Icon name="search" size={48} color="#B0B0C5" />
                  <Text style={styles.emptyTitle}>
                    {search ? '검색 결과가 없어요' : '아직 만든 아바타가 없어요'}
                  </Text>
                  <Text style={styles.emptySubtitle}>
                    {search ? '다른 검색어를 입력해보세요' : '새 아바타를 만들어보세요!'}
                  </Text>
                  {!search && (
                    <TouchableOpacity style={styles.emptyButton} onPress={() => setShowCreateModal(true)}>
                      <Plus size={18} color="#FFFFFF" />
                      <Text style={styles.emptyButtonText}>아바타 만들기</Text>
                    </TouchableOpacity>
                  )}
                </View>
              )}
            </>
          )}
        </View>
      </ScrollView>

      {/* Create Avatar Modal */}
      <Modal
        visible={showCreateModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowCreateModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>아바타 만들기</Text>
              <TouchableOpacity onPress={() => setShowCreateModal(false)}>
                <X size={24} color="#6C6C80" />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalSubtitle}>어떻게 만들까요?</Text>

            <TouchableOpacity style={styles.createOption} onPress={handleCreateFromScratch}>
              <View style={[styles.createOptionIcon, { backgroundColor: '#F0EDFF' }]}>
                <Wand2 size={28} color="#6C3BFF" />
              </View>
              <View style={styles.createOptionText}>
                <Text style={styles.createOptionTitle}>처음부터 만들기</Text>
                <Text style={styles.createOptionDesc}>
                  이름, 성격, 관심사를 직접 설정해서 나만의 아바타를 만들어요
                </Text>
              </View>
              <ChevronRight size={20} color="#B0B0C5" />
            </TouchableOpacity>

            <TouchableOpacity style={styles.createOption} onPress={handleCreateRandom}>
              <View style={[styles.createOptionIcon, { backgroundColor: '#FFF0E0' }]}>
                <Shuffle size={28} color="#F4A261" />
              </View>
              <View style={styles.createOptionText}>
                <Text style={styles.createOptionTitle}>랜덤으로 만들기</Text>
                <Text style={styles.createOptionDesc}>
                  AI가 임의로 생성한 아바타를 수정해서 빠르게 만들어요
                </Text>
              </View>
              <ChevronRight size={20} color="#B0B0C5" />
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 32 },
  searchBar: { marginBottom: 12 },
  filterRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  filterTab: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20,
    backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E2E2EC',
  },
  filterTabActive: { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  filterText: { fontSize: 12, fontWeight: '600', color: '#6C6C80' },
  filterTextActive: { color: '#FFFFFF' },
  createButton: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#F0EDFF',
    borderRadius: 16, padding: 16, marginBottom: 20,
    borderWidth: 2, borderColor: '#6C3BFF', borderStyle: 'dashed',
  },
  createIconContainer: {
    width: 48, height: 48, borderRadius: 24, backgroundColor: '#FFFFFF',
    alignItems: 'center', justifyContent: 'center', marginRight: 14,
  },
  createTextContainer: { flex: 1 },
  createTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 2 },
  createSubtitle: { fontSize: 12, color: '#6C6C80' },
  avatarList: { gap: 14 },
  avatarCard: { position: 'relative' },
  avatarRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 14 },
  avatarIcon: { width: 56, height: 56, borderRadius: 28, alignItems: 'center', justifyContent: 'center' },
  avatarInfo: { flex: 1 },
  avatarNameRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 2 },
  avatarName: { fontSize: 17, fontWeight: '700', color: '#1A1A2E' },
  avatarMeta: { fontSize: 12, color: '#B0B0C5', marginBottom: 4 },
  avatarDesc: { fontSize: 13, color: '#6C6C80' },
  typeBadgeRow: { marginTop: 12 },
  typeBadge: {
    flexDirection: 'row', alignItems: 'center', gap: 4,
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12, alignSelf: 'flex-start',
  },
  typeBadgeFictional: { backgroundColor: '#F3E5F5' },
  typeBadgeReal: { backgroundColor: '#E3F2FD' },
  typeBadgeText: { fontSize: 11, fontWeight: '600' },
  typeBadgeTextFictional: { color: '#9C27B0' },
  typeBadgeTextReal: { color: '#2196F3' },
  interestsRow: {
    flexDirection: 'row', flexWrap: 'wrap', gap: 8,
    marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#F0F0F5',
  },
  actionButtons: {
    flexDirection: 'row', gap: 10, marginTop: 12,
    paddingTop: 12, borderTopWidth: 1, borderTopColor: '#F0F0F5',
  },
  actionBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 14, paddingVertical: 8, backgroundColor: '#F0EDFF', borderRadius: 8,
  },
  actionBtnDanger: { backgroundColor: '#FFEBEE' },
  actionBtnText: { fontSize: 13, fontWeight: '600', color: '#6C3BFF' },
  actionBtnTextDanger: { color: '#E53935' },
  emptyState: { alignItems: 'center', paddingVertical: 40 },
  emptyTitle: { fontSize: 16, fontWeight: '600', color: '#1A1A2E', marginTop: 16, marginBottom: 4 },
  emptySubtitle: { fontSize: 13, color: '#6C6C80', marginBottom: 20 },
  emptyButton: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: '#6C3BFF', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12,
  },
  emptyButtonText: { fontSize: 14, fontWeight: '600', color: '#FFFFFF' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: {
    backgroundColor: '#FFFFFF', borderTopLeftRadius: 24,
    borderTopRightRadius: 24, padding: 24, paddingBottom: 40,
  },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  modalTitle: { fontSize: 20, fontWeight: '700', color: '#1A1A2E' },
  modalSubtitle: { fontSize: 14, color: '#6C6C80', marginBottom: 24 },
  createOption: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: '#F7F7FB', borderRadius: 16, padding: 16, marginBottom: 12,
  },
  createOptionIcon: { width: 56, height: 56, borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  createOptionText: { flex: 1 },
  createOptionTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  createOptionDesc: { fontSize: 12, color: '#6C6C80', lineHeight: 18 },
});