import React, { useState, useCallback } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, TouchableOpacity, TextInput, ActivityIndicator, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, useFocusEffect } from '@react-navigation/native';
import {
  Search, Bookmark, Volume2, Trash2, BookOpen, MessageCircle,
  ChevronDown, ChevronUp,
} from 'lucide-react-native';
import { Header, Card } from '../components';
import { fetchMyVocabulary, deleteVocabulary, SavedVocab } from '../services/apiVocabulary';

interface VocabItem {
  id: number;
  word: string;
  meaning: string;
  example: string;
  savedAt: string;
  fromAvatar?: string;
}

const formatRelative = (iso?: string | null): string => {
  if (!iso) return '';
  const ts = Date.parse(iso);
  if (isNaN(ts)) return '';
  const diffMs = Date.now() - ts;
  const day = 24 * 60 * 60 * 1000;
  const days = Math.floor(diffMs / day);
  if (days < 1) return '오늘';
  if (days < 7) return `${days}일 전`;
  const weeks = Math.floor(days / 7);
  if (weeks < 5) return `${weeks}주 전`;
  return new Date(ts).toLocaleDateString('ko-KR');
};

const toItem = (v: SavedVocab): VocabItem => ({
  id: v.id,
  word: v.word,
  meaning: v.meaning ?? '',
  example: v.example ?? '',
  savedAt: formatRelative(v.createdAt),
  fromAvatar: v.fromAvatar ?? undefined,
});

export default function SavedVocabularyScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const type: 'words' | 'phrases' = route.params?.type || 'words';
  const apiKind: 'word' | 'phrase' = type === 'words' ? 'word' : 'phrase';

  const [search, setSearch] = useState('');
  const [expandedItem, setExpandedItem] = useState<number | null>(null);
  const [items, setItems] = useState<VocabItem[]>([]);
  const [loading, setLoading] = useState(true);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      (async () => {
        setLoading(true);
        try {
          const rows = await fetchMyVocabulary(apiKind);
          if (!cancelled) setItems(rows.map(toItem));
        } catch (e) {
          console.log('fetch vocab failed:', e);
          if (!cancelled) setItems([]);
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();
      return () => { cancelled = true; };
    }, [apiKind]),
  );

  const filteredItems = items.filter((item) =>
    item.word.includes(search) ||
    item.meaning.toLowerCase().includes(search.toLowerCase())
  );

  const handleDelete = (id: number) => {
    Alert.alert('삭제', '저장한 항목을 삭제할까요?', [
      { text: '취소', style: 'cancel' },
      {
        text: '삭제',
        style: 'destructive',
        onPress: async () => {
          // Optimistic remove
          const previous = items;
          setItems(prev => prev.filter(it => it.id !== id));
          try {
            await deleteVocabulary(id);
          } catch (e) {
            console.log('delete vocab failed:', e);
            setItems(previous);
            Alert.alert('오류', '삭제에 실패했어요.');
          }
        },
      },
    ]);
  };

  const handlePlayAudio = (word: string) => {
    // TODO: Implement text-to-speech
    console.log('Playing audio for:', word);
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header 
        title={type === 'words' ? '저장한 단어' : '저장한 표현'} 
      />

      <View style={styles.container}>
        {/* Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            {type === 'words' ? (
              <BookOpen size={20} color="#6C3BFF" />
            ) : (
              <MessageCircle size={20} color="#4CAF50" />
            )}
            <Text style={styles.statCount}>{items.length}</Text>
            <Text style={styles.statLabel}>
              {type === 'words' ? '단어' : '표현'}
            </Text>
          </View>
        </View>

        {/* Search */}
        <View style={styles.searchContainer}>
          <Search size={20} color="#B0B0C5" />
          <TextInput
            style={styles.searchInput}
            value={search}
            onChangeText={setSearch}
            placeholder="검색..."
            placeholderTextColor="#B0B0C5"
          />
        </View>

        {/* List */}
        <ScrollView 
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        >
          {loading ? (
            <View style={styles.emptyState}>
              <ActivityIndicator size="large" color="#6C3BFF" />
              <Text style={styles.emptyTitle}>불러오는 중...</Text>
            </View>
          ) : filteredItems.length === 0 ? (
            <View style={styles.emptyState}>
              <Bookmark size={48} color="#E2E2EC" />
              <Text style={styles.emptyTitle}>
                {search ? '검색 결과가 없어요' : '저장한 항목이 없어요'}
              </Text>
              <Text style={styles.emptySubtitle}>
                대화 중 유용한 {type === 'words' ? '단어' : '표현'}를 저장해보세요
              </Text>
            </View>
          ) : (
            filteredItems.map((item) => (
              <Card key={item.id} variant="elevated" style={styles.vocabCard}>
                <TouchableOpacity 
                  style={styles.vocabHeader}
                  onPress={() => setExpandedItem(expandedItem === item.id ? null : item.id)}
                  activeOpacity={0.7}
                >
                  <View style={styles.vocabMain}>
                    <Text style={styles.vocabWord}>{item.word}</Text>
                    <Text style={styles.vocabMeaning}>{item.meaning}</Text>
                  </View>
                  <View style={styles.vocabActions}>
                    <TouchableOpacity 
                      style={styles.audioBtn}
                      onPress={() => handlePlayAudio(item.word)}
                    >
                      <Volume2 size={18} color="#6C3BFF" />
                    </TouchableOpacity>
                    {expandedItem === item.id ? (
                      <ChevronUp size={20} color="#B0B0C5" />
                    ) : (
                      <ChevronDown size={20} color="#B0B0C5" />
                    )}
                  </View>
                </TouchableOpacity>

                {expandedItem === item.id && (
                  <View style={styles.vocabExpanded}>
                    <View style={styles.exampleBox}>
                      <Text style={styles.exampleLabel}>예문</Text>
                      <Text style={styles.exampleText}>{item.example}</Text>
                    </View>
                    
                    <View style={styles.metaRow}>
                      {item.fromAvatar && (
                        <View style={styles.metaItem}>
                          <Text style={styles.metaLabel}>출처:</Text>
                          <Text style={styles.metaValue}>{item.fromAvatar}</Text>
                        </View>
                      )}
                      <View style={styles.metaItem}>
                        <Text style={styles.metaLabel}>저장:</Text>
                        <Text style={styles.metaValue}>{item.savedAt}</Text>
                      </View>
                    </View>

                    <TouchableOpacity 
                      style={styles.deleteBtn}
                      onPress={() => handleDelete(item.id)}
                    >
                      <Trash2 size={16} color="#E53935" />
                      <Text style={styles.deleteBtnText}>삭제</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </Card>
            ))
          )}
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  container: { flex: 1, paddingHorizontal: 20 },

  // Stats
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingVertical: 16,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 20,
  },
  statCount: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A2E',
  },
  statLabel: {
    fontSize: 14,
    color: '#6C6C80',
  },

  // Search
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 16,
    gap: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: '#1A1A2E',
  },

  // List
  listContent: {
    paddingBottom: 40,
    gap: 12,
  },

  // Vocab Card
  vocabCard: {
    padding: 0,
    overflow: 'hidden',
  },
  vocabHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  vocabMain: {
    flex: 1,
  },
  vocabWord: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 4,
  },
  vocabMeaning: {
    fontSize: 13,
    color: '#6C6C80',
  },
  vocabActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  audioBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F0EDFF',
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Expanded
  vocabExpanded: {
    borderTopWidth: 1,
    borderTopColor: '#F0F0F5',
    padding: 16,
    backgroundColor: '#FAFAFA',
  },
  exampleBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
  },
  exampleLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#6C3BFF',
    marginBottom: 4,
  },
  exampleText: {
    fontSize: 14,
    color: '#1A1A2E',
    lineHeight: 20,
  },
  metaRow: {
    flexDirection: 'row',
    gap: 20,
    marginBottom: 12,
  },
  metaItem: {
    flexDirection: 'row',
    gap: 4,
  },
  metaLabel: {
    fontSize: 12,
    color: '#B0B0C5',
  },
  metaValue: {
    fontSize: 12,
    color: '#6C6C80',
  },
  deleteBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    backgroundColor: '#FFEBEE',
    borderRadius: 10,
  },
  deleteBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#E53935',
  },

  // Empty
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A2E',
    marginTop: 16,
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 13,
    color: '#6C6C80',
    textAlign: 'center',
  },
});
