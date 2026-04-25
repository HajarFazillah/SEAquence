import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, useFocusEffect } from '@react-navigation/native';
import {
  ChevronRight, Heart, MessageCircle,
  Edit, Trash2, Clock, TrendingUp, Sparkles, User as UserIcon,
} from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Header, Card, Button, Tag, StatusBadge, Icon } from '../components';
import { SPEECH_LEVELS } from '../constants';
import { deleteAvatar } from '../services/apiUser';
import { getAvatarSessions, ActiveSession } from '../services/apiSession';

const FAVORITES_KEY = 'favorite_avatars';

// ─── Helpers ─────────────────────────────────────────────────────────────────

// Format startedAt date string into a readable relative date
// e.g. "2026-04-17T10:30:00" → "오늘", "2일 전", "1주 전"
const formatRelativeDate = (dateStr: string | null): string => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return '오늘';
  if (diffDays === 1) return '1일 전';
  if (diffDays < 7) return `${diffDays}일 전`;
  if (diffDays < 14) return '1주 전';
  return `${Math.floor(diffDays / 7)}주 전`;
};

// Calculate duration between startedAt and endedAt in mm:ss format
// If session not ended, show '-'
const formatDuration = (startStr: string | null, endStr: string | null): string => {
  if (!startStr || !endStr) return '-';
  const start = new Date(startStr);
  const end = new Date(endStr);
  const diffSec = Math.floor((end.getTime() - start.getTime()) / 1000);
  if (diffSec < 0) return '-';
  const mins = Math.floor(diffSec / 60);
  const secs = diffSec % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

// ─── Component ───────────────────────────────────────────────────────────────

export default function AvatarDetailScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { avatar } = route.params || {};

  const [isFavorite, setIsFavorite] = useState(false);
  const [sessions, setSessions] = useState<ActiveSession[]>([]);

  // Load real sessions and favorite state every time screen comes into focus
  useFocusEffect(
    useCallback(() => {
      if (!avatar?.id) return;

      // Load sessions
      getAvatarSessions(String(avatar.id))
        .then(data => setSessions(data))
        .catch(err => console.log('Failed to load avatar sessions:', err));

      // Load favorite state from AsyncStorage
      AsyncStorage.getItem(FAVORITES_KEY).then(stored => {
        const favorites: string[] = stored ? JSON.parse(stored) : [];
        setIsFavorite(favorites.includes(String(avatar.id)));
      }).catch(err => console.log('Failed to load favorites:', err));

    }, [avatar?.id])
  );

  // Toggle favorite and save to AsyncStorage
  const handleToggleFavorite = async () => {
    try {
      const stored = await AsyncStorage.getItem(FAVORITES_KEY);
      const favorites: string[] = stored ? JSON.parse(stored) : [];
      const avatarId = String(avatar.id);
      let updated: string[];
      if (favorites.includes(avatarId)) {
        updated = favorites.filter(id => id !== avatarId);
        setIsFavorite(false);
      } else {
        updated = [...favorites, avatarId];
        setIsFavorite(true);
      }
      await AsyncStorage.setItem(FAVORITES_KEY, JSON.stringify(updated));
    } catch (err) {
      console.log('Failed to save favorite:', err);
    }
  };

  // Calculate real stats from sessions
  const totalConversations = sessions.length;
  const totalMinutes = sessions.reduce((acc, s) => {
    if (!s.lastMessageAt || !s.endedAt) return acc;
    const start = new Date(s.lastMessageAt);
    const end = new Date(s.endedAt);
    const mins = Math.floor((end.getTime() - start.getTime()) / (1000 * 60));
    return acc + (mins > 0 ? mins : 0);
  }, 0);
  // No score field in backend yet — show 0
  const avgScore = 0;

  // Show only the 3 most recent sessions
  const recentSessions = sessions.slice(0, 3);

  const handleStartChat = () => {
    navigation.navigate('SituationSelection', { avatar });
  };

  const handleEdit = () => {
    navigation.navigate('CreateAvatar', { avatar, isEdit: true });
  };

  const handleDelete = () => {
    Alert.alert('아바타 삭제', '정말 삭제하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '삭제',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteAvatar(String(avatar?.id));
            navigation.navigate('Main', { screen: 'Avatar' });
          } catch {
            Alert.alert('오류', '삭제에 실패했어요. 다시 시도해주세요.');
          }
        },
      },
    ]);
  };

  type SpeechLevel = 'formal' | 'polite' | 'informal';
  const formalityToUser = (avatar?.formality_to_user || 'polite') as SpeechLevel;
  const formalityFromUser = (avatar?.formality_from_user || 'polite') as SpeechLevel;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header
        title="아바타 정보"
        rightElement={
          <TouchableOpacity onPress={handleEdit}>
            <Edit size={22} color="#6C3BFF" />
          </TouchableOpacity>
        }
      />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Avatar Header */}
        <View style={styles.avatarHeader}>
          <View style={[styles.avatarIcon, { backgroundColor: avatar?.avatar_bg || '#FFB6C1' }]}>
            <Icon name={(avatar?.icon || 'user') as any} size={48} color="#FFFFFF" />
          </View>
          <View style={styles.avatarInfo}>
            <View style={styles.nameRow}>
              <Text style={styles.avatarName}>{avatar?.name_ko || '아바타'}</Text>
              <TouchableOpacity onPress={handleToggleFavorite}>
                <Heart
                  size={24}
                  color={isFavorite ? '#E53935' : '#B0B0C5'}
                  fill={isFavorite ? '#E53935' : 'transparent'}
                />
              </TouchableOpacity>
            </View>
            <Text style={styles.avatarNameEn}>
              {avatar?.name_en || ''}{avatar?.age ? ` · ${avatar.age}세` : ''}
            </Text>
            <View style={styles.badgeRow}>
              <StatusBadge status={avatar?.difficulty || 'medium'} />
              <View style={[
                styles.typeBadge,
                avatar?.avatar_type === 'real' ? styles.typeBadgeReal : styles.typeBadgeFictional,
              ]}>
                {avatar?.avatar_type === 'real' ? (
                  <UserIcon size={12} color="#2196F3" />
                ) : (
                  <Sparkles size={12} color="#9C27B0" />
                )}
                <Text style={[
                  styles.typeBadgeText,
                  avatar?.avatar_type === 'real' ? styles.typeBadgeTextReal : styles.typeBadgeTextFictional,
                ]}>
                  {avatar?.avatar_type === 'real' ? '실제 인물' : '가상 인물'}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Description */}
        <Card variant="elevated" style={styles.descCard}>
          <Text style={styles.descText}>
            {avatar?.relationship_description || '대화 연습을 위한 아바타입니다.'}
          </Text>
        </Card>

        {/* AI Memo */}
        {avatar?.memo && (
          <Card variant="outlined" style={styles.memoCard}>
            <View style={styles.memoHeader}>
              <Text style={styles.memoLabel}>AI 참고 메모</Text>
            </View>
            <Text style={styles.memoText}>{avatar.memo}</Text>
          </Card>
        )}

        {/* Avatar Description */}
        {avatar?.description && (
          <Card variant="outlined" style={styles.memoCard}>
            <View style={styles.memoHeader}>
              <Text style={styles.memoLabel}>아바타 관련 설명</Text>
            </View>
            <Text style={styles.memoText}>{avatar.description}</Text>
          </Card>
        )}

        {/* Stats — totalConversations and totalMinutes are real, avgScore is 0 until backend adds score */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <MessageCircle size={20} color="#6C3BFF" />
            <Text style={styles.statValue}>{totalConversations}</Text>
            <Text style={styles.statLabel}>대화</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Clock size={20} color="#4CAF50" />
            <Text style={styles.statValue}>{totalMinutes}분</Text>
            <Text style={styles.statLabel}>연습 시간</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <TrendingUp size={20} color="#F4A261" />
            <Text style={styles.statValue}>{avgScore}%</Text>
            <Text style={styles.statLabel}>평균 점수</Text>
          </View>
        </View>

        {/* Speech Level Settings */}
        <Text style={styles.sectionTitle}>말투 설정</Text>
        <Card variant="elevated" style={styles.speechCard}>
          <View style={styles.speechRow}>
            <View style={styles.speechItem}>
              <Text style={styles.speechLabel}>아바타 → 나</Text>
              <View style={[styles.speechBadge, { backgroundColor: SPEECH_LEVELS[formalityToUser]?.color + '20' }]}>
                <Text style={[styles.speechBadgeText, { color: SPEECH_LEVELS[formalityToUser]?.color }]}>
                  {SPEECH_LEVELS[formalityToUser]?.name_ko}
                </Text>
              </View>
            </View>
            <View style={styles.speechItem}>
              <Text style={styles.speechLabel}>나 → 아바타</Text>
              <View style={[styles.speechBadge, { backgroundColor: SPEECH_LEVELS[formalityFromUser]?.color + '20' }]}>
                <Text style={[styles.speechBadgeText, { color: SPEECH_LEVELS[formalityFromUser]?.color }]}>
                  {SPEECH_LEVELS[formalityFromUser]?.name_ko}
                </Text>
              </View>
            </View>
          </View>
        </Card>

        {/* Interests */}
        <Text style={styles.sectionTitle}>관심사</Text>
        <Card variant="elevated" style={styles.interestsCard}>
          <View style={styles.tagGrid}>
            {(avatar?.interests ?? []).map((interest: string, i: number) => (
              <Tag key={i} label={interest} selected />
            ))}
          </View>
        </Card>

        {/* Personality */}
        {avatar?.personality_traits && avatar.personality_traits.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>성격</Text>
            <Card variant="elevated" style={styles.interestsCard}>
              <View style={styles.tagGrid}>
                {avatar.personality_traits.map((trait: string, i: number) => (
                  <Tag key={i} label={trait} variant="outline" />
                ))}
              </View>
            </Card>
          </>
        )}

        {/* Recent Conversations — real data from backend */}
        <Text style={styles.sectionTitle}>최근 대화</Text>
        {recentSessions.length === 0 ? (
          <Card variant="elevated" style={styles.emptyCard}>
            <Text style={styles.emptyText}>아직 대화 기록이 없어요. 대화를 시작해보세요!</Text>
          </Card>
        ) : (
          <View style={styles.conversationList}>
            {recentSessions.map((session) => (
              <Card key={session.sessionId} variant="elevated" style={styles.convCard}>
                <View style={styles.convRow}>
                  <View style={styles.convInfo}>
                    <Text style={styles.convSituation}>{session.situation}</Text>
                    <Text style={styles.convDate}>
                      {formatRelativeDate(session.lastMessageAt)} · {formatDuration(session.lastMessageAt, session.endedAt)}
                    </Text>
                  </View>
                  <View style={styles.convScore}>
                    <Text style={styles.convScoreText}>{session.difficulty}</Text>
                  </View>
                  <ChevronRight size={20} color="#B0B0C5" />
                </View>
              </Card>
            ))}
          </View>
        )}

        {/* Delete button */}
        <TouchableOpacity style={styles.deleteButton} onPress={handleDelete}>
          <Trash2 size={18} color="#E53935" />
          <Text style={styles.deleteButtonText}>아바타 삭제</Text>
        </TouchableOpacity>

      </ScrollView>

      {/* Start Chat Button */}
      <View style={styles.footer}>
        <Button title="대화 시작하기" onPress={handleStartChat} showArrow />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },
  avatarHeader: { alignItems: 'center', paddingVertical: 20 },
  avatarIcon: { width: 100, height: 100, borderRadius: 50, alignItems: 'center', justifyContent: 'center', marginBottom: 16 },
  avatarInfo: { alignItems: 'center' },
  nameRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 4 },
  avatarName: { fontSize: 24, fontWeight: '700', color: '#1A1A2E' },
  avatarNameEn: { fontSize: 14, color: '#6C6C80', marginBottom: 12 },
  badgeRow: { flexDirection: 'row', gap: 8 },
  typeBadge: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  typeBadgeFictional: { backgroundColor: '#F3E5F5' },
  typeBadgeReal: { backgroundColor: '#E3F2FD' },
  typeBadgeText: { fontSize: 11, fontWeight: '600' },
  typeBadgeTextFictional: { color: '#9C27B0' },
  typeBadgeTextReal: { color: '#2196F3' },
  descCard: { marginBottom: 16 },
  descText: { fontSize: 14, color: '#6C6C80', lineHeight: 22, textAlign: 'center' },
  memoCard: { marginBottom: 20, borderColor: '#E2E2EC' },
  memoHeader: { marginBottom: 8 },
  memoLabel: { fontSize: 12, fontWeight: '600', color: '#6C3BFF' },
  memoText: { fontSize: 13, color: '#6C6C80', lineHeight: 20 },
  statsRow: { flexDirection: 'row', backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, marginBottom: 24, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 4, elevation: 2 },
  statItem: { flex: 1, alignItems: 'center' },
  statDivider: { width: 1, backgroundColor: '#E2E2EC' },
  statValue: { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginTop: 6, marginBottom: 2 },
  statLabel: { fontSize: 11, color: '#6C6C80' },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 12 },
  speechCard: { marginBottom: 20 },
  speechRow: { flexDirection: 'row', gap: 16 },
  speechItem: { flex: 1, alignItems: 'center' },
  speechLabel: { fontSize: 12, color: '#6C6C80', marginBottom: 8 },
  speechBadge: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 12 },
  speechBadgeText: { fontSize: 14, fontWeight: '600' },
  interestsCard: { marginBottom: 20 },
  tagGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  emptyCard: { marginBottom: 20 },
  emptyText: { fontSize: 14, color: '#6C6C80', textAlign: 'center', paddingVertical: 8 },
  conversationList: { gap: 10, marginBottom: 20 },
  convCard: { padding: 14 },
  convRow: { flexDirection: 'row', alignItems: 'center' },
  convInfo: { flex: 1 },
  convSituation: { fontSize: 15, fontWeight: '600', color: '#1A1A2E', marginBottom: 2 },
  convDate: { fontSize: 12, color: '#6C6C80' },
  convScore: { backgroundColor: '#F0EDFF', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 10, marginRight: 8 },
  convScoreText: { fontSize: 13, fontWeight: '600', color: '#6C3BFF' },
  deleteButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14, marginBottom: 20 },
  deleteButtonText: { fontSize: 14, fontWeight: '600', color: '#E53935' },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
});