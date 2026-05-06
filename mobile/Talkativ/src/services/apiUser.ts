import { getAuthHeader } from './apiAuth';
import { IconName } from '../components/Icon';
import { SPRING_API_BASE_URL } from '../constants';

export interface UserProfile {
  userId: string;
  username: string;
  email: string;
  nativeLang: string;
  targetLang: string;
  koreanLevel: string;
  avatarUrl?: string;
  age?: string;
  gender?: string;
  interests?: string[];
  dislikes?: string[];
  memo?: string;
}

export interface UserStats {
  completedSessions: number;
  learnedExpressions: number;
  practiceMinutes: number;
  progressPercent: number;
}

export interface UserAvatar {
  id: number;
  name_ko: string;
  name_en: string;
  age: string;
  gender: string;
  avatar_type: 'fictional' | 'real';
  role: string;
  custom_role: string;
  relationship_description: string;
  description: string;
  personality_traits: string[];
  speaking_style: string;
  interests: string[];
  dislikes: string[];
  avatar_bg: string;
  icon: IconName;
  difficulty: 'easy' | 'medium' | 'hard';
  memo: string;
  formality_to_user: string;
  formality_from_user: string;
  bio: string;
}

export const SPRING_BASE_URL = SPRING_API_BASE_URL;

export const getMyProfile = async (): Promise<UserProfile> => {
  const headers = await getAuthHeader();
  const response = await fetch(`${SPRING_BASE_URL}/api/users/me`, {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
  if (!response.ok) throw new Error('Failed to fetch user profile');
  return response.json();
};

export const getUserStats = async (): Promise<UserStats> => {
  const headers = await getAuthHeader();
  const response = await fetch(`${SPRING_BASE_URL}/api/users/me/stats`, {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
  if (!response.ok) throw new Error('Failed to fetch user stats');
  return response.json();
};

export const getMyAvatars = async (): Promise<UserAvatar[]> => {
  const headers = await getAuthHeader();
  const response = await fetch(`${SPRING_BASE_URL}/api/avatars`, {
    headers: { 'Content-Type': 'application/json', ...headers },
  });
  if (!response.ok) throw new Error('Failed to fetch avatars');
  return response.json();
};

export const createAvatar = async (data: Omit<UserAvatar, 'id'>): Promise<UserAvatar> => {
  const headers = await getAuthHeader();
  const response = await fetch(`${SPRING_BASE_URL}/api/avatars`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create avatar');
  return response.json();
};

export const updateAvatar = async (id: string, data: Partial<UserAvatar>): Promise<UserAvatar> => {
  const headers = await getAuthHeader();
  const response = await fetch(`${SPRING_BASE_URL}/api/avatars/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to update avatar');
  return response.json();
};

export const deleteAvatar = async (id: string): Promise<void> => {
  const headers = await getAuthHeader();
  const response = await fetch(`${SPRING_BASE_URL}/api/avatars/${id}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json', ...headers },
  });
  if (!response.ok) throw new Error('Failed to delete avatar');
};
