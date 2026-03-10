import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView, TouchableOpacity,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';

export default function RealtimeSessionScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const avatar = route.params?.avatar ?? { name: '김예은', avatarBg: '#FFB6C1' };

  const [seconds, setSeconds] = useState(0);
  const [isRunning, setIsRunning] = useState(true);

  // Timer
  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(interval);
  }, [isRunning]);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60).toString().padStart(2, '0');
    const sec = (s % 60).toString().padStart(2, '0');
    return `${m}:${sec}`;
  };

  const handleEnd = () => {
    setIsRunning(false);
    navigation.navigate('Feedback', { avatar, duration: formatTime(seconds) });
  };

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={handleEnd} style={styles.headerBtn}>
          <Text style={styles.backArrow}>◀</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Profiles</Text>
        <TouchableOpacity style={styles.headerBtn}>
          <Text style={styles.bellIcon}>🔔</Text>
        </TouchableOpacity>
      </View>

      {/* Avatar name + timer */}
      <View style={styles.heroSection}>
        <Text style={styles.avatarName}>{avatar.name}</Text>
        <Text style={styles.timer}>{formatTime(seconds)}</Text>
      </View>

      {/* Conversation Guide Card */}
      <View style={styles.guideCard}>
        <Text style={styles.guideLabel}>Conversation Guide</Text>
        <Text style={styles.guideText}>Real time conversation guide</Text>
        {/* TODO: populate with AI-generated guide based on avatar profile */}
      </View>

      {/* Controls */}
      <View style={styles.controls}>
        {/* End session */}
        <TouchableOpacity style={styles.controlBtnOutline} onPress={handleEnd}>
          <Text style={styles.controlBtnOutlineText}>✕</Text>
        </TouchableOpacity>

        {/* Pause / Resume */}
        <TouchableOpacity
          style={styles.controlBtnMain}
          onPress={() => setIsRunning((r) => !r)}
        >
          <Text style={styles.controlBtnMainText}>{isRunning ? '⏸' : '▶'}</Text>
        </TouchableOpacity>

        {/* Favourite */}
        <TouchableOpacity style={styles.controlBtnGhost}>
          <Text style={styles.controlBtnGhostText}>♡</Text>
        </TouchableOpacity>
      </View>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:                   { flex: 1, backgroundColor: '#FFFFFF' },

  header:                 { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  headerBtn:              { width: 36, alignItems: 'center' },
  backArrow:              { fontSize: 18, color: '#1A1A2E' },
  bellIcon:               { fontSize: 20 },
  headerTitle:            { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },

  heroSection:            { flex: 1, alignItems: 'center', justifyContent: 'center' },
  avatarName:             { fontSize: 36, fontWeight: '700', color: '#1A1A2E', marginBottom: 10 },
  timer:                  { fontSize: 18, color: '#B0B0C5', fontWeight: '500' },

  guideCard:              { marginHorizontal: 20, marginBottom: 40, backgroundColor: '#F7F7FB', borderRadius: 20, padding: 20, minHeight: 120 },
  guideLabel:             { fontSize: 11, color: '#B0B0C5', marginBottom: 10 },
  guideText:              { fontSize: 15, color: '#1A1A2E', fontWeight: '500' },

  controls:               { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 24, paddingBottom: 48 },

  controlBtnOutline:      { width: 56, height: 56, borderRadius: 28, borderWidth: 2, borderColor: '#F4A261', alignItems: 'center', justifyContent: 'center' },
  controlBtnOutlineText:  { fontSize: 20, color: '#F4A261' },

  controlBtnMain:         { width: 72, height: 72, borderRadius: 36, backgroundColor: '#1A1A2E', alignItems: 'center', justifyContent: 'center' },
  controlBtnMainText:     { fontSize: 26, color: '#FFFFFF' },

  controlBtnGhost:        { width: 56, height: 56, borderRadius: 28, backgroundColor: '#E8E8F0', alignItems: 'center', justifyContent: 'center' },
  controlBtnGhostText:    { fontSize: 22, color: '#B0B0C5' },
});
