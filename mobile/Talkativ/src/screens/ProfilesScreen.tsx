import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, SafeAreaView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

const CATEGORIES = [
  { id: 'all', icon: '⊞', label: 'All' },
  { id: 'c1',  icon: '♡', label: 'Category' },
  { id: 'c2',  icon: '☹', label: 'Category' },
  { id: 'c3',  icon: '☽', label: 'Category' },
  { id: 'c4',  icon: '☺', label: 'Category' },
];

const TABS = ['All', 'Avatar', 'Created'];

const STATUS_STYLE: Record<string, { bg: string; color: string }> = {
  Done:          { bg: '#EAE8FF', color: '#6C3BFF' },
  'In Progress': { bg: '#FFF0E0', color: '#F4A261' },
  'To-do':       { bg: '#E8F5E9', color: '#4CAF50' },
};

const mockProfiles = [
  { id: '1', situation: 'Situation', name: '김에은', time: '10:00 AM', status: 'Done',        avatarBg: '#FFB6C1' },
  { id: '2', situation: 'Situation', name: '김에은', time: '12:00 PM', status: 'In Progress', avatarBg: '#FFB6C1' },
  { id: '3', situation: 'Situation', name: '김에은', time: '07:00 PM', status: 'To-do',       avatarBg: '#C8B4F8' },
];

export default function ProfilesScreen() {
  const navigation = useNavigation<any>();
  const [activeCategory, setActiveCategory] = useState('all');
  const [activeTab, setActiveTab] = useState('All');
  const [search, setSearch] = useState('');

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

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Search */}
        <View style={styles.searchBar}>
          <TextInput
            style={styles.searchInput}
            placeholder="Search"
            placeholderTextColor="#B0B0C5"
            value={search}
            onChangeText={setSearch}
          />
          <Text style={styles.searchIcon}>🔍</Text>
        </View>

        {/* Category Icons */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
          {CATEGORIES.map((cat) => (
            <TouchableOpacity
              key={cat.id}
              style={styles.categoryItem}
              onPress={() => setActiveCategory(cat.id)}
            >
              <View style={[
                styles.categoryIcon,
                activeCategory === cat.id && styles.categoryIconActive,
              ]}>
                <Text style={styles.categoryEmoji}>{cat.icon}</Text>
              </View>
              <Text style={[
                styles.categoryLabel,
                activeCategory === cat.id && styles.categoryLabelActive,
              ]}>
                {cat.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Tabs */}
        <View style={styles.tabRow}>
          {TABS.map((tab) => (
            <TouchableOpacity
              key={tab}
              style={[styles.tab, activeTab === tab && styles.tabActive]}
              onPress={() => setActiveTab(tab)}
            >
              <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
                {tab}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Profile List */}
        <View style={styles.list}>
          {mockProfiles.map((item) => {
            const s = STATUS_STYLE[item.status];
            return (
              <TouchableOpacity
                key={item.id}
                style={styles.card}
                onPress={() => navigation.navigate('Chat', { name: item.name, avatarBg: item.avatarBg })}
              >
                <View style={styles.cardLeft}>
                  <Text style={styles.cardSituation}>{item.situation}</Text>
                  <Text style={styles.cardName}>{item.name}</Text>
                  <View style={styles.cardTimeRow}>
                    <Text style={styles.clockIcon}>🕐</Text>
                    <Text style={styles.cardTime}>{item.time}</Text>
                    <View style={[styles.statusBadge, { backgroundColor: s.bg }]}>
                      <Text style={[styles.statusText, { color: s.color }]}>{item.status}</Text>
                    </View>
                  </View>
                </View>
                <View style={[styles.avatarCircle, { backgroundColor: item.avatarBg }]}>
                  <Text style={styles.avatarEmoji}>👜</Text>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

      </ScrollView>

      {/* Create Button */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.createBtn}
          onPress={() => navigation.navigate('CreateProfileStep2')}
        >
          <Text style={styles.createBtnText}>Create</Text>
          <Text style={styles.createBtnArrow}>→</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:               { flex: 1, backgroundColor: '#F7F7FB' },
  header:             { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  headerBtn:          { width: 36, alignItems: 'center' },
  backArrow:          { fontSize: 18, color: '#1A1A2E' },
  bellIcon:           { fontSize: 20 },
  headerTitle:        { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },

  content:            { paddingHorizontal: 20, paddingBottom: 100 },

  searchBar:          { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 14, paddingHorizontal: 16, paddingVertical: 12, marginBottom: 20, shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 4, elevation: 1 },
  searchInput:        { flex: 1, fontSize: 15, color: '#1A1A2E' },
  searchIcon:         { fontSize: 16 },

  categoryScroll:     { marginBottom: 20 },
  categoryItem:       { alignItems: 'center', marginRight: 16 },
  categoryIcon:       { width: 52, height: 52, borderRadius: 16, backgroundColor: '#E8E8F0', alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  categoryIconActive: { backgroundColor: '#6C3BFF' },
  categoryEmoji:      { fontSize: 20 },
  categoryLabel:      { fontSize: 11, color: '#B0B0C5' },
  categoryLabelActive:{ color: '#6C3BFF', fontWeight: '600' },

  tabRow:             { flexDirection: 'row', gap: 10, marginBottom: 20 },
  tab:                { paddingHorizontal: 20, paddingVertical: 8, borderRadius: 20, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E2E2EC' },
  tabActive:          { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  tabText:            { fontSize: 13, color: '#6C6C80', fontWeight: '500' },
  tabTextActive:      { color: '#FFFFFF', fontWeight: '700' },

  list:               { gap: 12 },
  card:               { backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 1 },
  cardLeft:           { flex: 1 },
  cardSituation:      { fontSize: 11, color: '#B0B0C5', marginBottom: 2 },
  cardName:           { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 6 },
  cardTimeRow:        { flexDirection: 'row', alignItems: 'center', gap: 4 },
  clockIcon:          { fontSize: 12 },
  cardTime:           { fontSize: 12, color: '#B0B0C5', marginRight: 8 },
  statusBadge:        { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 10 },
  statusText:         { fontSize: 11, fontWeight: '600' },
  avatarCircle:       { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  avatarEmoji:        { fontSize: 18 },

  footer:             { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#F7F7FB' },
  createBtn:          { backgroundColor: '#6C3BFF', borderRadius: 16, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
  createBtnText:      { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  createBtnArrow:     { color: '#FFFFFF', fontSize: 18 },
});
