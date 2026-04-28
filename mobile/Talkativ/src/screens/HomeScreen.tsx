import React, { useEffect, useRef, useCallback, useState } from 'react';
import Svg, { Circle, Defs, LinearGradient as SvgGradient, Stop } from 'react-native-svg';
import {
  View, Text, StyleSheet, TouchableOpacity, Image, ScrollView,
  ActivityIndicator, Animated, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Bell, ChevronRight, Smile, Meh, Frown, TrendingUp } from 'lucide-react-native';
import { StatusBadge, Icon } from '../components';
import { useHomeData } from '../hooks/useHomeData';
import { ActiveSession } from '../services/apiSession';
import { buildConversationPreviewText } from '../services/conversationPreview';

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

const getMoodConfig = (mood: number) => {
  if (mood >= 70) return { icon: Smile, color: '#22C55E', label: '좋음', bg: 'rgba(34,197,94,0.08)' };
  if (mood >= 40) return { icon: Meh,   color: '#F59E0B', label: '보통', bg: 'rgba(245,158,11,0.08)' };
  return              { icon: Frown, color: '#EF4444', label: '나쁨', bg: 'rgba(239,68,68,0.08)' };
};

// ─── Animated Circular Progress ───────────────────────────────────────────────

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

const CircularProgress = ({ percentage }: { percentage: number }) => {
  const animatedValue = useRef(new Animated.Value(0)).current;
  const size = 80;
  const strokeWidth = 6;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  useEffect(() => {
    Animated.timing(animatedValue, {
      toValue: percentage, duration: 1200, delay: 400, useNativeDriver: false,
    }).start();
  }, [percentage]);

  const strokeDashoffset = animatedValue.interpolate({
    inputRange: [0, 100], outputRange: [circumference, 0],
  });

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={{ position: 'absolute' }}>
        <Circle cx={size/2} cy={size/2} r={radius}
          stroke="rgba(255,255,255,0.15)" strokeWidth={strokeWidth} fill="none" />
      </Svg>
      <Animated.View style={{ position: 'absolute', width: size, height: size }}>
        <Svg width={size} height={size}>
          <AnimatedCircle
            cx={size/2} cy={size/2} r={radius}
            stroke="#FFFFFF" strokeWidth={strokeWidth} fill="none"
            strokeDasharray={circumference} strokeDashoffset={strokeDashoffset}
            strokeLinecap="round" rotation="-90" origin={`${size/2}, ${size/2}`}
          />
        </Svg>
      </Animated.View>
      <Text style={styles.circlePercent}>{percentage}%</Text>
    </View>
  );
};

// ─── Progress Card ─────────────────────────────────────────────────────────────

const ProgressCard = ({ item, previewText, onPress, index }: {
  item: ActiveSession;
  previewText: string;
  onPress: () => void;
  index: number;
}) => {
  const anim      = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const moodWidth = useRef(new Animated.Value(0)).current;
  const moodConfig = getMoodConfig(item.mood);
  const MoodIcon   = moodConfig.icon;

  useEffect(() => {
    Animated.spring(anim, { toValue: 1, delay: index * 70, tension: 70, friction: 10, useNativeDriver: true }).start();
    Animated.timing(moodWidth, { toValue: item.mood, duration: 900, delay: 300 + index * 70, useNativeDriver: false }).start();
  }, []);

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
            <View style={[styles.progressAvatarIcon, { backgroundColor: item.avatarBg }]}>
              <Icon name={item.avatarIcon as any} size={18} color="#FFFFFF" />
            </View>
            <StatusBadge status={item.difficulty} />
          </View>

          <Text style={styles.progressAvatarName} numberOfLines={1}>{item.avatarName}</Text>

          <View style={styles.progressMetaRow}>
            <Text style={styles.progressSituation} numberOfLines={1}>{item.situation}</Text>
            <Text style={styles.progressTime}>{formatRelativeTime(item.lastMessageAt)}</Text>
          </View>

          {previewText ? (
            <Text style={styles.progressPreview} numberOfLines={2}>{previewText}</Text>
          ) : null}

          <View style={[styles.moodChip, { backgroundColor: moodConfig.bg }]}>
            <MoodIcon size={12} color={moodConfig.color} />
            <Text style={[styles.moodText, { color: moodConfig.color }]}>{moodConfig.label}</Text>
          </View>

          <View style={styles.moodBarTrack}>
            <Animated.View style={[
              styles.moodBarFill,
              {
                width: moodWidth.interpolate({ inputRange: [0, 100], outputRange: ['0%', '100%'] }),
                backgroundColor: moodConfig.color,
              },
            ]} />
          </View>
        </View>
      </TouchableOpacity>
    </Animated.View>
  );
};

// ─── Stat Card ─────────────────────────────────────────────────────────────────

const StatCard = ({ stat, index }: {
  stat: { id: string; title: string; count: number; unit?: string; icon: any; color: string };
  index: number;
}) => {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.spring(anim, { toValue: 1, delay: 500 + index * 80, tension: 60, friction: 8, useNativeDriver: true }).start();
  }, []);

  return (
    <Animated.View style={[styles.statCardWrapper, {
      opacity: anim,
      transform: [{ translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [16, 0] }) }],
    }]}>
      <View style={styles.statCard}>
        <View style={[styles.statIconBg, { backgroundColor: `${stat.color}14` }]}>
          <Icon name={stat.icon} size={20} color={stat.color} />
        </View>
        <Text style={styles.statCount}>{stat.count}{stat.unit || ''}</Text>
        <Text style={styles.statLabel}>{stat.title}</Text>
      </View>
    </Animated.View>
  );
};

// ─── Screen ────────────────────────────────────────────────────────────────────

export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const { profile, stats, activeSessions, conversationPreviews, loading } = useHomeData();
  const [customAvatarUrl, setCustomAvatarUrl] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      AsyncStorage.getItem('custom_avatar_url')
        .then(saved => setCustomAvatarUrl(saved))
        .catch(() => {});
    }, [])
  );

  const headerAnim = useRef(new Animated.Value(0)).current;
  const ctaAnim    = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.stagger(100, [
      Animated.spring(headerAnim, { toValue: 1, tension: 60, friction: 10, useNativeDriver: true }),
      Animated.spring(ctaAnim,    { toValue: 1, tension: 60, friction: 10, useNativeDriver: true }),
    ]).start();
  }, []);

  const liveStats = [
    { id: '1', title: '완료한 대화', count: stats?.completedSessions  ?? 0,            icon: 'message' as const, color: '#6366F1' },
    { id: '2', title: '배운 표현',   count: stats?.learnedExpressions ?? 0,            icon: 'book'    as const, color: '#EC4899' },
    { id: '3', title: '연습 시간',   count: stats?.practiceMinutes    ?? 0, unit: '분', icon: 'clock'   as const, color: '#10B981' },
  ];

  const handleContinueConversation = (item: ActiveSession) => {
    navigation.navigate('Chat', {
      avatar: { id: item.avatarId, name_ko: item.avatarName, icon: item.avatarIcon, avatarBg: item.avatarBg, difficulty: item.difficulty },
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
            <View>
              <Text style={styles.hello}>안녕하세요</Text>
              <Text style={styles.username}>{profile?.username ?? 'Guest'}</Text>
            </View>
          </TouchableOpacity>
          <TouchableOpacity style={styles.notifBtn} activeOpacity={0.8}>
            <Bell size={19} color="#374151" />
          </TouchableOpacity>
        </Animated.View>

        {/* ── CTA Card ── */}
        <Animated.View style={{
          opacity: ctaAnim,
          transform: [{ translateY: ctaAnim.interpolate({ inputRange: [0, 1], outputRange: [16, 0] }) }],
        }}>
          <View style={styles.ctaCard}>
            <View style={styles.ctaBlob} />
            <View style={styles.ctaTop}>
              <View style={{ flex: 1 }}>
                <Text style={styles.ctaEyebrow}>오늘의 목표</Text>
                <Text style={styles.ctaTitle}>한국어 실력을{'\n'}매일 향상시켜보세요!</Text>
              </View>
              <CircularProgress percentage={stats?.progressPercent ?? 0} />
            </View>
            <TouchableOpacity
              style={styles.ctaBtn}
              onPress={() => navigation.navigate('Analytics', { source: 'home' })}
              activeOpacity={0.85}
            >
              <TrendingUp size={14} color="#1C1028" />
              <Text style={styles.ctaBtnText}>실수 분석 보기</Text>
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

        <ScrollView horizontal showsHorizontalScrollIndicator={false}
          style={styles.horizontalScroll} contentContainerStyle={styles.horizontalContent}>
          {activeSessions.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>진행 중인 대화가 없습니다</Text>
            </View>
          ) : (
            activeSessions.map((item, index) => (
              <ProgressCard
                key={item.sessionId}
                item={item}
                index={index}
                previewText={buildConversationPreviewText(conversationPreviews[item.avatarId])}
                onPress={() => handleContinueConversation(item)}
              />
            ))
          )}
        </ScrollView>

        {/* ── Stats ── */}
        <Text style={[styles.sectionTitle, { marginBottom: 14 }]}>학습 통계</Text>
        <View style={styles.statsRow}>
          {liveStats.map((stat, index) => (
            <StatCard key={stat.id} stat={stat} index={index} />
          ))}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
};

// ─── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  safe:      { flex: 1, backgroundColor: '#F8F8F8' },
  container: { paddingHorizontal: 20, paddingTop: 14, paddingBottom: 40 },

  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },

  // Header
  header:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  profileRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatar:     { width: 46, height: 46, borderRadius: 23, backgroundColor: '#E5E7EB' },
  hello:      { fontSize: 12, color: '#9CA3AF', marginBottom: 2 },
  username:   { fontSize: 17, fontWeight: '700', color: '#111827', letterSpacing: -0.3 },
  notifBtn:   {
    width: 40, height: 40, borderRadius: 12,
    backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center',
    ...Platform.select({
      ios:     { shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.07, shadowRadius: 4 },
      android: { elevation: 2 },
    }),
  },

  // CTA Card — dark charcoal, one accent blob, one clean white button
  ctaCard: {
    backgroundColor: '#1C1028', borderRadius: 20, padding: 22, marginBottom: 28, overflow: 'hidden',
    ...Platform.select({
      ios:     { shadowColor: '#1C1028', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.2, shadowRadius: 14 },
      android: { elevation: 8 },
    }),
  },
  ctaBlob:    { position: 'absolute', width: 180, height: 180, borderRadius: 90, backgroundColor: 'rgba(99,102,241,0.15)', top: -60, right: -40 },
  ctaTop:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  ctaEyebrow: { fontSize: 10, color: 'rgba(255,255,255,0.4)', fontWeight: '600', letterSpacing: 0.8, textTransform: 'uppercase', marginBottom: 8 },
  ctaTitle:   { color: '#FFFFFF', fontSize: 17, fontWeight: '700', lineHeight: 25, letterSpacing: -0.2 },
  ctaBtn:     {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6,
    backgroundColor: '#FFFFFF', borderRadius: 11, paddingVertical: 11,
  },
  ctaBtnText: { fontSize: 13, fontWeight: '700', color: '#1C1028' },
  circlePercent: { color: '#FFFFFF', fontWeight: '700', fontSize: 15 },

  // Section headers
  sectionHeader:   { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 },
  sectionTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sectionTitle:    { fontSize: 15, fontWeight: '700', color: '#111827', letterSpacing: -0.2 },
  countBadge:      { backgroundColor: '#EEF2FF', borderRadius: 7, paddingHorizontal: 7, paddingVertical: 2 },
  countText:       { color: '#6366F1', fontWeight: '700', fontSize: 11 },
  sectionLink:     { flexDirection: 'row', alignItems: 'center', gap: 2 },
  sectionLinkText: { fontSize: 12, fontWeight: '600', color: '#6366F1' },

  // Scroll
  horizontalScroll:  { marginBottom: 28 },
  horizontalContent: { gap: 10, paddingRight: 4 },

  // Empty
  emptyState:     { paddingVertical: 20 },
  emptyStateText: { color: '#9CA3AF', fontSize: 13 },

  // Progress Card
  progressCard: {
    width: 176, borderRadius: 16, padding: 14, backgroundColor: '#FFFFFF',
    ...Platform.select({
      ios:     { shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.06, shadowRadius: 6 },
      android: { elevation: 2 },
    }),
  },
  progressAvatarRow:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  progressAvatarIcon: { width: 34, height: 34, borderRadius: 11, alignItems: 'center', justifyContent: 'center' },
  progressAvatarName: { fontSize: 14, fontWeight: '700', color: '#111827', marginBottom: 3, letterSpacing: -0.2 },
  progressMetaRow:    { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  progressSituation:  { flex: 1, fontSize: 11, color: '#9CA3AF' },
  progressTime:       { fontSize: 10, color: '#D1D5DB', fontWeight: '500' },
  progressPreview:    { fontSize: 11, lineHeight: 16, color: '#6B7280', marginBottom: 10 },
  moodChip:           { flexDirection: 'row', alignItems: 'center', gap: 4, alignSelf: 'flex-start', paddingHorizontal: 7, paddingVertical: 3, borderRadius: 7, marginBottom: 8 },
  moodText:           { fontSize: 10, fontWeight: '600' },
  moodBarTrack:       { height: 3, backgroundColor: '#F3F4F6', borderRadius: 2, overflow: 'hidden' },
  moodBarFill:        { height: '100%', borderRadius: 2 },

  // Stats
  statsRow:        { flexDirection: 'row', gap: 10 },
  statCardWrapper: { flex: 1 },
  statCard:        {
    backgroundColor: '#FFFFFF', borderRadius: 14, padding: 14, alignItems: 'center', gap: 5,
    ...Platform.select({
      ios:     { shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 5 },
      android: { elevation: 2 },
    }),
  },
  statIconBg: { width: 38, height: 38, borderRadius: 11, alignItems: 'center', justifyContent: 'center' },
  statCount:  { fontSize: 19, fontWeight: '800', color: '#111827', letterSpacing: -0.4 },
  statLabel:  { fontSize: 10, color: '#9CA3AF', fontWeight: '500', textAlign: 'center' },
});

export default HomeScreen;