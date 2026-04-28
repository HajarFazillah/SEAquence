import React, { useCallback, useMemo, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import { Clock3, ChevronRight, Sparkles, UserRound, SearchX } from 'lucide-react-native';
import { Card, Header, SearchBar, Tag, Icon } from '../components';
import { ConversationPreview, getAllConversationPreviews } from '../services/conversationPreview';
import { getMyAvatars, UserAvatar } from '../services/apiUser';

type AvatarFilter = 'all' | 'real' | 'fictional';
type TimeFilter = 'all' | 'today' | 'week';

const formatRelativeTime = (iso?: string): string => {
  if (!iso) return '방금 전';
  const diffMs = Date.now() - new Date(iso).getTime();
  const diffMin = Math.max(0, Math.floor(diffMs / 60000));

  if (diffMin < 1) return '방금 전';
  if (diffMin < 60) return `${diffMin}분 전`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}시간 전`;
  const diffDay = Math.floor(diffHour / 24);
  if (diffDay < 7) return `${diffDay}일 전`;
  return new Intl.DateTimeFormat('ko-KR', { month: 'short', day: 'numeric' }).format(new Date(iso));
};

const formatDateLabel = (iso?: string): string => {
  if (!iso) return '';
  return new Intl.DateTimeFormat('ko-KR', {
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(iso));
};

const difficultyLabel = (difficulty?: string) => {
  if (difficulty === 'easy') return '쉬운 대화';
  if (difficulty === 'hard') return '도전 대화';
  return '보통 난이도';
};

const avatarTypeLabel = (avatarType?: string) =>
  avatarType === 'real' ? '실물 아바타' : '가상 인물';

const withinTimeFilter = (iso: string, filter: TimeFilter) => {
  if (filter === 'all') return true;
  const diffMs = Date.now() - new Date(iso).getTime();
  if (filter === 'today') return diffMs <= 24 * 60 * 60 * 1000;
  return diffMs <= 7 * 24 * 60 * 60 * 1000;
};

export default function ConversationHistoryScreen() {
  const navigation = useNavigation<any>();
  const [loading, setLoading] = useState(true);
  const [historyItems, setHistoryItems] = useState<ConversationPreview[]>([]);
  const [avatarMap, setAvatarMap] = useState<Record<string, UserAvatar>>({});
  const [search, setSearch] = useState('');
  const [avatarFilter, setAvatarFilter] = useState<AvatarFilter>('all');
  const [timeFilter, setTimeFilter] = useState<TimeFilter>('all');

  useFocusEffect(
    useCallback(() => {
      let mounted = true;
      setLoading(true);

      Promise.allSettled([getAllConversationPreviews(), getMyAvatars()])
        .then(([previewsResult, avatarsResult]) => {
          if (!mounted) return;

          if (previewsResult.status === 'fulfilled') {
            setHistoryItems(previewsResult.value);
          } else {
            setHistoryItems([]);
          }

          if (avatarsResult.status === 'fulfilled') {
            const nextMap = avatarsResult.value.reduce<Record<string, UserAvatar>>((acc, avatar) => {
              acc[String(avatar.id)] = avatar;
              return acc;
            }, {});
            setAvatarMap(nextMap);
          } else {
            setAvatarMap({});
          }
        })
        .finally(() => {
          if (mounted) setLoading(false);
        });

      return () => {
        mounted = false;
      };
    }, [])
  );

  const filteredItems = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return historyItems.filter((item) => {
      const avatar = avatarMap[item.avatarId];
      const matchesSearch = !needle || [
        item.avatarName,
        item.situation,
        avatar?.role,
        ...(avatar?.interests || []),
      ].some((value) => String(value || '').toLowerCase().includes(needle));

      const matchesAvatarType =
        avatarFilter === 'all' ||
        (avatarFilter === 'real' && avatar?.avatar_type === 'real') ||
        (avatarFilter === 'fictional' && avatar?.avatar_type === 'fictional');

      const matchesTime = withinTimeFilter(item.updatedAt, timeFilter);

      return matchesSearch && matchesAvatarType && matchesTime;
    });
  }, [avatarFilter, avatarMap, historyItems, search, timeFilter]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title="대화 기록" showBack />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.heroCard}>
          <Text style={styles.heroEyebrow}>Conversation Archive</Text>
          <Text style={styles.heroTitle}>이전 대화를 한눈에 다시 찾아보세요</Text>
          <Text style={styles.heroSubtitle}>아바타 유형, 최근 대화 시점, 상황 기준으로 빠르게 고를 수 있어요.</Text>
        </View>

        <SearchBar
          value={search}
          onChangeText={setSearch}
          placeholder="아바타 이름이나 상황으로 검색"
          style={styles.searchBar}
        />

        <View style={styles.filterSection}>
          <Text style={styles.filterLabel}>아바타 유형</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterRow}>
            <Tag label="전체" selected={avatarFilter === 'all'} onPress={() => setAvatarFilter('all')} />
            <Tag label="실물 아바타" selected={avatarFilter === 'real'} onPress={() => setAvatarFilter('real')} />
            <Tag label="가상 인물" selected={avatarFilter === 'fictional'} onPress={() => setAvatarFilter('fictional')} />
          </ScrollView>
        </View>

        <View style={styles.filterSection}>
          <Text style={styles.filterLabel}>최근 시점</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filterRow}>
            <Tag label="전체" selected={timeFilter === 'all'} onPress={() => setTimeFilter('all')} />
            <Tag label="24시간" selected={timeFilter === 'today'} onPress={() => setTimeFilter('today')} />
            <Tag label="최근 7일" selected={timeFilter === 'week'} onPress={() => setTimeFilter('week')} />
          </ScrollView>
        </View>

        {loading ? (
          <View style={styles.loadingWrap}>
            <ActivityIndicator size="large" color="#6C3BFF" />
          </View>
        ) : filteredItems.length === 0 ? (
          <View style={styles.emptyState}>
            <SearchX size={46} color="#B8B8C8" />
            <Text style={styles.emptyTitle}>{historyItems.length === 0 ? '아직 저장된 대화 기록이 없어요' : '조건에 맞는 기록이 없어요'}</Text>
            <Text style={styles.emptySubtitle}>{historyItems.length === 0 ? '대화를 시작하면 최근 기록이 여기에 쌓입니다.' : '검색어나 필터를 조금 바꿔서 다시 찾아보세요.'}</Text>
          </View>
        ) : (
          <View style={styles.list}>
            {filteredItems.map((item) => {
              const avatar = avatarMap[item.avatarId];
              const avatarType = avatar?.avatar_type || 'fictional';
              const situation = item.situation || '일상 대화';

              return (
                <Card
                  key={item.sessionId}
                  variant="elevated"
                  style={styles.historyCard}
                  onPress={() => navigation.navigate('Chat', {
                    avatar: avatar || {
                      id: item.avatarId,
                      name_ko: item.avatarName,
                    },
                    situation: item.situation ? { name_ko: item.situation } : undefined,
                    sessionId: item.sessionId,
                  })}
                >
                  <View style={styles.cardTop}>
                    <View style={[styles.avatarStub, { backgroundColor: avatar?.avatar_bg || '#F0EDFF' }]}>
                      {avatar?.icon ? (
                        <Icon name={avatar.icon} size={18} color="#FFFFFF" />
                      ) : avatarType === 'real' ? (
                        <UserRound size={18} color="#FFFFFF" />
                      ) : (
                        <Sparkles size={18} color="#FFFFFF" />
                      )}
                    </View>

                    <View style={styles.cardCopy}>
                      <View style={styles.nameRow}>
                        <Text style={styles.avatarName}>{item.avatarName || avatar?.name_ko || '대화 상대'}</Text>
                        <View style={styles.timeCapsule}>
                          <Clock3 size={12} color="#8D7BFF" />
                          <Text style={styles.timeText}>{formatRelativeTime(item.updatedAt)}</Text>
                        </View>
                      </View>
                      <Text style={styles.situationTitle}>{situation}</Text>
                      <Text style={styles.dateText}>{formatDateLabel(item.updatedAt)}</Text>
                    </View>

                    <ChevronRight size={18} color="#C4BDF5" />
                  </View>

                  <View style={styles.metaTags}>
                    <Tag
                      label={avatarTypeLabel(avatarType)}
                      variant="filled"
                      color={avatarType === 'real' ? '#2F80ED' : '#A855F7'}
                    />
                    <Tag label={difficultyLabel(avatar?.difficulty)} variant="outline" />
                    <Tag label={situation} variant="outline" />
                  </View>
                </Card>
              );
            })}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 32 },
  heroCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#1A1A2E',
    shadowOpacity: 0.05,
    shadowRadius: 16,
    elevation: 2,
  },
  heroEyebrow: { fontSize: 12, fontWeight: '700', color: '#8D7BFF', marginBottom: 8 },
  heroTitle: { fontSize: 22, fontWeight: '700', color: '#1A1A2E', lineHeight: 30, marginBottom: 8 },
  heroSubtitle: { fontSize: 13, lineHeight: 20, color: '#6D6D84' },
  searchBar: { marginBottom: 16 },
  filterSection: { marginBottom: 14 },
  filterLabel: { fontSize: 13, fontWeight: '600', color: '#54546A', marginBottom: 10 },
  filterRow: { gap: 8, paddingRight: 12 },
  loadingWrap: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 80 },
  emptyState: { alignItems: 'center', paddingTop: 88, paddingHorizontal: 16 },
  emptyTitle: { marginTop: 14, fontSize: 17, fontWeight: '700', color: '#1A1A2E', textAlign: 'center' },
  emptySubtitle: { marginTop: 8, fontSize: 13, lineHeight: 20, color: '#7A7A92', textAlign: 'center' },
  list: { gap: 14, paddingTop: 6 },
  historyCard: { borderRadius: 24, padding: 18 },
  cardTop: { flexDirection: 'row', alignItems: 'center' },
  avatarStub: {
    width: 48,
    height: 48,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  cardCopy: { flex: 1, marginRight: 10 },
  nameRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 6 },
  avatarName: { fontSize: 16, fontWeight: '700', color: '#1A1A2E', flex: 1 },
  timeCapsule: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#F3F0FF',
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  timeText: { fontSize: 11, fontWeight: '600', color: '#6C3BFF' },
  situationTitle: { fontSize: 15, fontWeight: '600', color: '#36364B', marginBottom: 4 },
  dateText: { fontSize: 12, color: '#8B8BA3' },
  metaTags: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 14 },
});
