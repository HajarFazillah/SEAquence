import AsyncStorage from '@react-native-async-storage/async-storage';
import { SPRING_API_BASE_URL } from '../constants';

export interface SavedVocab {
  id: number;
  userId: string;
  kind: 'word' | 'phrase';
  word: string;
  meaning: string | null;
  example: string | null;
  fromAvatar: string | null;
  sessionId: string | null;
  createdAt: string;
}

export interface VocabSavePayload {
  kind: 'word' | 'phrase';
  word: string;
  meaning?: string;
  example?: string;
  fromAvatar?: string;
  sessionId?: string;
}

const authHeaders = async (): Promise<Record<string, string>> => {
  const token = await AsyncStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const saveVocabulary = async (
  items: VocabSavePayload[],
): Promise<SavedVocab[]> => {
  if (!items.length) return [];
  const res = await fetch(`${SPRING_API_BASE_URL}/api/vocabulary`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      Accept: 'application/json',
      ...(await authHeaders()),
    },
    body: JSON.stringify({ items }),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`vocab save failed ${res.status}: ${body}`);
  }
  return res.json();
};

export const fetchMyVocabulary = async (
  kind?: 'word' | 'phrase',
): Promise<SavedVocab[]> => {
  const url =
    `${SPRING_API_BASE_URL}/api/vocabulary/me` +
    (kind ? `?kind=${kind}` : '');
  const res = await fetch(url, {
    headers: { Accept: 'application/json; charset=utf-8', ...(await authHeaders()) },
  });
  if (!res.ok) throw new Error(`vocab fetch failed: ${res.status}`);
  return res.json();
};

export const deleteVocabulary = async (id: number): Promise<void> => {
  const res = await fetch(`${SPRING_API_BASE_URL}/api/vocabulary/${id}`, {
    method: 'DELETE',
    headers: { ...(await authHeaders()) },
  });
  if (!res.ok && res.status !== 204) {
    throw new Error(`vocab delete failed: ${res.status}`);
  }
};
