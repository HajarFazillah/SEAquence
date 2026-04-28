import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  Heart, MessageCircle, Edit, Trash2,
  Clock, TrendingUp, ChevronLeft,
} from 'lucide-react-native';
import { Tag, Icon } from '../components';
import { SPEECH_LEVELS } from '../constants';
import { deleteAvatar } from '../services/apiUser';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const stripMarkdown = (text: string): string =>
  text
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^[\-\*]\s/gm, '• ')
    .replace(/_{1,2}(.*?)_{1,2}/g, '$1')
    .replace(/~~(.*?)~~/g, '$1')
    .trim();

const buildMockBio = (avatar: any): string => {
  const name      = avatar?.name_ko || '아바타';
  const traits    = (avatar?.personality_traits || ['친절한']).slice(0, 2).join(', ');
  const interests = (avatar?.interests || ['다양한 주제']).slice(0, 3).join(', ');
  const toLabel   = avatar?.formality_to_user   === 'formal'   ? '합쇼체'
                  : avatar?.formality_to_user   === 'informal' ? '반말' : '해요체';
  const fromLabel = avatar?.formality_from_user === 'formal'   ? '합쇼체'
                  : avatar?.formality_from_user === 'informal' ? '반말' : '해요체';
  const style     = avatar?.speaking_style || '자연스럽게 대화해도 좋습니다';
  const dislikes  = (avatar?.dislikes || []).length > 0 ? avatar.dislikes.join(', ') : '특별히 없음';
  return (
    `${name}는 성격이 ${traits} 편이며, ${interests}에 관심이 많습니다.\n\n` +
    `대화 팁:\n• ${name}는 ${toLabel}로 말합니다\n• 당신은 ${fromLabel}로 대화하세요\n• ${style}\n\n` +
    `피해야 할 주제: ${dislikes}`
  );
};

const getAgeDesc = (age?: number): string => {
  if (!age) return '';
  if (age < 20) return '많이 어려요';
  if (age < 25) return '또래예요';
  if (age < 30) return '나보다 연상이에요';
  if (age < 40) return '경험이 풍부해요';
  return '인생 선배예요';
};

const getGenderDesc = (gender?: string): string => {
  if (gender === 'female') return '언니라고 불러도 될 것 같아요';
  if (gender === 'male')   return '오빠라고 불러도 될 것 같아요';
  return '성별을 가리지 않아요';
};

const getDifficultyDesc = (diff?: string): string => {
  if (diff === 'easy') return '편하게 연습하기 좋아요';
  if (diff === 'hard') return '많이 도전적이에요';
  return '조금 도전적이에요';
};

const getDifficultyLabel = (diff?: string): string => {
  if (diff === 'easy') return '초급';
  if (diff === 'hard') return '고급';
  return '중급';
};

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function AvatarDetailScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();
  const { avatar } = route.params || {};

  const [isFavorite, setIsFavorite] = useState(false);

  const handleStartChat = () => navigation.navigate('SituationSelection', { avatar });
  const handleEdit      = () => navigation.navigate('CreateAvatar', { avatar, isEdit: true });

  const handleDelete = () => {
    Alert.alert('아바타 삭제', '정말 삭제하시겠습니까?', [
      { text: '취소', style: 'cancel' },
      {
        text: '삭제', style: 'destructive',
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
  const formalityToUser   = (avatar?.formality_to_user   || 'polite') as SpeechLevel;
  const formalityFromUser = (avatar?.formality_from_user || 'polite') as SpeechLevel;
  const bioText           = avatar?.bio ? stripMarkdown(avatar.bio) : buildMockBio(avatar);
  const genderLabel       = avatar?.gender === 'male'   ? '남성'
                          : avatar?.gender === 'female' ? '여성'
                          : avatar?.gender === 'other'  ? '기타' : null;
  const roleLabel         = avatar?.custom_role || avatar?.role || '';

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <ChevronLeft size={18} color="#111" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>아바타 정보</Text>
        <TouchableOpacity onPress={handleEdit} style={styles.headerBtn}>
          <Edit size={16} color={BRAND} />
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* ── Hero ── */}
        <View style={styles.hero}>
          {/* gradient ring via border trick */}
          <View style={styles.avRing}>
            <View style={[styles.avInner, { backgroundColor: avatar?.avatar_bg || '#C4B5FD' }]}>
              <Icon name={(avatar?.icon || 'user') as any} size={44} color="#fff" />
            </View>
          </View>

          <View style={styles.nameRow}>
            <Text style={styles.avatarName}>{avatar?.name_ko || '아바타'}</Text>
            <TouchableOpacity
              style={[styles.favBtn, isFavorite && styles.favBtnOn]}
              onPress={() => setIsFavorite(!isFavorite)}
            >
              <Heart size={15} color={isFavorite ? '#FF4D4D' : '#ccc'} fill={isFavorite ? '#FF4D4D' : 'none'} />
            </TouchableOpacity>
          </View>

          {avatar?.name_en ? <Text style={styles.avatarSub}>{avatar.name_en}</Text> : null}
          {roleLabel ? <Text style={styles.avatarRole}>{roleLabel}</Text> : null}

          <View style={styles.heroPills}>
            <View style={styles.pillType}>
              <Text style={styles.pillTypeText}>
                {avatar?.avatar_type === 'real' ? '실제 인물' : '가상 인물'}
              </Text>
            </View>
            {avatar?.difficulty && (
              <View style={styles.pillDiff}>
                <Text style={styles.pillDiffText}>{getDifficultyLabel(avatar.difficulty)}</Text>
              </View>
            )}
          </View>
        </View>

        {/* ── Stats ── */}
        <View style={styles.stats}>
          {[
            { icon: <MessageCircle size={15} color={BRAND}      />, bg: '#EDE9FE', value: '8',    label: '대화'      },
            { icon: <Clock         size={15} color="#22C55E"    />, bg: '#DCFCE7', value: '45분', label: '연습 시간' },
            { icon: <TrendingUp    size={15} color="#EAB308"    />, bg: '#FEF9C3', value: '82%',  label: '평균 점수' },
          ].map((s, i) => (
            <View key={i} style={styles.statCard}>
              <View style={[styles.statIcon, { backgroundColor: s.bg }]}>{s.icon}</View>
              <Text style={styles.statValue}>{s.value}</Text>
              <Text style={styles.statLabel}>{s.label}</Text>
            </View>
          ))}
        </View>

        {/* ── 기본 정보 ── */}
        <Text style={styles.sectionLabel}>기본 정보</Text>
        <View style={styles.infoGrid}>

          {avatar?.age ? (
            <View style={styles.miniCard}>
              <View style={[styles.miniIcon, { backgroundColor: '#EDE9FE' }]}>
                <MessageCircle size={13} color={BRAND} />
              </View>
              <Text style={styles.miniLbl}>나이</Text>
              <Text style={styles.miniBig}>{avatar.age}</Text>
              <Text style={styles.miniDesc}>{getAgeDesc(avatar.age)}</Text>
            </View>
          ) : null}

          {genderLabel ? (
            <View style={styles.miniCard}>
              <View style={[styles.miniIcon, { backgroundColor: '#FCE7F3' }]}>
                <Heart size={13} color="#EC4899" />
              </View>
              <Text style={styles.miniLbl}>성별</Text>
              <Text style={[styles.miniBig, { fontSize: 18 }]}>{genderLabel}</Text>
              <Text style={styles.miniDesc}>{getGenderDesc(avatar?.gender)}</Text>
            </View>
          ) : null}

          {avatar?.difficulty ? (
            <View style={styles.miniCard}>
              <View style={[styles.miniIcon, { backgroundColor: '#FEF9C3' }]}>
                <TrendingUp size={13} color="#EAB308" />
              </View>
              <Text style={styles.miniLbl}>난이도</Text>
              <Text style={[styles.miniBig, { fontSize: 18 }]}>{getDifficultyLabel(avatar.difficulty)}</Text>
              <Text style={styles.miniDesc}>{getDifficultyDesc(avatar.difficulty)}</Text>
            </View>
          ) : null}

          {roleLabel ? (
            <View style={styles.miniCard}>
              <View style={[styles.miniIcon, { backgroundColor: '#DCFCE7' }]}>
                <Clock size={13} color="#22C55E" />
              </View>
              <Text style={styles.miniLbl}>관계</Text>
              <Text style={[styles.miniBig, { fontSize: 15 }]}>{roleLabel}</Text>
              <Text style={styles.miniDesc}>함께 연습하는 상대예요</Text>
            </View>
          ) : null}

          {avatar?.relationship_description ? (
            <View style={styles.miniCardWide}>
              <View style={[styles.miniIcon, { backgroundColor: '#EDE9FE' }]}>
                <MessageCircle size={13} color={BRAND} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.miniLbl}>관계 설명</Text>
                <Text style={styles.miniDescWide}>{avatar.relationship_description}</Text>
              </View>
            </View>
          ) : null}

        </View>

        {/* ── 말투 설정 ── */}
        <Text style={styles.sectionLabel}>말투 설정</Text>
        <View style={styles.speechRow}>
          {[
            { label: '아바타 → 나',  level: formalityToUser },
            { label: '나 → 아바타', level: formalityFromUser },
          ].map((s, i) => (
            <View key={i} style={styles.speechCard}>
              <Text style={styles.speechDir}>{s.label}</Text>
              <View style={styles.speechBadge}>
                <Text style={styles.speechBadgeText}>
                  {SPEECH_LEVELS[s.level]?.name_ko || '해요체'}
                </Text>
              </View>
            </View>
          ))}
        </View>

        {/* ── 관심사 ── */}
        {(avatar?.interests ?? []).length > 0 && (
          <>
            <Text style={styles.sectionLabel}>관심사</Text>
            <View style={styles.tagWrap}>
              {avatar.interests.map((item: string, i: number) => (
                <View key={i} style={styles.tagSel}>
                  <Text style={styles.tagSelText}>{item}</Text>
                </View>
              ))}
            </View>
          </>
        )}

        {/* ── 성격 ── */}
        {(avatar?.personality_traits ?? []).length > 0 && (
          <>
            <Text style={styles.sectionLabel}>성격</Text>
            <View style={styles.tagWrap}>
              {avatar.personality_traits.map((trait: string, i: number) => (
                <View key={i} style={styles.tagOut}>
                  <Text style={styles.tagOutText}>{trait}</Text>
                </View>
              ))}
            </View>
          </>
        )}

        {/* ── 싫어하는 주제 ── */}
        {(avatar?.dislikes ?? []).length > 0 && (
          <>
            <Text style={styles.sectionLabel}>싫어하는 주제</Text>
            <View style={styles.tagWrap}>
              {avatar.dislikes.map((item: string, i: number) => (
                <View key={i} style={styles.tagOut}>
                  <Text style={styles.tagOutText}>{item}</Text>
                </View>
              ))}
            </View>
          </>
        )}

        {/* ── AI 참고 메모 ── */}
        {avatar?.memo && (
          <>
            <Text style={styles.sectionLabel}>AI 참고 메모</Text>
            <View style={styles.guideCard}>
              <Text style={styles.memoText}>{avatar.memo}</Text>
            </View>
          </>
        )}

        {/* ── 아바타 관련 설명 ── */}
        {avatar?.description && (
          <>
            <Text style={styles.sectionLabel}>아바타 관련 설명</Text>
            <View style={styles.guideCard}>
              <Text style={styles.memoText}>{avatar.description}</Text>
            </View>
          </>
        )}

        {/* ── 대화 가이드 ── */}
        <Text style={styles.sectionLabel}>대화 가이드</Text>
        <View style={styles.guideCard}>
          <View style={styles.guideHead}>
            <View style={styles.guideDot} />
            <Text style={styles.guideLbl}>
              {avatar?.bio ? 'HyperCLOVA X 분석' : 'AI 자동 생성'}
            </Text>
          </View>
          <Text style={styles.guideText}>{bioText}</Text>
        </View>

        {/* ── Delete ── */}
        <TouchableOpacity style={styles.deleteBtn} onPress={handleDelete}>
          <Trash2 size={14} color="#FF4D4D" />
          <Text style={styles.deleteBtnText}>아바타 삭제</Text>
        </TouchableOpacity>

      </ScrollView>

      {/* Footer */}
      <View style={styles.footer}>
        <TouchableOpacity style={styles.startBtn} onPress={handleStartChat}>
          <Text style={styles.startBtnText}>대화 시작하기</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const BRAND = '#6C3BFF';
const BG    = '#F7F7FB';

const styles = StyleSheet.create({
  safe:    { flex: 1, backgroundColor: BG },
  content: { paddingHorizontal: 16, paddingBottom: 110, paddingTop: 4 },

  // Header
  header:      { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12 },
  headerBtn:   { width: 36, height: 36, borderRadius: 18, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 15, fontWeight: '500', color: '#111' },

  // Hero
  hero:       { alignItems: 'center', paddingTop: 8, paddingBottom: 24, gap: 7 },
  avRing:     { width: 100, height: 100, borderRadius: 50, padding: 3, marginBottom: 4, backgroundColor: '#A78BFA' },
  avInner:    { width: '100%', height: '100%', borderRadius: 50, alignItems: 'center', justifyContent: 'center' },
  nameRow:    { flexDirection: 'row', alignItems: 'center', gap: 8 },
  avatarName: { fontSize: 22, fontWeight: '500', color: '#111' },
  favBtn:     { width: 30, height: 30, borderRadius: 15, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  favBtnOn:   { backgroundColor: '#FFE4E4' },
  avatarSub:  { fontSize: 13, color: '#aaa', marginTop: -3 },
  avatarRole: { fontSize: 13, color: '#888' },
  heroPills:  { flexDirection: 'row', gap: 7, marginTop: 2 },
  pillType:       { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 20, backgroundColor: '#EDE9FE' },
  pillTypeText:   { fontSize: 11, fontWeight: '500', color: BRAND },
  pillDiff:       { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 20, backgroundColor: '#FEF9C3' },
  pillDiffText:   { fontSize: 11, fontWeight: '500', color: '#92400E' },

  // Stats
  stats:     { flexDirection: 'row', gap: 10, marginBottom: 24 },
  statCard:  { flex: 1, backgroundColor: '#fff', borderRadius: 20, padding: 14, alignItems: 'center', gap: 5 },
  statIcon:  { width: 32, height: 32, borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginBottom: 2 },
  statValue: { fontSize: 16, fontWeight: '500', color: '#111' },
  statLabel: { fontSize: 10, color: '#999' },

  // Section label
  sectionLabel: { fontSize: 11, fontWeight: '500', color: '#999', letterSpacing: 0.5, marginBottom: 10 },

  // Info grid
  infoGrid:     { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 24 },
  miniCard:     { width: '47.5%', backgroundColor: '#fff', borderRadius: 20, padding: 15, gap: 3 },
  miniCardWide: { width: '100%', backgroundColor: '#fff', borderRadius: 20, padding: 15, flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  miniIcon:     { width: 28, height: 28, borderRadius: 10, alignItems: 'center', justifyContent: 'center', marginBottom: 7 },
  miniLbl:      { fontSize: 10, color: '#bbb', fontWeight: '500', letterSpacing: 0.4 },
  miniBig:      { fontSize: 24, fontWeight: '500', color: '#111', lineHeight: 28, marginTop: 1 },
  miniDesc:     { fontSize: 11, color: '#888', lineHeight: 16, marginTop: 3 },
  miniDescWide: { fontSize: 13, color: '#444', lineHeight: 20, marginTop: 4 },

  // Speech
  speechRow:       { flexDirection: 'row', gap: 8, marginBottom: 24 },
  speechCard:      { flex: 1, backgroundColor: '#fff', borderRadius: 20, padding: 14, alignItems: 'center', gap: 8 },
  speechDir:       { fontSize: 10, color: '#aaa' },
  speechBadge:     { backgroundColor: BRAND, paddingHorizontal: 18, paddingVertical: 7, borderRadius: 20 },
  speechBadgeText: { fontSize: 13, fontWeight: '500', color: '#fff' },

  // Tags
  tagWrap:    { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 24 },
  tagSel:     { paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20, backgroundColor: '#EDE9FE' },
  tagSelText: { fontSize: 12, fontWeight: '500', color: BRAND },
  tagOut:     { paddingHorizontal: 14, paddingVertical: 7, borderRadius: 20, backgroundColor: '#fff', borderWidth: 0.5, borderColor: '#E5E5EA' },
  tagOutText: { fontSize: 12, fontWeight: '500', color: '#555' },

  // Guide / memo
  guideCard: { backgroundColor: '#fff', borderRadius: 20, padding: 16, marginBottom: 24 },
  guideHead: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10 },
  guideDot:  { width: 7, height: 7, borderRadius: 4, backgroundColor: BRAND },
  guideLbl:  { fontSize: 11, fontWeight: '500', color: BRAND },
  guideText: { fontSize: 13, color: '#555', lineHeight: 21 },
  memoText:  { fontSize: 13, color: '#555', lineHeight: 21 },

  // Delete
  deleteBtn:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingVertical: 12, marginBottom: 8 },
  deleteBtnText: { fontSize: 13, fontWeight: '500', color: '#FF4D4D' },

  // Footer
  footer:       { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 16, paddingBottom: 28, backgroundColor: BG },
  startBtn:     { backgroundColor: BRAND, borderRadius: 22, paddingVertical: 15, alignItems: 'center' },
  startBtnText: { fontSize: 15, fontWeight: '500', color: '#fff' },
});