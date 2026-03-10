import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  SafeAreaView, ScrollView, TextInput,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

export default function CreateProfileStep2Screen() {
  const navigation = useNavigation<any>();
  const [name, setName]             = useState('');
  const [description, setDescription] = useState('');

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

        {/* Relationship dropdown */}
        <TouchableOpacity style={styles.fieldRow}>
          <View style={[styles.fieldIcon, { backgroundColor: '#FFE8E8' }]}>
            <Text>👜</Text>
          </View>
          <View style={styles.fieldText}>
            <Text style={styles.fieldLabel}>Relationship</Text>
            <Text style={styles.fieldValue}>Work</Text>
          </View>
          <Text style={styles.dropdownArrow}>▼</Text>
        </TouchableOpacity>

        {/* Name input */}
        <View style={styles.inputCard}>
          <Text style={styles.inputLabel}>Name</Text>
          <TextInput
            style={styles.input}
            placeholder="Enter name"
            placeholderTextColor="#C0C0D0"
            value={name}
            onChangeText={setName}
          />
        </View>

        {/* Description input */}
        <View style={styles.inputCard}>
          <Text style={styles.inputLabel}>Description</Text>
          <TextInput
            style={[styles.input, styles.inputMultiline]}
            placeholder="profile description, by words -- will be used as a prompt"
            placeholderTextColor="#C0C0D0"
            value={description}
            onChangeText={setDescription}
            multiline
            numberOfLines={4}
          />
        </View>

        {/* Age dropdown */}
        <TouchableOpacity style={styles.fieldRow}>
          <View style={[styles.fieldIcon, { backgroundColor: '#EAE8FF' }]}>
            <Text>📅</Text>
          </View>
          <View style={styles.fieldText}>
            <Text style={styles.fieldLabel}>Age</Text>
            <Text style={styles.fieldValueMuted}>sample</Text>
          </View>
          <Text style={styles.dropdownArrow}>▼</Text>
        </TouchableOpacity>

        {/* Nationality dropdown */}
        <TouchableOpacity style={styles.fieldRow}>
          <View style={[styles.fieldIcon, { backgroundColor: '#EAE8FF' }]}>
            <Text>📅</Text>
          </View>
          <View style={styles.fieldText}>
            <Text style={styles.fieldLabel}>Nationality</Text>
            <Text style={styles.fieldValueMuted}>sample</Text>
          </View>
          <Text style={styles.dropdownArrow}>▼</Text>
        </TouchableOpacity>

        {/* Current Status dropdown */}
        <TouchableOpacity style={styles.fieldRow}>
          <View style={[styles.fieldIcon, { backgroundColor: '#EAE8FF' }]}>
            <Text>📅</Text>
          </View>
          <View style={styles.fieldText}>
            <Text style={styles.fieldLabel}>Current status</Text>
            <Text style={styles.fieldValueMuted}>sample</Text>
          </View>
        </TouchableOpacity>

      </ScrollView>

      {/* Next Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.nextBtn}
          onPress={() => navigation.navigate('CreateProfileStep1')}  // TODO: wire to next step
        >
          <Text style={styles.nextBtnText}>Next</Text>
          <Text style={styles.nextBtnArrow}>→</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:             { flex: 1, backgroundColor: '#F7F7FB' },
  header:           { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  headerBtn:        { width: 36, alignItems: 'center' },
  backArrow:        { fontSize: 18, color: '#1A1A2E' },
  bellIcon:         { fontSize: 20 },
  headerTitle:      { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },

  content:          { paddingHorizontal: 20, paddingBottom: 100, gap: 14 },

  fieldRow:         { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 4, elevation: 1 },
  fieldIcon:        { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  fieldText:        { flex: 1 },
  fieldLabel:       { fontSize: 11, color: '#B0B0C5', marginBottom: 2 },
  fieldValue:       { fontSize: 15, fontWeight: '600', color: '#1A1A2E' },
  fieldValueMuted:  { fontSize: 15, color: '#B0B0C5' },
  dropdownArrow:    { fontSize: 12, color: '#B0B0C5' },

  inputCard:        { backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 4, elevation: 1 },
  inputLabel:       { fontSize: 11, color: '#B0B0C5', marginBottom: 6 },
  input:            { fontSize: 15, color: '#1A1A2E', padding: 0 },
  inputMultiline:   { height: 90, textAlignVertical: 'top' },

  footer:           { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
  nextBtn:          { backgroundColor: '#6C3BFF', borderRadius: 16, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
  nextBtnText:      { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  nextBtnArrow:     { color: '#FFFFFF', fontSize: 18 },
});
