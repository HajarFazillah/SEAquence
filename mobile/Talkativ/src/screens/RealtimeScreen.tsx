import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity, TextInput,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

const mockAvatars = [
  { id: '1', name: '김에은',  category: '아바타',      avatarBg: '#FFB6C1', relationship: 'Work' },
  { id: '2', name: '하자',    category: '실물 프로필', avatarBg: '#C8B4F8', relationship: 'Friend' },
  { id: '3', name: '민준',    category: '실물 프로필', avatarBg: '#B4D4F8', relationship: 'Work' },
];

export default function RealtimeScreen() {
  const navigation = useNavigation<any>();
  const [search, setSearch] = useState('');

  const filtered = mockAvatars.filter((a) =>
    a.name.includes(search) || a.category.includes(search)
  );

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Real-time</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Subtitle */}
        <Text style={styles.subtitle}>Pick an avatar to start your session</Text>

        {/* Search */}
        <View style={styles.searchBar}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search avatar"
            placeholderTextColor="#B0B0C5"
            value={search}
            onChangeText={setSearch}
          />
          <Text style={styles.searchIcon}>🔍</Text>
        </View>

        {/* Avatar List */}
        <View style={styles.list}>
          {filtered.map((item) => (
            <TouchableOpacity
              key={item.id}
              style={styles.card}
              onPress={() => navigation.navigate('RealtimeSession', { avatar: item })}
            >
              <View style={[styles.avatarCircle, { backgroundColor: item.avatarBg }]}>
                <Text style={styles.avatarEmoji}>👜</Text>
              </View>
              <View style={styles.cardText}>
                <Text style={styles.cardName}>{item.name}</Text>
                <Text style={styles.cardCategory}>{item.category} · {item.relationship}</Text>
              </View>
              <Text style={styles.cardArrow}>›</Text>
            </TouchableOpacity>
          ))}
        </View>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:          { flex: 1, backgroundColor: '#F7F7FB' },
  header:        { paddingHorizontal: 20, paddingVertical: 16 },
  headerTitle:   { fontSize: 22, fontWeight: '700', color: '#1A1A2E' },

  content:       { paddingHorizontal: 20, paddingBottom: 40 },
  subtitle:      { fontSize: 14, color: '#6C6C80', marginBottom: 20 },

  searchBar:     { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 14, paddingHorizontal: 16, paddingVertical: 12, marginBottom: 24, shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 4, elevation: 1 },
  searchInput:   { flex: 1, fontSize: 15, color: '#1A1A2E' },
  searchIcon:    { fontSize: 16 },

  list:          { gap: 12 },
  card:          { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 1 },
  avatarCircle:  { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  avatarEmoji:   { fontSize: 22 },
  cardText:      { flex: 1 },
  cardName:      { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 3 },
  cardCategory:  { fontSize: 12, color: '#B0B0C5' },
  cardArrow:     { fontSize: 22, color: '#C0C0D0' },
});
