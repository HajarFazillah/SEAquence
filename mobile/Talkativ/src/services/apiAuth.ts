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
  await AsyncStorage.setItem('token', data.token);
  await AsyncStorage.setItem('userId', String(data.userId));
  return data;
};

// Auth: Register
export const registerUser = async (username: string, email: string, password: string) => {
  const response = await fetch(`${SPRING_BASE_URL}/api/users/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username,
      email,
      password,
      nativeLang: 'en',   // ← default for now
      targetLang: 'ko',   // ← always Korean
    }),
  });
  if (!response.ok) throw new Error('Registration failed. Email may already be in use.');
  return response.json();
};

// Helper: get token for protected requests
export const getAuthHeader = async () => {
  const token = await AsyncStorage.getItem('token');
  return { Authorization: `Bearer ${token}` };
};

// Auth: Logout
export const logoutUser = async () => {
  await AsyncStorage.removeItem('token');
  await AsyncStorage.removeItem('userId');
};
