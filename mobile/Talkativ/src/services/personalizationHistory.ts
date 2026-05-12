import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = 'talkativ.personalization.events.v1';
const MAX_EVENTS = 300;

export interface PracticePatternEvent {
  id: string;
  sessionId: string;
  createdAt: string;
  avatarId?: string;
  avatarName?: string;
  relationshipType?: string;
  situationId?: string;
  situationName?: string;
  situationCategory?: string;
  speechLevel?: string;
  correctionTypes: string[];
  hadErrors: boolean;
  accuracyScore?: number | null;
  hintShown?: boolean;
  retrySuccess?: boolean;
}

const safeParse = (raw: string | null): PracticePatternEvent[] => {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export const fetchPracticePatternEvents = async (): Promise<PracticePatternEvent[]> => {
  const raw = await AsyncStorage.getItem(STORAGE_KEY);
  return safeParse(raw);
};

export const appendPracticePatternEvent = async (
  event: Omit<PracticePatternEvent, 'id' | 'createdAt'>,
): Promise<void> => {
  const existing = await fetchPracticePatternEvents();
  const next: PracticePatternEvent = {
    ...event,
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    createdAt: new Date().toISOString(),
  };
  await AsyncStorage.setItem(
    STORAGE_KEY,
    JSON.stringify([next, ...existing].slice(0, MAX_EVENTS)),
  );
};
