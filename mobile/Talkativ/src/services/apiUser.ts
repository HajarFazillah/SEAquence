import { getAuthHeader } from './apiAuth';

export interface UserProfile {
  userId: string;
  username: string;
  email: string;
  nativeLang: string;
  targetLang: string;
  koreanLevel: string;
  avatarUrl?: string;
  interests?: string[];
}

export interface UserStats {
  completedSessions: number;
  learnedExpressions: number;
  practiceMinutes: number;
  progressPercent: number;
}

export const SPRING_BASE_URL = 'http://10.0.2.2:8080';

export const getMyProfile = async (): Promise<UserProfile> => {
  const headers = await getAuthHeader();
  const response = await fetch(`${SPRING_BASE_URL}/api/users/me`, {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
  if (!response.ok) throw new Error('Failed to fetch user profile');
  return response.json();
};

export const getMyStats = async (): Promise<UserStats> => {
  const headers = await getAuthHeader();
  const response = await fetch(`${SPRING_BASE_URL}/api/users/me/stats`, {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
  if (!response.ok) throw new Error('Failed to fetch user stats');
  return response.json();
};