import React from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity,
} from 'react-native';

const mockAvatars = [
  {
    id: '1',
    name: '김예은',
    category: '아바타',
    relationship: 'Work',
    avatarBg: '#FFB6C1',
    createdAt: 'March 5, 2026',
    status: 'Active',
  },
  // TODO: populate from API — GET /avatars
];

export default function AvatarScreen() {
  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Avatar</Text>
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Count */}
        <View style={styles.countRow}>
          <Text style={styles.countText}>{mockAvatars.length} avatar{mockAvatars.length !== 1 ? 's' : ''} created</Text>
        </View>

        {/* Avatar List */}
        <View style={styles.list}>
          {mockAvatars.map((item) => (
            <TouchableOpacity key={item.id} style={styles.card}>
              {/* Avatar circle */}
              <View style={[styles.avatarCircle, { backgroundColor: item.avatarBg }]}>
                <Text style={styles.avatarEmoji}>👜</Text>
              </View>

              {/* Info */}
              <View style={styles.cardInfo}>
                <Text style={styles.cardName}>{item.name}</Text>
                <Text style={styles.cardMeta}>{item.category} · {item.relationship}</Text>
                <Text style={styles.cardDate}>Created {item.createdAt}</Text>
              </View>

              {/* Status badge */}
              <View style={styles.statusBadge}>
                <Text style={styles.statusText}>{item.status}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* Empty state — shown when no avatars */}
        {mockAvatars.length === 0 && (
          <View style={styles.emptyState}>
            <Text style={styles.emptyEmoji}>🪆</Text>
            <Text style={styles.emptyTitle}>No avatars yet</Text>
            <Text style={styles.emptySubtitle}>Create a profile to get started</Text>
          </View>
        )}

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:           { flex: 1, backgroundColor: '#F7F7FB' },
  header:         { paddingHorizontal: 20, paddingVertical: 16 },
  headerTitle:    { fontSize: 22, fontWeight: '700', color: '#1A1A2E' },

  content:        { paddingHorizontal: 20, paddingBottom: 40 },

  countRow:       { marginBottom: 16 },
  countText:      { fontSize: 13, color: '#B0B0C5' },

  list:           { gap: 12 },
  card:           { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 16, padding: 16, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, elevation: 1 },

  avatarCircle:   { width: 52, height: 52, borderRadius: 26, alignItems: 'center', justifyContent: 'center', marginRight: 14 },
  avatarEmoji:    { fontSize: 24 },

  cardInfo:       { flex: 1 },
  cardName:       { fontSize: 16, fontWeight: '700', color: '#1A1A2E', marginBottom: 3 },
  cardMeta:       { fontSize: 12, color: '#B0B0C5', marginBottom: 2 },
  cardDate:       { fontSize: 11, color: '#C8C8D8' },

  statusBadge:    { backgroundColor: '#EAE8FF', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 10 },
  statusText:     { fontSize: 11, color: '#6C3BFF', fontWeight: '600' },

  emptyState:     { alignItems: 'center', marginTop: 80 },
  emptyEmoji:     { fontSize: 48, marginBottom: 16 },
  emptyTitle:     { fontSize: 18, fontWeight: '700', color: '#1A1A2E', marginBottom: 6 },
  emptySubtitle:  { fontSize: 14, color: '#B0B0C5' },
});
