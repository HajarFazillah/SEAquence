import AsyncStorage from '@react-native-async-storage/async-storage';
import { SPRING_API_BASE_URL } from '../constants';

const SPRING_BASE_URL = SPRING_API_BASE_URL;

// Auth: Login
export const loginUser = async (email: string, password: string) => {
  const response = await fetch(`${SPRING_BASE_URL}/api/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) throw new Error('Invalid email or password.');
  const data = await response.json();
  // LoginResponse shape: { token: string, user: { userId: string, ... } }
  const userId = data.user?.userId ?? data.userId ?? '';
  await AsyncStorage.setItem('token', data.token);
  await AsyncStorage.setItem('userId', userId);
  await AsyncStorage.setItem('user_id', userId);
  return data;
};

type RegistrationProfile = {
  username: string;
  email: string;
  password: string;
  age: string;
  gender: string;
  koreanLevel: string;
  memo: string;
  interests: string[];
  dislikes: string[];
};

const getErrorMessage = async (response: Response, fallback: string) => {
  const data = await response.json().catch(() => null);
  return data?.message || data?.error || fallback;
};

// Auth: Register
export const registerUser = async (profile: RegistrationProfile) => {
  const response = await fetch(`${SPRING_BASE_URL}/api/users/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...profile,
      nativeLang: 'en',   // ← default for now
      targetLang: 'ko',   // ← always Korean
    }),
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response, 'Registration failed. Please try again.'));
  }
  return response.json();
};

// Helper: get token for protected requests
export const getAuthHeader = async () => {
  const token = await AsyncStorage.getItem('token');
  return { Authorization: `Bearer ${token}` };
};

// Auth: Forgot Password — sends OTP to email
export const forgotPassword = async (email: string) => {
  const response = await fetch(`${SPRING_BASE_URL}/api/users/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.message ?? 'Failed to send reset code.');
  }
};

// Auth: Reset Password — confirms OTP and sets new password
export const resetPassword = async (email: string, code: string, newPassword: string) => {
  const response = await fetch(`${SPRING_BASE_URL}/api/users/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code, newPassword }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.message ?? 'Failed to reset password.');
  }
};

// Auth: Logout
export const logoutUser = async () => {
  await AsyncStorage.multiRemove(['token', 'userId', 'user_id']);
};
