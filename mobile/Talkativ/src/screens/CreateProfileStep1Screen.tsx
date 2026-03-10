import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, SafeAreaView, ScrollView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

const PREFERENCE_TAGS = ['친한 친구', '동료', '동료', '동료', '친한 친구', '동료', '동료', '동료', '동료'];
const SENSITIVE_TAGS  = ['친한 친구', '동료', '동료', '동료', '친한 친구', '동료', '동료', '동료', '동료'];

export default function CreateProfileStep1Screen() {
  const navigation = useNavigation<any>();
  const [selectedPrefs, setSelectedPrefs]       = useState<number[]>([0]);
  const [selectedSensitive, setSelectedSensitive] = useState<number[]>([0]);

  const togglePref = (i: number) =>
    setSelectedPrefs((prev) =>
      prev.includes(i) ? prev.filter((x) => x !== i) : [...prev, i]
    );

  const toggleSensitive = (i: number) =>
    setSelectedSensitive((prev) =>
      prev.includes(i) ? prev.filter((x) => x !== i) : [...prev, i]
    );

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <Text style={styles.backArrow}>◀</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Profiles</Text>
        <TouchableOpacity style={styles.headerBtn}>
          <Text style={styles.bellIcon}>🔔</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.content}>

        {/* Preferences Section */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>Preferences</Text>
          <View style={styles.tagGrid}>
            {PREFERENCE_TAGS.map((tag, i) => (
              <TouchableOpacity
                key={i}
                style={[styles.tag, selectedPrefs.includes(i) && styles.tagActive]}
                onPress={() => togglePref(i)}
              >
                <Text style={[styles.tagText, selectedPrefs.includes(i) && styles.tagTextActive]}>
                  {tag}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Sensitive Section */}
        <View style={styles.card}>
          <Text style={[styles.sectionLabel, { color: '#E53935' }]}>Sensitive</Text>
          <View style={styles.tagGrid}>
            {SENSITIVE_TAGS.map((tag, i) => (
              <TouchableOpacity
                key={i}
                style={[styles.tag, selectedSensitive.includes(i) && styles.tagActive]}
                onPress={() => toggleSensitive(i)}
              >
                <Text style={[styles.tagText, selectedSensitive.includes(i) && styles.tagTextActive]}>
                  {tag}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

      </ScrollView>

      {/* Next Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.nextBtn}
          onPress={() => navigation.navigate('Profiles')}
        >
          <Text style={styles.nextBtnText}>Next</Text>
          <Text style={styles.nextBtnArrow}>→</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:           { flex: 1, backgroundColor: '#F7F7FB' },
  header:         { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  headerBtn:      { width: 36, alignItems: 'center' },
  backArrow:      { fontSize: 18, color: '#1A1A2E' },
  bellIcon:       { fontSize: 20 },
  headerTitle:    { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },

  content:        { paddingHorizontal: 20, paddingBottom: 100, gap: 16 },

  card:           { backgroundColor: '#FFFFFF', borderRadius: 20, padding: 20, shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 6, elevation: 2 },
  sectionLabel:   { fontSize: 16, fontWeight: '700', color: '#2E7D32', marginBottom: 16 },

  tagGrid:        { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  tag:            { paddingHorizontal: 18, paddingVertical: 10, borderRadius: 20, borderWidth: 1.5, borderColor: '#E2E2EC', backgroundColor: '#FFFFFF' },
  tagActive:      { borderColor: '#6C3BFF', backgroundColor: '#FFFFFF' },
  tagText:        { fontSize: 14, color: '#6C6C80' },
  tagTextActive:  { color: '#6C3BFF', fontWeight: '600' },

  footer:         { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
  nextBtn:        { backgroundColor: '#6C3BFF', borderRadius: 16, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
  nextBtnText:    { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  nextBtnArrow:   { color: '#FFFFFF', fontSize: 18 },
});