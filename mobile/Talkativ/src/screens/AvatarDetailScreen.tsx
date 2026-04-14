import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert,} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  ChevronRight, Heart, MessageCircle,
  Edit, Trash2, Clock, TrendingUp, Sparkles, User as UserIcon,
} from 'lucide-react-native';
import { Header, Card, Button, Tag, StatusBadge, Icon } from '../components';
import { SPEECH_LEVELS } from '../constants';
import { deleteAvatar } from '../services/apiUser';

export default function AvatarDetailScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const { avatar } = route.params || {};

  const [isFavorite, setIsFavorite] = useState(false);

  // Kept as mock until Session API is wired
  const stats = {
    totalConversations: 8,
    totalMinutes: 45,
    avgScore: 82,
  };

  const recentConversations = [
    { id: '1', situation: '카페에서 수다', date: '2일 전', score: 85, duration: '05:30' },
    { id: '2', situation: '캠퍼스 만남', date: '5일 전', score: 78, duration: '03:20' },
    { id: '3', situation: '처음 만남', date: '1주 전', score: 82, duration: '04:15' },
  ];

  const handleStartChat = () => {
    navigation.navigate('SituationSelection', { avatar });
  };

  const handleEdit = () => {
    navigation.navigate('CreateAvatar', { avatar, isEdit: true });
  };

  // ── UPDATED handleDelete ──────────────────────────────────────────────────
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
            // useFocusEffect in AvatarScreen auto-refreshes ✅
          } catch {
            Alert.alert('오류', '삭제에 실패했어요. 다시 시도해주세요.');
          }
        },
      },
    ]);
  };
  // ─────────────────────────────────────────────────────────────────────────

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
              <TouchableOpacity onPress={() => setIsFavorite(!isFavorite)}>
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

        {/* Stats — mock until Session API is wired */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <MessageCircle size={20} color="#6C3BFF" />
            <Text style={styles.statValue}>{stats.totalConversations}</Text>
            <Text style={styles.statLabel}>대화</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Clock size={20} color="#4CAF50" />
            <Text style={styles.statValue}>{stats.totalMinutes}분</Text>
            <Text style={styles.statLabel}>연습 시간</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <TrendingUp size={20} color="#F4A261" />
            <Text style={styles.statValue}>{stats.avgScore}%</Text>
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

        {/* Recent Conversations — mock until Session API is wired */}
        <Text style={styles.sectionTitle}>최근 대화</Text>
        <View style={styles.conversationList}>
          {recentConversations.map((conv) => (
            <Card key={conv.id} variant="elevated" style={styles.convCard}>
              <View style={styles.convRow}>
                <View style={styles.convInfo}>
                  <Text style={styles.convSituation}>{conv.situation}</Text>
                  <Text style={styles.convDate}>{conv.date} · {conv.duration}</Text>
                </View>
                <View style={styles.convScore}>
                  <Text style={styles.convScoreText}>{conv.score}점</Text>
                </View>
                <ChevronRight size={20} color="#B0B0C5" />
              </View>
            </Card>
          ))}
        </View>

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