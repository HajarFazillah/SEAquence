// API service for Talkativ mobile app
// This module provides functions to handle user authentication and other API interactions with the backend server.

import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = 'http://10.0.2.2:8080'; // Android emulator
// const BASE_URL = 'http://localhost:8080'; // iOS simulator

export const kakaoLogin = async (accessToken: string) => {
  const response = await fetch(`${BASE_URL}/auth/kakao`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ accessToken }),
  });

  if (!response.ok) throw new Error('Kakao login failed');

  const data = await response.json();
  await AsyncStorage.setItem('auth_token', data.token);
  return data;
};

export const logout = async () => {
  await AsyncStorage.removeItem('auth_token');
};
