import React from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';

const mockPatterns = [
  { label: '응답 시간', value: 0.9,  result: '빠름',  color: '#4CAF50' },
  { label: '대화 깊이', value: 0.55, result: '보통',  color: '#5B8DEF' },
  { label: '주제 다양성', value: 0.7, result: '좋음', color: '#9C27B0' },
];

const mockRelationship = {
  label: '좋은 관계',
  sublabel: '관계 강도',
  percentage: 87,
  color: '#5B8DEF',
};

const mockRealProfile = {
  label: '실물 프로필',
  sublabel: '하자',
  percentage: 60,
  color: '#5B8DEF',
};

export default function AnalyticsScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();
  const avatar     = route.params?.avatar;
  const duration   = route.params?.duration ?? '00:00';
  const rating     = route.params?.rating ?? 4;

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <Text style={styles.backArrow}>◀</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Analytics</Text>
        <View style={styles.headerBtn} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Top stat cards */}
        <View style={styles.cardRow}>

          {/* Relationship strength */}
          <View style={styles.statCard}>
            <Text style={styles.statCardLabel}>{mockRelationship.label}</Text>
            <View style={styles.statCardIconRow}>
              <Text style={styles.statCardEmoji}>👜</Text>
            </View>
            <Text style={styles.statCardSublabel}>{mockRelationship.sublabel}</Text>
            <Text style={styles.statCardPercent}>{mockRelationship.percentage}%</Text>
            <View style={styles.progressBg}>
              <View style={[styles.progressFill, {
                width: `${mockRelationship.percentage}%` as any,
                backgroundColor: mockRelationship.color,
              }]} />
            </View>
          </View>

          {/* Real profile */}
          <View style={styles.statCard}>
            <Text style={styles.statCardLabel}>{mockRealProfile.label}</Text>
            <View style={styles.statCardIconRow}>
              <Text style={styles.statCardEmoji}>👜</Text>
            </View>
            <Text style={styles.statCardSublabel}>{mockRealProfile.sublabel}</Text>
            <View style={styles.progressBg}>
              <View style={[styles.progressFill, {
                width: `${mockRealProfile.percentage}%` as any,
                backgroundColor: mockRealProfile.color,
              }]} />
            </View>
          </View>

        </View>

        {/* 대화 패턴 */}
        <Text style={styles.sectionTitle}>대화 패턴</Text>
        <View style={styles.patternCard}>
          {mockPatterns.map((p) => (
            <View key={p.label} style={styles.patternRow}>
              <Text style={styles.patternLabel}>{p.label}</Text>
              <View style={styles.patternBarBg}>
                <View style={[styles.patternBarFill, {
                  width: `${p.value * 100}%` as any,
                  backgroundColor: p.color,
                }]} />
              </View>
              <Text style={styles.patternResult}>{p.result}</Text>
            </View>
          ))}
        </View>

        {/* Used Vocabularies */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionCardTitle}>Used Vocabularies</Text>
          {/* TODO: populate with actual words from session */}
          <Text style={styles.sectionCardEmpty}>No data yet — will be populated after AI integration</Text>
        </View>

        {/* What can be improved */}
        <View style={styles.sectionCard}>
          <Text style={styles.sectionCardTitle}>What can be improved</Text>
          {/* TODO: populate with AI feedback */}
          <Text style={styles.sectionCardEmpty}>No data yet — will be populated after AI integration</Text>
        </View>

        {/* Done button */}
        <TouchableOpacity
          style={styles.doneBtn}
          onPress={() => navigation.navigate('Main')}
        >
          <Text style={styles.doneBtnText}>Back to Home</Text>
        </TouchableOpacity>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:               { flex: 1, backgroundColor: '#F7F7FB' },

  header:             { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  headerBtn:          { width: 36, alignItems: 'center' },
  backArrow:          { fontSize: 18, color: '#1A1A2E' },
  headerTitle:        { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },

  content:            { paddingHorizontal: 20, paddingBottom: 40 },

  // Top cards
  cardRow:            { flexDirection: 'row', gap: 14, marginBottom: 28 },
  statCard:           { flex: 1, backgroundColor: '#FFFFFF', borderRadius: 20, padding: 16, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 6, elevation: 2 },
  statCardLabel:      { fontSize: 11, color: '#B0B0C5', marginBottom: 8 },
  statCardIconRow:    { marginBottom: 6 },
  statCardEmoji:      { fontSize: 22 },
  statCardSublabel:   { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 8 },
  statCardPercent:    { fontSize: 13, color: '#6C6C80', marginBottom: 6 },
  progressBg:         { height: 6, backgroundColor: '#E2E2EC', borderRadius: 4, overflow: 'hidden' },
  progressFill:       { height: 6, borderRadius: 4 },

  // Pattern section
  sectionTitle:       { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginBottom: 14 },
  patternCard:        { backgroundColor: '#FFFFFF', borderRadius: 20, padding: 20, gap: 16, marginBottom: 20, shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 4, elevation: 1 },
  patternRow:         { flexDirection: 'row', alignItems: 'center', gap: 10 },
  patternLabel:       { width: 72, fontSize: 13, color: '#1A1A2E' },
  patternBarBg:       { flex: 1, height: 8, backgroundColor: '#E2E2EC', borderRadius: 4, overflow: 'hidden' },
  patternBarFill:     { height: 8, borderRadius: 4 },
  patternResult:      { width: 32, fontSize: 12, color: '#6C6C80', textAlign: 'right' },

  // Section cards
  sectionCard:        { backgroundColor: '#FFFFFF', borderRadius: 20, padding: 20, marginBottom: 16, shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 4, elevation: 1 },
  sectionCardTitle:   { fontSize: 15, fontWeight: '700', color: '#1A1A2E', marginBottom: 10 },
  sectionCardEmpty:   { fontSize: 12, color: '#C0C0D0', fontStyle: 'italic' },

  // Done button
  doneBtn:            { backgroundColor: '#6C3BFF', borderRadius: 16, paddingVertical: 16, alignItems: 'center', marginTop: 8 },
  doneBtnText:        { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
});
