import AsyncStorage from '@react-native-async-storage/async-storage';
import { SPRING_API_BASE_URL } from '../constants';

export interface SavedMistake {
  id: number;
  sessionId: string;
  userId: string;
  turnNumber: number | null;
  originalText: string;
  correctedText: string;
  correctionType: string | null;
  severity: string | null;
  explanation: string | null;
  tip: string | null;
  createdAt: string;
}

export interface WeakArea {
  error_type: string;
  error_type_ko: string;
  count: number;
  severity: string;
}

const authHeaders = async (): Promise<Record<string, string>> => {
  const token = await AsyncStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const fetchMistakesBySession = async (
  sessionId: string,
): Promise<SavedMistake[]> => {
  const res = await fetch(
    `${SPRING_API_BASE_URL}/api/mistakes/session/${encodeURIComponent(sessionId)}`,
    { headers: { Accept: 'application/json; charset=utf-8', ...(await authHeaders()) } },
  );
  if (!res.ok) throw new Error(`Failed to fetch session mistakes: ${res.status}`);
  return res.json();
};

export const fetchMyMistakes = async (): Promise<SavedMistake[]> => {
  const res = await fetch(`${SPRING_API_BASE_URL}/api/mistakes/me`, {
    headers: { Accept: 'application/json; charset=utf-8', ...(await authHeaders()) },
  });
  if (!res.ok) throw new Error(`Failed to fetch my mistakes: ${res.status}`);
  return res.json();
};

export const fetchMyWeakAreas = async (): Promise<WeakArea[]> => {
  const res = await fetch(`${SPRING_API_BASE_URL}/api/mistakes/me/weak-areas`, {
    headers: { Accept: 'application/json; charset=utf-8', ...(await authHeaders()) },
  });
  if (!res.ok) throw new Error(`Failed to fetch weak areas: ${res.status}`);
  return res.json();
};

export const deleteAllMyMistakes = async (): Promise<void> => {
  const res = await fetch(`${SPRING_API_BASE_URL}/api/mistakes/me`, {
    method: 'DELETE',
    headers: await authHeaders(),
  });
  if (!res.ok && res.status !== 204) {
    throw new Error(`delete mistakes failed: ${res.status}`);
  }
};

export const saveMistakesToBackend = async (
  sessionId: string,
  turnNumber: number,
  mistakes: Array<{
    originalText: string;
    correctedText: string;
    correctionType: string;
    severity: string;
    explanation: string;
    tip?: string | null;
  }>,
): Promise<void> => {
  if (!mistakes.length) return;
  const res = await fetch(`${SPRING_API_BASE_URL}/api/mistakes`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      Accept: 'application/json',
      ...(await authHeaders()),
    },
    body: JSON.stringify({ sessionId, turnNumber, mistakes }),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`save failed ${res.status}: ${body}`);
  }
};
