import AsyncStorage from '@react-native-async-storage/async-storage';

const STORAGE_KEY = 'conversation_previews_v1';
const MAX_PREVIEWS = 30;

export interface ConversationPreview {
  sessionId: string;
  avatarId: string;
  avatarName?: string;
  situation?: string;
  userSnippet?: string;
  aiSnippet?: string;
  updatedAt: string;
  messageCount: number;
}

const clip = (text?: string, max = 44): string => {
  const normalized = String(text || '').replace(/\s+/g, ' ').trim();
  if (!normalized) return '';
  return normalized.length > max ? `${normalized.slice(0, max - 1)}…` : normalized;
};

const readAll = async (): Promise<ConversationPreview[]> => {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const writeAll = async (items: ConversationPreview[]) => {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_PREVIEWS)));
};

export const saveConversationPreview = async (preview: ConversationPreview) => {
  const current = await readAll();
  const next = [preview, ...current.filter((item) => item.sessionId !== preview.sessionId && item.avatarId !== preview.avatarId)]
    .sort((a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));
  await writeAll(next);
};

export const getConversationPreviewMapByAvatar = async (): Promise<Record<string, ConversationPreview>> => {
  const items = await readAll();
  return items.reduce<Record<string, ConversationPreview>>((acc, item) => {
    if (!acc[item.avatarId]) acc[item.avatarId] = item;
    return acc;
  }, {});
};

export const removeConversationPreview = async (avatarId: string) => {
  const current = await readAll();
  await writeAll(current.filter((item) => item.avatarId !== avatarId));
};

export const buildConversationPreviewText = (preview?: ConversationPreview | null): string => {
  if (!preview) return '';
  if (preview.userSnippet && preview.aiSnippet) {
    return `나: ${preview.userSnippet}\nAI: ${preview.aiSnippet}`;
  }
  if (preview.aiSnippet) return `AI: ${preview.aiSnippet}`;
  if (preview.userSnippet) return `나: ${preview.userSnippet}`;
  return '';
};

export const makePreviewPayload = (params: {
  sessionId: string;
  avatarId: string;
  avatarName?: string;
  situation?: string;
  messageCount: number;
  lastUserMessage?: string;
  lastAiMessage?: string;
}): ConversationPreview => ({
  sessionId: params.sessionId,
  avatarId: params.avatarId,
  avatarName: params.avatarName,
  situation: params.situation,
  messageCount: params.messageCount,
  userSnippet: clip(params.lastUserMessage),
  aiSnippet: clip(params.lastAiMessage),
  updatedAt: new Date().toISOString(),
});
