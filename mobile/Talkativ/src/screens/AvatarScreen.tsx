import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Modal, Alert, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { Plus, ChevronRight, Wand2, Shuffle, X, Edit, Trash2, Sparkles, User, Heart } from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Header, Card, SearchBar, StatusBadge, Tag, Icon, CompatibilityRing, IconName } from '../components';
import { AVATAR_COLORS } from '../constants';
import { getMyAvatars, deleteAvatar, UserAvatar } from '../services/apiUser';

const FAVORITES_KEY = 'favorite_avatars';
const AI_SERVER = 'http://10.0.2.2:8000';

type RandomGender = 'male' | 'female' | 'other';
type RandomAvatarType = 'fictional' | 'real';
type RandomDifficulty = 'easy' | 'medium' | 'hard';

const RANDOM_NAMES: Array<{ ko: string; en: string; gender: RandomGender | 'neutral' }> = [
  { ko: '김하린', en: 'Harin Kim', gender: 'female' },
  { ko: '박서연', en: 'Seoyeon Park', gender: 'female' },
  { ko: '이하윤', en: 'Hayoon Lee', gender: 'female' },
  { ko: '최지우', en: 'Jiu Choi', gender: 'female' },
  { ko: '정유나', en: 'Yuna Jung', gender: 'female' },
  { ko: '강채원', en: 'Chaewon Kang', gender: 'female' },
  { ko: '윤수아', en: 'Sua Yoon', gender: 'female' },
  { ko: '장예린', en: 'Yerin Jang', gender: 'female' },
  { ko: '오다은', en: 'Daeun Oh', gender: 'female' },
  { ko: '한소윤', en: 'Soyoon Han', gender: 'female' },
  { ko: '김민준', en: 'Minjun Kim', gender: 'male' },
  { ko: '이서준', en: 'Seojun Lee', gender: 'male' },
  { ko: '박도윤', en: 'Doyoon Park', gender: 'male' },
  { ko: '최지호', en: 'Jiho Choi', gender: 'male' },
  { ko: '정하준', en: 'Hajun Jung', gender: 'male' },
  { ko: '강현우', en: 'Hyunwoo Kang', gender: 'male' },
  { ko: '윤태민', en: 'Taemin Yoon', gender: 'male' },
  { ko: '장건우', en: 'Geonwoo Jang', gender: 'male' },
  { ko: '오시우', en: 'Siwoo Oh', gender: 'male' },
  { ko: '한유준', en: 'Yujun Han', gender: 'male' },
  { ko: '김지원', en: 'Jiwon Kim', gender: 'neutral' },
  { ko: '이현서', en: 'Hyunseo Lee', gender: 'neutral' },
  { ko: '박하늘', en: 'Haneul Park', gender: 'neutral' },
  { ko: '최가온', en: 'Gaon Choi', gender: 'neutral' },
  { ko: '정도하', en: 'Doha Jung', gender: 'neutral' },
  { ko: '강윤재', en: 'Yunjae Kang', gender: 'neutral' },
  { ko: '윤민서', en: 'Minseo Yoon', gender: 'neutral' },
  { ko: '장서우', en: 'Seowoo Jang', gender: 'neutral' },
  { ko: '오유진', en: 'Yujin Oh', gender: 'neutral' },
  { ko: '한지안', en: 'Jian Han', gender: 'neutral' },
];

const RANDOM_ROLES = [
  { id: 'friend', label: '친구' },
  { id: 'close_friend', label: '절친' },
  { id: 'classmate', label: '동기' },
  { id: 'roommate', label: '룸메이트' },
  { id: 'club_member', label: '동아리 멤버' },
  { id: 'younger_sibling', label: '동생' },
  { id: 'older_brother', label: '형/오빠' },
  { id: 'older_sister', label: '누나/언니' },
  { id: 'cousin', label: '사촌' },
  { id: 'parent', label: '부모님' },
  { id: 'grandparent', label: '조부모님' },
  { id: 'junior', label: '후배' },
  { id: 'senior', label: '선배' },
  { id: 'professor', label: '교수님' },
  { id: 'teacher', label: '선생님' },
  { id: 'tutor', label: '튜터/과외선생' },
  { id: 'colleague', label: '동료' },
  { id: 'teammate', label: '팀원' },
  { id: 'team_leader', label: '팀장' },
  { id: 'boss', label: '상사/부장' },
  { id: 'ceo', label: '대표/사장님' },
  { id: 'intern', label: '인턴' },
  { id: 'client', label: '고객/클라이언트' },
  { id: 'staff', label: '직원/점원' },
  { id: 'stranger', label: '처음 만난 사람' },
  { id: 'neighbor', label: '이웃' },
  { id: 'doctor', label: '의사' },
  { id: 'delivery', label: '배달원' },
  { id: 'taxi_driver', label: '택시기사' },
];

const ROLE_AGE_RANGES: Record<string, [number, number]> = {
  younger_sibling: [12, 24],
  older_brother: [22, 42],
  older_sister: [22, 42],
  parent: [42, 68],
  grandparent: [64, 86],
  junior: [17, 28],
  senior: [21, 36],
  professor: [35, 70],
  teacher: [28, 62],
  tutor: [22, 38],
  team_leader: [30, 52],
  boss: [38, 62],
  ceo: [40, 70],
  intern: [20, 29],
  client: [28, 64],
  doctor: [30, 68],
  delivery: [22, 58],
  taxi_driver: [35, 70],
};

const RANDOM_GENDERS: RandomGender[] = ['male', 'female', 'other'];
const RANDOM_AVATAR_TYPES: RandomAvatarType[] = ['fictional', 'real'];
const RANDOM_DIFFICULTIES: RandomDifficulty[] = ['easy', 'medium', 'hard'];
const RANDOM_AVATAR_ICONS: IconName[] = [
  'user', 'users', 'smile', 'userCircle', 'crown', 'baby',
  'graduationCap', 'briefcase', 'building', 'heart', 'star',
  'sparkles', 'music', 'gamepad', 'dumbbell', 'palette', 'camera',
];

const RANDOM_PERSONALITY_TRAITS = [
  '친절한', '유쾌한', '차분한', '활발한', '내성적인', '외향적인',
  '진지한', '유머러스', '다정한', '쿨한', '열정적인', '느긋한',
  '꼼꼼한', '긍정적인', '현실적인', '감성적인', '이성적인', '눈치가 빠른',
  '장난기 있는', '책임감 있는', '호기심 많은', '솔직한',
];

const RANDOM_INTERESTS = [
  'K-POP', '영화', '드라마', '음악', '독서', '여행', '카페', '음식',
  '운동', '게임', '패션', '사진', '요리', '미술', '역사', '과학',
  '비즈니스', '기술', '경제', '스포츠', '자기계발', '애니메이션',
  '반려동물', '산책', '웹툰', '공연', '언어 공부', '맛집 탐방',
];

const RANDOM_DISLIKES = [
  '정치', '종교', '논쟁', '스포츠', '연예인 가십', '학업 스트레스',
  '취업 압박', '결혼/연애 압박', '외모 이야기', '돈 이야기',
  '무례한 말투', '지나친 농담',
];

const RANDOM_SPEAKING_STYLES = [
  '짧고 자연스럽게 말하는 편',
  '상대방 말을 잘 듣고 차분하게 답하는 편',
  '가벼운 농담을 섞지만 선을 넘지 않는 편',
  '따뜻하고 다정하게 리액션하는 편',
  '현실적인 조언을 또렷하게 해주는 편',
  '편안한 친구처럼 일상적인 표현을 자주 쓰는 편',
  '조금 신중하고 예의 바르게 말하는 편',
  '호기심이 많아서 질문을 자연스럽게 이어가는 편',
];

const RANDOM_RELATIONSHIP_NOTES = [
  '처음에는 조금 어색하지만 금방 편해질 수 있는 사이입니다.',
  '가벼운 일상 이야기에서 시작하면 자연스럽게 대화가 이어집니다.',
  '서로의 관심사를 천천히 알아가는 분위기가 잘 어울립니다.',
  '예의를 지키면서도 너무 딱딱하지 않게 대화하는 관계입니다.',
  '작은 근황이나 취미 이야기를 편하게 나누기 좋은 사이입니다.',
];

const RANDOM_MEMOS = [
  '사용자가 한국어 표현을 자연스럽게 연습할 수 있도록 짧은 질문을 가끔 던집니다.',
  '너무 과장된 반응보다 실제 사람처럼 담백하고 구체적으로 답합니다.',
  '사용자가 실수하면 대화를 끊지 않고 자연스럽게 고쳐 줍니다.',
  '답변은 친근하지만 과하게 들뜨지 않게 유지합니다.',
  '한국어 학습에 도움이 되도록 쉬운 대안 표현을 함께 떠올립니다.',
];

const randomItem = <T,>(items: T[]): T =>
  items[Math.floor(Math.random() * items.length)];

const randomInt = (min: number, max: number) =>
  Math.floor(Math.random() * (max - min + 1)) + min;

const randomItems = <T,>(items: T[], min: number, max: number): T[] => {
  const count = randomInt(min, max);
  const shuffled = [...items].sort(() => Math.random() - 0.5);
  return shuffled.slice(0, count);
};

const buildRandomAvatarTemplate = () => {
  const gender = randomItem(RANDOM_GENDERS);
  const names = RANDOM_NAMES.filter(item => gender === 'other' || item.gender === gender || item.gender === 'neutral');
  const name = randomItem(names.length > 0 ? names : RANDOM_NAMES);
  const role = randomItem(RANDOM_ROLES);
  const ageRange = ROLE_AGE_RANGES[role.id] || [18, 45];
  const personality_traits = randomItems(RANDOM_PERSONALITY_TRAITS, 2, 4);
  const interests = randomItems(RANDOM_INTERESTS, 3, 5);
  const dislikes = randomItems(RANDOM_DISLIKES, 0, 2);
  const speaking_style = randomItem(RANDOM_SPEAKING_STYLES);
  const relationshipNote = randomItem(RANDOM_RELATIONSHIP_NOTES);

  return {
    name_ko: name.ko,
    name_en: name.en,
    age: String(randomInt(ageRange[0], ageRange[1])),
    gender,
    avatar_type: randomItem(RANDOM_AVATAR_TYPES),
    role: role.id,
    custom_role: '',
    relationship_description: `${role.label} 관계입니다. ${relationshipNote}`,
    description:
      `${name.ko}은(는) ${personality_traits.join(', ')} 성격입니다. ` +
      `${interests.slice(0, 3).join(', ')} 이야기를 좋아하고, ${speaking_style}.`,
    personality_traits,
    speaking_style,
    interests,
    dislikes,
    avatar_bg: randomItem(Object.values(AVATAR_COLORS)),
    icon: randomItem(RANDOM_AVATAR_ICONS),
    difficulty: randomItem(RANDOM_DIFFICULTIES),
    memo: randomItem(RANDOM_MEMOS),
  };
};

export default function AvatarScreen() {
  const navigation = useNavigation<any>();
  const [search,          setSearch]          = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [avatars,         setAvatars]         = useState<UserAvatar[]>([]);
  const [loading,         setLoading]         = useState(true);
  const [filterType,      setFilterType]      = useState<'all' | 'fictional' | 'real' | 'favorites'>('all');
  const [favoriteIds,     setFavoriteIds]     = useState<string[]>([]);
  const [compatScores,    setCompatScores]    = useState<Record<number, number>>({});

  const fetchCompatibilityScores = async (
    avatarList:    UserAvatar[],
    userInterests: string[]
  ): Promise<Record<number, number>> => {
    if (!avatarList.length) return {};
    try {
      const res = await fetch(`${AI_SERVER}/api/v1/compatibility/batch-simple`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_profile: { name: '나', likes: userInterests, dislikes: [] },
          avatars: avatarList.map(a => ({
            id:                 String(a.id),
            name_ko:            a.name_ko,
            role:               a.role               || 'friend',
            interests:          a.interests          || [],
            personality_traits: a.personality_traits || [],
            dislikes:           a.dislikes           || [],
          })),
        }),
      });
      if (!res.ok) return {};
      const data = await res.json();
      const scores: Record<number, number> = {};
      (data.results || []).forEach((r: any, idx: number) => {
        const avatar = avatarList[idx];
        if (avatar) scores[avatar.id] = Math.round(r.overall_score || 0);
      });
      return scores;
    } catch {
      return {};
    }
  };
  // ── 아바타 + 궁합 로드 ─────────────────────────────────────────────────────
  useFocusEffect(
    useCallback(() => {
      const load = async () => {
        try {
          setLoading(true);
          const data = await getMyAvatars();
          setAvatars(data);

          // Load favorite IDs from AsyncStorage
          const stored = await AsyncStorage.getItem(FAVORITES_KEY);
          setFavoriteIds(stored ? JSON.parse(stored) : []);
          if (data.length > 0) {
            const userInterests = data
              .flatMap(a => a.interests || [])
              .slice(0, 5);
            fetchCompatibilityScores(data, userInterests)
              .then(scores => setCompatScores(scores))
              .catch(() => {});
          }
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

    let matchesFilter = true;
    if (filterType === 'fictional') matchesFilter = avatar.avatar_type === 'fictional';
    else if (filterType === 'real') matchesFilter = avatar.avatar_type === 'real';
    else if (filterType === 'favorites') matchesFilter = favoriteIds.includes(String(avatar.id));

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
    navigation.navigate('CreateAvatar', {
      mode: 'random',
      template: buildRandomAvatarTemplate(),
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
              setAvatars(prev => prev.filter(a => a.id !== avatar.id));
              setCompatScores(prev => {
                const next = { ...prev };
                delete next[avatar.id];
                return next;
              });
            } catch {
              Alert.alert('오류', '삭제에 실패했어요. 다시 시도해주세요.');
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
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
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.filterScroll}
          contentContainerStyle={styles.filterRow}
        >
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

          <TouchableOpacity
            style={[styles.filterTab, styles.filterTabHeart, filterType === 'favorites' && styles.filterTabFavorite]}
            onPress={() => setFilterType('favorites')}
          >
            <Heart
              size={14}
              color={filterType === 'favorites' ? '#FFFFFF' : '#E53935'}
              fill={filterType === 'favorites' ? '#FFFFFF' : '#E53935'}
            />
          </TouchableOpacity>
        </ScrollView>

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
              {filteredAvatars.map((avatar) => {
                const score = compatScores[avatar.id];
                return (
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
                          {favoriteIds.includes(String(avatar.id)) && (
                            <Heart size={16} color="#E53935" fill="#E53935" />
                          )}
                        </View>
                        <Text style={styles.avatarMeta}>
                          {avatar.name_en}{avatar.age ? ` · ${avatar.age}세` : ''}
                        </Text>
                        <Text style={styles.avatarDesc}>{avatar.relationship_description}</Text>
                      </View>

                      {/* 궁합 링 */}
                      {score !== undefined ? (
                        <CompatibilityRing percentage={score} size={52} />
                      ) : (
                        <View style={styles.compatPlaceholder} />
                      )}
                    </View>

                    {/* Avatar Type Badge */}
                    <View style={styles.typeBadgeRow}>
                      <View style={[
                        styles.typeBadge,
                        avatar.avatar_type === 'fictional' ? styles.typeBadgeFictional : styles.typeBadgeReal,
                      ]}>
                        {avatar.avatar_type === 'fictional'
                          ? <Sparkles size={12} color="#9C27B0" />
                          : <User size={12} color="#2196F3" />}
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
                      <TouchableOpacity style={styles.actionBtn} onPress={() => handleEditAvatar(avatar)}>
                        <Edit size={16} color="#6C3BFF" />
                        <Text style={styles.actionBtnText}>수정</Text>
                      </TouchableOpacity>
                      <TouchableOpacity style={[styles.actionBtn, styles.actionBtnDanger]} onPress={() => handleDeleteAvatar(avatar)}>
                        <Trash2 size={16} color="#E53935" />
                        <Text style={[styles.actionBtnText, styles.actionBtnTextDanger]}>삭제</Text>
                      </TouchableOpacity>
                    </View>
                  </Card>
                );
              })}

              {filteredAvatars.length === 0 && (
                <View style={styles.emptyState}>
                  <Icon name="search" size={48} color="#B0B0C5" />
                  <Text style={styles.emptyTitle}>
                    {filterType === 'favorites'
                      ? '즐겨찾기한 아바타가 없어요'
                      : search ? '검색 결과가 없어요' : '아직 만든 아바타가 없어요'}
                  </Text>
                  <Text style={styles.emptySubtitle}>
                    {filterType === 'favorites'
                      ? '아바타 상세 페이지에서 ♡를 눌러 추가해보세요'
                      : search ? '다른 검색어를 입력해보세요' : '새 아바타를 만들어보세요!'}
                  </Text>
                  {!search && filterType !== 'favorites' && (
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
      <Modal visible={showCreateModal} transparent animationType="fade" onRequestClose={() => setShowCreateModal(false)}>
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
                <Text style={styles.createOptionDesc}>이름, 성격, 관심사를 직접 설정해서 나만의 아바타를 만들어요</Text>
              </View>
              <ChevronRight size={20} color="#B0B0C5" />
            </TouchableOpacity>
            <TouchableOpacity style={styles.createOption} onPress={handleCreateRandom}>
              <View style={[styles.createOptionIcon, { backgroundColor: '#FFF0E0' }]}>
                <Shuffle size={28} color="#F4A261" />
              </View>
              <View style={styles.createOptionText}>
                <Text style={styles.createOptionTitle}>랜덤으로 만들기</Text>
                <Text style={styles.createOptionDesc}>AI가 임의로 생성한 아바타를 수정해서 빠르게 만들어요</Text>
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
  safe:    { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 32 },
  searchBar:         { marginBottom: 12 },
  filterScroll:      { marginBottom: 16 },
  filterRow:         { flexDirection: 'row', gap: 8 },
  filterTab:         { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E2E2EC' },
  filterTabActive:   { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  filterTabHeart:    { paddingHorizontal: 12, paddingVertical: 8 },
  filterTabFavorite: { backgroundColor: '#E53935', borderColor: '#E53935', paddingHorizontal: 12, paddingVertical: 8 },
  filterText:        { fontSize: 12, fontWeight: '600', color: '#6C6C80' },
  filterTextActive:  { color: '#FFFFFF' },

  createButton:        { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F0EDFF', borderRadius: 16, padding: 16, marginBottom: 20, borderWidth: 2, borderColor: '#6C3BFF', borderStyle: 'dashed' },
  createIconContainer: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  createTextContainer: { flex: 1 },
  createTitle:         { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 2 },
  createSubtitle:      { fontSize: 12, color: '#6C6C80' },

  avatarList:    { gap: 14 },
  avatarCard:    { position: 'relative' },
  avatarRow:     { flexDirection: 'row', alignItems: 'flex-start', gap: 14 },
  avatarIcon:    { width: 56, height: 56, borderRadius: 28, alignItems: 'center', justifyContent: 'center' },
  avatarInfo:    { flex: 1 },
  avatarNameRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 2 },
  avatarName:    { fontSize: 17, fontWeight: '700', color: '#1A1A2E' },
  avatarMeta:    { fontSize: 12, color: '#B0B0C5', marginBottom: 4 },
  avatarDesc:    { fontSize: 13, color: '#6C6C80' },

  compatPlaceholder: { width: 52, height: 52 },

  typeBadgeRow:           { marginTop: 12 },
  typeBadge:              { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12, alignSelf: 'flex-start' },
  typeBadgeFictional:     { backgroundColor: '#F3E5F5' },
  typeBadgeReal:          { backgroundColor: '#E3F2FD' },
  typeBadgeText:          { fontSize: 11, fontWeight: '600' },
  typeBadgeTextFictional: { color: '#9C27B0' },
  typeBadgeTextReal:      { color: '#2196F3' },

  interestsRow:  { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#F0F0F5' },

  actionButtons:       { flexDirection: 'row', gap: 10, marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#F0F0F5' },
  actionBtn:           { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 14, paddingVertical: 8, backgroundColor: '#F0EDFF', borderRadius: 8 },
  actionBtnDanger:     { backgroundColor: '#FFEBEE' },
  actionBtnText:       { fontSize: 13, fontWeight: '600', color: '#6C3BFF' },
  actionBtnTextDanger: { color: '#E53935' },

  emptyState:      { alignItems: 'center', paddingVertical: 40 },
  emptyTitle:      { fontSize: 16, fontWeight: '600', color: '#1A1A2E', marginTop: 16, marginBottom: 4 },
  emptySubtitle:   { fontSize: 13, color: '#6C6C80', marginBottom: 20 },
  emptyButton:     { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#6C3BFF', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 12 },
  emptyButtonText: { fontSize: 14, fontWeight: '600', color: '#FFFFFF' },

  modalOverlay:  { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent:  { backgroundColor: '#FFFFFF', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, paddingBottom: 40 },
  modalHeader:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  modalTitle:    { fontSize: 20, fontWeight: '700', color: '#1A1A2E' },
  modalSubtitle: { fontSize: 14, color: '#6C6C80', marginBottom: 24 },

  createOption:      { flexDirection: 'row', alignItems: 'center', backgroundColor: '#F7F7FB', borderRadius: 16, padding: 16, marginBottom: 12 },
  createOptionIcon:  { width: 56, height: 56, borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  createOptionText:  { flex: 1 },
  createOptionTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 4 },
  createOptionDesc:  { fontSize: 12, color: '#6C6C80', lineHeight: 18 },
});
