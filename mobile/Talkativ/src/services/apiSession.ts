import { getAuthHeader } from './apiAuth';
import { SPRING_API_BASE_URL } from '../constants';

// ─── Types ───────────────────────────────────────────────────────────────────
export interface AvatarFromDB {
  id: number;
  name_ko: string;
  name_en: string;
  avatar_type: string;
  age: string;
  gender: string;
  avatar_bg: string;
  icon: string;
  role: string;
  custom_role: string;
  relationship_description: string;
  difficulty: string;
  description: string;
  personality_traits: string[];
  speaking_style: string;
  interests: string[];
  dislikes: string[];
  memo: string;
  formality_to_user: string;
  formality_from_user: string;
  bio: string;
}

export interface ActiveSession {
  sessionId: string;
  avatarId: string;
  avatarName: string;
  avatarIcon: string;
  avatarBg: string;
  situation: string;
  mood: number;
  difficulty: 'easy' | 'medium' | 'hard';
  sessionType?: 'chat' | 'realtime';
  lastMessageAt: string;
  endedAt: string | null;
}

export interface SessionRequest {
  avatarId: string;
  avatarName: string;
  avatarIcon: string;
  avatarBg: string;
  situation?: string;
  difficulty?: string;
  sessionType?: 'chat' | 'realtime';
}

export interface SessionMessage {
  turnNumber?: number;
  role: 'user' | 'assistant';
  content: string;
  createdAt?: string;
}

export const SPRING_BASE_URL = SPRING_API_BASE_URL;

// ─── Helper ──────────────────────────────────────────────────────────────────
async function jsonHeaders(): Promise<Record<string, string>> {
  const authHeader = await getAuthHeader();
  return { 'Content-Type': 'application/json', ...authHeader };
}

// ─── Avatars ─────────────────────────────────────────────────────────────────
export const getUserAvatars = async (): Promise<AvatarFromDB[]> => {
  const headers = await jsonHeaders();
  const response = await fetch(`${SPRING_BASE_URL}/api/avatars`, { headers });
  if (!response.ok) throw new Error(`getUserAvatars failed (${response.status})`);
  return response.json();
};

// ─── Sessions ────────────────────────────────────────────────────────────────
export const getActiveSessions = async (): Promise<ActiveSession[]> => {
  const headers = await jsonHeaders();
  const response = await fetch(`${SPRING_BASE_URL}/api/sessions?status=active`, { headers });
  if (!response.ok) throw new Error('Failed to fetch active sessions');
  return response.json();
};

export const getCompletedSessions = async (): Promise<ActiveSession[]> => {
  const headers = await jsonHeaders();
  const response = await fetch(`${SPRING_BASE_URL}/api/sessions?status=completed`, { headers });
  if (!response.ok) throw new Error('Failed to fetch completed sessions');
  return response.json();
};

// Fetch all sessions for a specific avatar
export const getAvatarSessions = async (avatarId: string): Promise<ActiveSession[]> => {
  const headers = await jsonHeaders();
  const response = await fetch(`${SPRING_BASE_URL}/api/sessions?avatarId=${avatarId}`, { headers });
  if (!response.ok) throw new Error(`getAvatarSessions failed (${response.status})`);
  return response.json();
};

export const createSession = async (request: SessionRequest): Promise<ActiveSession> => {
  const headers = await jsonHeaders();
  const response = await fetch(`${SPRING_BASE_URL}/api/sessions`, {
    method: 'POST',
    headers,
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(`createSession failed (${response.status})`);
  return response.json();
};

export const deleteAllMySessions = async (): Promise<void> => {
  const headers = await jsonHeaders();
  const response = await fetch(`${SPRING_BASE_URL}/api/sessions/me`, {
    method: 'DELETE',
    headers,
  });
  if (!response.ok && response.status !== 204) {
    throw new Error(`deleteAllMySessions failed (${response.status})`);
  }
};

export const endSession = async (sessionId: string): Promise<void> => {
  const headers = await jsonHeaders();
  const response = await fetch(`${SPRING_BASE_URL}/api/sessions/${sessionId}/end`, {
    method: 'PATCH',
    headers,
  });
  if (!response.ok) throw new Error(`endSession failed (${response.status})`);
};

export const getSessionMessages = async (sessionId: string): Promise<SessionMessage[]> => {
  const headers = await jsonHeaders();
  const response = await fetch(`${SPRING_BASE_URL}/api/sessions/${sessionId}/messages`, { headers });
  if (!response.ok) throw new Error(`getSessionMessages failed (${response.status})`);
  return response.json();
};

export const saveSessionMessages = async (
  sessionId: string,
  messages: SessionMessage[],
): Promise<void> => {
  const headers = await jsonHeaders();
  const response = await fetch(`${SPRING_BASE_URL}/api/sessions/${sessionId}/messages`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(messages.map(({ role, content }) => ({ role, content }))),
  });
  if (!response.ok && response.status !== 204) {
    throw new Error(`saveSessionMessages failed (${response.status})`);
  }
};
