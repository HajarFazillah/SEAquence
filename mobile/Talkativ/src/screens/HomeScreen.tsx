import React, { useEffect, useRef, useCallback, useState, useMemo } from 'react';
import Svg, { Circle, G } from 'react-native-svg';
import {
  View, Text, StyleSheet, TouchableOpacity, Image, ScrollView,
  ActivityIndicator, Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ChevronRight, Shuffle } from 'lucide-react-native';
import { StatusBadge, Icon } from '../components';
import { useHomeData } from '../hooks/useHomeData';
import { ActiveSession } from '../services/apiSession';
import { fetchMyWeakAreas } from '../services/apiMistakes';
import { getMyAvatars } from '../services/apiUser';
import { apiService } from '../services/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const formatRelativeTime = (iso?: string) => {
  if (!iso) return '방금 전';
  const diffMs = Date.now() - new Date(iso).getTime();
  const diffMin = Math.max(0, Math.floor(diffMs / 60000));
  if (diffMin < 1) return '방금 전';
  if (diffMin < 60) return `${diffMin}분 전`;
  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return `${diffHour}시간 전`;
  return `${Math.floor(diffHour / 24)}일 전`;
};

const MISTAKE_TYPE_LABELS: Record<string, string> = {
  speech_level: '말투',   grammar: '문법',      spelling: '맞춤법',
  vocabulary:   '어휘',   honorific: '높임말',   naturalness: '자연스러움',
  expression:   '표현',   politeness: '존댓말',  other: '기타',
};
const getMistakeLabel = (type?: string) =>
  type ? (MISTAKE_TYPE_LABELS[type] ?? type) : null;

// ─── Donut chart ──────────────────────────────────────────────────────────────

const DONUT_SIZE         = 120;
const DONUT_RADIUS       = 42;
const DONUT_STROKE       = 16;
const DONUT_CIRCUMFERENCE = 2 * Math.PI * DONUT_RADIUS;
const WEAK_PALETTE       = ['#F97066', '#FB923C', '#FBBF24', '#818CF8', '#34D399'];

const canonicalType = (type?: string | null): string => {
  switch ((type || '').toLowerCase()) {
    case 'speech_level': case 'honorific': case 'honorifics':
    case 'politeness':   case 'formality':
      return 'politeness';
    case 'grammar':  case 'particle': case 'particles': case 'ending':
    case 'sentence_ending': case 'verb_conjugation': case 'word_order': case 'tense':
      return 'grammar';
    case 'vocabulary': case 'word_choice': case 'expression':
      return 'expression';
    case 'spelling': case 'spacing':
      return 'spelling';
    case 'naturalness': case 'context': case 'register':
      return 'naturalness';
    default: return 'other';
  }
};

const WEAK_LABELS: Record<string, string> = {
  politeness: '존댓말/공손성', grammar: '문법 구조', expression: '표현/어휘',
  spelling: '표기', naturalness: '자연스러움', other: '기타',
};

// ─── Progress Card ─────────────────────────────────────────────────────────────

const ProgressCard = ({ item, onPress, index }: {
  item: ActiveSession; onPress: () => void; index: number;
}) => {
  const anim      = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.spring(anim, { toValue: 1, delay: index * 70, tension: 70, friction: 10, useNativeDriver: true }).start();
  }, [anim, index]);

  return (
    <Animated.View style={{
      opacity: anim,
      transform: [
        { scale: scaleAnim },
        { translateX: anim.interpolate({ inputRange: [0, 1], outputRange: [24, 0] }) },
      ],
    }}>
      <TouchableOpacity
        onPress={onPress}
        onPressIn={() => Animated.spring(scaleAnim, { toValue: 0.97, useNativeDriver: true, tension: 200 }).start()}
        onPressOut={() => Animated.spring(scaleAnim, { toValue: 1,    useNativeDriver: true, tension: 200 }).start()}
        activeOpacity={1}
      >
        <View style={styles.progressCard}>
          <View style={styles.progressAvatarRow}>
            <View style={[styles.progressAvatarIcon, { backgroundColor: item.avatarBg || '#6C3BFF' }]}>
              <Icon name={item.avatarIcon as any} size={17} color="#FFFFFF" />
            </View>
            <StatusBadge status={item.difficulty} />
          </View>
          <Text style={styles.progressAvatarName} numberOfLines={1}>{item.avatarName}</Text>
          <Text style={styles.progressSituation} numberOfLines={2}>{item.situation}</Text>
          <View style={{ flex: 1 }} />
          <Text style={styles.progressTime}>{formatRelativeTime(item.lastMessageAt)}</Text>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
};

// ─── Screen ────────────────────────────────────────────────────────────────────

const CARD_STEP = 164 + 12;

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const { profile, stats, activeSessions, loading } = useHomeData();
  const [customAvatarUrl, setCustomAvatarUrl] = useState<string | null>(null);
  const [rawWeakAreas, setRawWeakAreas]       = useState<any[]>([]);
  const [randomLoading, setRandomLoading]     = useState(false);

  const carouselRef   = useRef<ScrollView>(null);
  const carouselIndex = useRef(0);
  const userScrolling = useRef(false);

  useFocusEffect(
    useCallback(() => {
      AsyncStorage.getItem('custom_avatar_url')
        .then(saved => setCustomAvatarUrl(saved))
        .catch(() => {});
      fetchMyWeakAreas().then(setRawWeakAreas).catch(() => {});
    }, [])
  );

  const headerAnim = useRef(new Animated.Value(0)).current;
  const ctaAnim    = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.stagger(100, [
      Animated.spring(headerAnim, { toValue: 1, tension: 60, friction: 10, useNativeDriver: true }),
      Animated.spring(ctaAnim,    { toValue: 1, tension: 60, friction: 10, useNativeDriver: true }),
    ]).start();
  }, [ctaAnim, headerAnim]);

  useEffect(() => {
    if (activeSessions.length <= 1) return;
    const id = setInterval(() => {
      if (userScrolling.current) return;
      carouselIndex.current = (carouselIndex.current + 1) % activeSessions.length;
      carouselRef.current?.scrollTo({ x: carouselIndex.current * CARD_STEP, animated: true });
    }, 2800);
    return () => clearInterval(id);
  }, [activeSessions.length]);

  const weakChartData = useMemo(() => {
    const merged = new Map<string, { count: number; weightedScore: number }>();
    rawWeakAreas.forEach(area => {
      const key   = canonicalType(area.error_type);
      const score = area.weighted_score ?? (area.count || 0);
      const cur   = merged.get(key) ?? { count: 0, weightedScore: 0 };
      merged.set(key, { count: cur.count + (area.count || 0), weightedScore: cur.weightedScore + score });
    });
    const items = Array.from(merged.entries())
      .sort((a, b) => b[1].weightedScore - a[1].weightedScore)
      .slice(0, 5);
    const total = Math.max(1, items.reduce((s, [, v]) => s + v.weightedScore, 0));
    return items.map(([key, v], i) => ({
      key,
      label: WEAK_LABELS[key] ?? key,
      count: v.count,
      ratio: v.weightedScore / total,
      color: WEAK_PALETTE[i % WEAK_PALETTE.length],
    }));
  }, [rawWeakAreas]);

  const handleRandomPractice = async () => {
    if (randomLoading) return;
    setRandomLoading(true);
    try {
      const [avatars, situations] = await Promise.all([
        getMyAvatars(),
        apiService.getSituations().catch(() => []),
      ]);
      if (!avatars.length) return;
      const avatar    = avatars[Math.floor(Math.random() * avatars.length)];
      const situation = situations.length
        ? situations[Math.floor(Math.random() * situations.length)]
        : { id: 'random', name_ko: '일상 대화', name_en: 'Everyday', description_ko: '자유롭게 대화해보세요' };
      navigation.navigate('Chat', { avatar, situation });
    } catch {
      // silent
    } finally {
      setRandomLoading(false);
    }
  };

  const handleContinueConversation = (item: ActiveSession) => {
    navigation.navigate('Chat', {
      avatar:    { id: item.avatarId, name_ko: item.avatarName, icon: item.avatarIcon, avatarBg: item.avatarBg, difficulty: item.difficulty },
      situation: { name_ko: item.situation },
      sessionId: item.sessionId,
    });
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safe} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#6366F1" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>

        {/* ── Header ── */}
        <Animated.View style={[styles.header, {
          opacity: headerAnim,
          transform: [{ translateY: headerAnim.interpolate({ inputRange: [0, 1], outputRange: [-12, 0] }) }],
        }]}>
          <TouchableOpacity style={styles.profileRow} onPress={() => navigation.navigate('My Profile')} activeOpacity={0.8}>
            <Image
              source={{ uri: customAvatarUrl ?? profile?.avatarUrl ?? 'https://i.pravatar.cc/100?img=47' }}
              style={styles.avatar}
            />
            <Text style={styles.greeting}>
              안녕하세요, <Text style={styles.greetingName}>{profile?.username ?? 'Guest'}</Text>
            </Text>
          </TouchableOpacity>
        </Animated.View>

        {/* ── CTA Card ── */}
        <Animated.View style={{
          opacity: ctaAnim,
          transform: [{ translateY: ctaAnim.interpolate({ inputRange: [0, 1], outputRange: [16, 0] }) }],
        }}>
          <View style={styles.ctaCard}>
            <Text style={styles.ctaEyebrow}>오늘의 학습</Text>
            <Text style={styles.ctaTitle}>
              {profile?.username ? `${profile.username}님, ` : ''}오늘도 꾸준히 연습해봐요
            </Text>
            <View style={styles.ctaStatsRow}>
              <View style={styles.ctaStat}>
                <Text style={styles.ctaStatNum}>{stats?.completedSessions ?? 0}</Text>
                <Text style={styles.ctaStatLabel}>완료 대화</Text>
              </View>
              <View style={styles.ctaStatDivider} />
              <View style={styles.ctaStat}>
                <Text style={styles.ctaStatNum}>{stats?.practiceMinutes ?? 0}</Text>
                <Text style={styles.ctaStatLabel}>연습 시간(분)</Text>
              </View>
              <View style={styles.ctaStatDivider} />
              <View style={styles.ctaStat}>
                <Text style={[styles.ctaStatNum, { fontSize: getMistakeLabel(stats?.topMistakeType) ? 17 : 22 }]}>
                  {getMistakeLabel(stats?.topMistakeType) ?? '—'}
                </Text>
                <Text style={styles.ctaStatLabel}>자주 틀리는 것</Text>
              </View>
            </View>
            <TouchableOpacity
              style={styles.ctaBtn}
              onPress={handleRandomPractice}
              activeOpacity={0.85}
              disabled={randomLoading}
            >
              {randomLoading
                ? <ActivityIndicator size="small" color="rgba(255,255,255,0.8)" />
                : <Shuffle size={14} color="rgba(255,255,255,0.8)" />
              }
              <Text style={styles.ctaBtnText}>랜덤 연습 시작</Text>
            </TouchableOpacity>
          </View>
        </Animated.View>

        {/* ── In Progress ── */}
        <View style={styles.sectionHeader}>
          <View style={styles.sectionTitleRow}>
            <Text style={styles.sectionTitle}>진행 중</Text>
            {activeSessions.length > 0 && (
              <View style={styles.countBadge}>
                <Text style={styles.countText}>{activeSessions.length}</Text>
              </View>
            )}
          </View>
          <TouchableOpacity style={styles.sectionLink} onPress={() => navigation.navigate('ConversationHistory')} activeOpacity={0.7}>
            <Text style={styles.sectionLinkText}>기록 보기</Text>
            <ChevronRight size={13} color="#6366F1" />
          </TouchableOpacity>
        </View>

        <ScrollView
          ref={carouselRef}
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.horizontalScroll}
          contentContainerStyle={styles.horizontalContent}
          onScrollBeginDrag={() => { userScrolling.current = true; }}
          onMomentumScrollEnd={e => {
            userScrolling.current = false;
            carouselIndex.current = Math.round(e.nativeEvent.contentOffset.x / CARD_STEP);
          }}
          onScrollEndDrag={e => {
            userScrolling.current = false;
            carouselIndex.current = Math.round(e.nativeEvent.contentOffset.x / CARD_STEP);
          }}
        >
          {activeSessions.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateTitle}>진행 중인 대화가 없어요</Text>
              <Text style={styles.emptyStateText}>아바타 탭에서 새 대화를 시작해보세요</Text>
            </View>
          ) : (
            activeSessions.map((item, index) => (
              <ProgressCard
                key={item.sessionId}
                item={item}
                index={index}
                onPress={() => handleContinueConversation(item)}
              />
            ))
          )}
        </ScrollView>

        {/* ── 학습 통계 ── */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>학습 통계</Text>
          <TouchableOpacity style={styles.sectionLink} onPress={() => navigation.navigate('Analytics', { source: 'home' })} activeOpacity={0.7}>
            <Text style={styles.sectionLinkText}>자세히 보기</Text>
            <ChevronRight size={13} color="#6366F1" />
          </TouchableOpacity>
        </View>

        {weakChartData.length > 0 ? (
          <View style={styles.weakCard}>
            {/* Donut */}
            <View style={styles.weakDonutWrap}>
              <Svg width={DONUT_SIZE} height={DONUT_SIZE} viewBox={`0 0 ${DONUT_SIZE} ${DONUT_SIZE}`}>
                <G rotation="-90" origin={`${DONUT_SIZE / 2}, ${DONUT_SIZE / 2}`}>
                  <Circle cx={DONUT_SIZE / 2} cy={DONUT_SIZE / 2} r={DONUT_RADIUS}
                    stroke="#F0F0F5" strokeWidth={DONUT_STROKE} fill="none" />
                  {weakChartData.reduce((acc, item) => {
                    const len = item.ratio * DONUT_CIRCUMFERENCE;
                    acc.nodes.push(
                      <Circle
                        key={item.key}
                        cx={DONUT_SIZE / 2} cy={DONUT_SIZE / 2} r={DONUT_RADIUS}
                        stroke={item.color} strokeWidth={DONUT_STROKE} fill="none"
                        strokeLinecap="butt"
                        strokeDasharray={`${len} ${DONUT_CIRCUMFERENCE - len}`}
                        strokeDashoffset={-acc.offset}
                      />
                    );
                    acc.offset += len;
                    return acc;
                  }, { offset: 0, nodes: [] as React.ReactNode[] }).nodes}
                </G>
              </Svg>
              <View style={styles.weakDonutCenter}>
                <Text style={styles.weakDonutValue}>{weakChartData[0]?.count ?? 0}</Text>
                <Text style={styles.weakDonutLabel}>최다 실수</Text>
              </View>
            </View>

            {/* Legend */}
            <View style={styles.weakLegend}>
              {weakChartData.map(item => (
                <View key={item.key} style={styles.weakLegendRow}>
                  <View style={[styles.weakLegendDot, { backgroundColor: item.color }]} />
                  <Text style={styles.weakLegendLabel}>{item.label}</Text>
                  <Text style={styles.weakLegendCount}>{item.count}회</Text>
                </View>
              ))}
            </View>
          </View>
        ) : (
          <View style={styles.weakEmpty}>
            <Text style={styles.weakEmptyText}>대화 후 여기에 실수 분석이 표시됩니다</Text>
          </View>
        )}

      </ScrollView>
    </SafeAreaView>
  );
};

// ─── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe:      { flex: 1, backgroundColor: '#FFFFFF' },
  container: { paddingHorizontal: 20, paddingTop: 24, paddingBottom: 40 },

  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },

  // Header
  header:       { flexDirection: 'row', alignItems: 'center', marginBottom: 22 },
  profileRow:   { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatar:       { width: 46, height: 46, borderRadius: 23, backgroundColor: '#E5E7EB' },
  greeting:     { fontSize: 18, fontWeight: '700', color: '#111827', letterSpacing: -0.3 },
  greetingName: { fontWeight: '700', color: '#6C3BFF' },

  // CTA Card
  ctaCard: {
    backgroundColor: '#1A1035', borderRadius: 20, padding: 22,
    marginBottom: 28, overflow: 'hidden', borderWidth: 1, borderColor: '#2D1F52',
  },
  ctaEyebrow:     { fontSize: 11, color: 'rgba(255,255,255,0.5)', fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 6 },
  ctaTitle:       { color: '#FFFFFF', fontSize: 16, fontWeight: '600', lineHeight: 23, letterSpacing: -0.2, marginBottom: 20 },
  ctaStatsRow:    { flexDirection: 'row', alignItems: 'center', marginBottom: 20 },
  ctaStat:        { flex: 1, alignItems: 'center', gap: 3 },
  ctaStatNum:     { fontSize: 22, fontWeight: '700', color: '#FFFFFF', letterSpacing: -0.5 },
  ctaStatLabel:   { fontSize: 11, color: 'rgba(255,255,255,0.5)', fontWeight: '500' },
  ctaStatDivider: { width: 1, height: 32, backgroundColor: 'rgba(255,255,255,0.12)' },
  ctaBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
    backgroundColor: 'rgba(255,255,255,0.10)', borderRadius: 11, paddingVertical: 11,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.15)',
  },
  ctaBtnText: { fontSize: 13, fontWeight: '600', color: '#FFFFFF' },

  // Section headers
  sectionHeader:   { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 },
  sectionTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sectionTitle:    { fontSize: 16, fontWeight: '700', color: '#111827', letterSpacing: -0.3 },
  countBadge:      { backgroundColor: '#EEF2FF', borderRadius: 8, paddingHorizontal: 8, paddingVertical: 2 },
  countText:       { color: '#6366F1', fontWeight: '700', fontSize: 12 },
  sectionLink:     { flexDirection: 'row', alignItems: 'center', gap: 2 },
  sectionLinkText: { fontSize: 12, fontWeight: '600', color: '#6366F1' },

  // Scroll
  horizontalScroll:  { marginBottom: 28 },
  horizontalContent: { gap: 12, paddingRight: 4 },

  // Empty state (진행 중)
  emptyState:      { paddingVertical: 24, paddingHorizontal: 4 },
  emptyStateTitle: { fontSize: 14, fontWeight: '600', color: '#374151', marginBottom: 4 },
  emptyStateText:  { fontSize: 12, color: '#6B7280' },

  // Progress Card
  progressCard: {
    width: 164, borderRadius: 16, backgroundColor: '#FFFFFF',
    padding: 14, minHeight: 150, borderWidth: 1, borderColor: '#E8E8F0',
  },
  progressAvatarRow:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  progressAvatarIcon: { width: 34, height: 34, borderRadius: 11, alignItems: 'center', justifyContent: 'center' },
  progressAvatarName: { fontSize: 14, fontWeight: '700', color: '#111827', letterSpacing: -0.2, marginBottom: 4 },
  progressSituation:  { fontSize: 13, color: '#374151', lineHeight: 18 },
  progressTime:       { fontSize: 11, color: '#9CA3AF', fontWeight: '500', marginTop: 10 },

  // 학습 통계 — donut chart card
  weakCard: {
    flexDirection: 'row', alignItems: 'center', gap: 20,
    borderWidth: 1, borderColor: '#E8E8F0', borderRadius: 16,
    padding: 16,
  },
  weakDonutWrap: {
    width: DONUT_SIZE, height: DONUT_SIZE,
    alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  },
  weakDonutCenter: {
    position: 'absolute', alignItems: 'center', justifyContent: 'center',
  },
  weakDonutValue: { fontSize: 20, fontWeight: '800', color: '#111827', lineHeight: 24 },
  weakDonutLabel: { fontSize: 10, fontWeight: '600', color: '#6B7280', marginTop: 2 },
  weakLegend:     { flex: 1, gap: 8 },
  weakLegendRow:  { flexDirection: 'row', alignItems: 'center', gap: 8 },
  weakLegendDot:  { width: 9, height: 9, borderRadius: 5, flexShrink: 0 },
  weakLegendLabel: { flex: 1, fontSize: 12, fontWeight: '600', color: '#374151' },
  weakLegendCount: { fontSize: 12, color: '#9CA3AF', fontWeight: '500' },
  weakEmpty:      { paddingVertical: 24, alignItems: 'center' },
  weakEmptyText:  { fontSize: 13, color: '#9CA3AF' },
});

export default HomeScreen;
