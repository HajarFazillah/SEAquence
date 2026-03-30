import { getAuthHeader } from './apiAuth';

export interface ActiveSession {
  sessionId: string;
  avatarId: string;
  avatarName: string;
  avatarIcon: string;
  avatarBg: string;
  situation: string;
  mood: number;
  difficulty: 'easy' | 'medium' | 'hard';
  lastMessageAt: string;
}

export const SPRING_BASE_URL = 'http://10.0.2.2:8080';

export const getActiveSessions = async (): Promise<ActiveSession[]> => {
  const headers = await getAuthHeader();
  const response = await fetch(`${SPRING_BASE_URL}/api/sessions?status=active`, {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
  if (!response.ok) throw new Error('Failed to fetch active sessions');
  return response.json();
};