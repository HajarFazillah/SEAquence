import React, { useState } from 'react';
import { login, me } from '@react-native-kakao/user';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { GoogleSignin, statusCodes } from '@react-native-google-signin/google-signin';
import {
  View, Text, StyleSheet, SafeAreaView,
  TouchableOpacity, KeyboardAvoidingView, Platform,
  ScrollView, TextInput, Image, Alert
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { ChevronLeft } from 'lucide-react-native';
import { loginUser } from '../services/apiAuth';

GoogleSignin.configure({
  webClientId: '482478499619-38qm0qviq4nooj10ibke90lmndk1lo1v.apps.googleusercontent.com',
});

export const LoginScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async () => {
    if (!email || !password) return;
    try {
      await loginUser(email, password);
      navigation.navigate('Main');
    } catch (error: any) {
      Alert.alert('Login Failed', error.message);
    }
  };

  const handleSignUp = () => {
    navigation.navigate('SignUp');
  };

  const handleKakaoLogin = async () => {
    try {
      await login();
      const profile = await me();
      console.log('=== KAKAO PROFILE ===', JSON.stringify(profile));

      const response = await fetch('http://10.0.2.2:8080/auth/kakao', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          kakaoId: String(profile.id),
          email: profile.email ?? String(profile.id) + '@kakao.com',
          nickname: profile.nickname ?? 'Kakao User',
          profileImageUrl: profile.profileImageUrl ?? null,
        }),
      });

      const data = await response.json();
      console.log('=== BACKEND RESPONSE ===', JSON.stringify(data));

      await AsyncStorage.setItem('token', data.token);
      await AsyncStorage.setItem('userId', data.userId);

      navigation.navigate('Main');
    } catch (error: any) {
      console.log('Kakao login failed:', error.message);
      Alert.alert('Kakao Login Failed', error.message);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      await GoogleSignin.hasPlayServices();
      const userInfo = await GoogleSignin.signIn();
      console.log('=== GOOGLE PROFILE ===', JSON.stringify(userInfo));

      const response = await fetch('http://10.0.2.2:8080/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          googleId: userInfo.data?.user.id,
          email: userInfo.data?.user.email,
          nickname: userInfo.data?.user.name ?? 'Google User',
          profileImageUrl: userInfo.data?.user.photo ?? null,
        }),
      });

      const data = await response.json();
      console.log('=== BACKEND RESPONSE ===', JSON.stringify(data));

      await AsyncStorage.setItem('token', data.token);
      await AsyncStorage.setItem('userId', data.userId);

      navigation.navigate('Main');
    } catch (error: any) {
      console.log('Google login failed:', error.message);
      Alert.alert('Google Login Failed', error.message);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">

          <View style={styles.header}>
            <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
              <ChevronLeft size={24} color="#1A1A2E" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>로그인</Text>
            <View style={styles.backBtn} />
          </View>

          <Text style={styles.welcome}>Welcome to talkativ!</Text>

          <TouchableOpacity style={styles.kakaoButton} onPress={handleKakaoLogin}>
            <Image source={require('../assets/images/kakao_logo.png')} style={styles.kakaoLogo} />
            <Text style={styles.kakaoText}>CONTINUE WITH KAKAO</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.googleButton} onPress={handleGoogleLogin}>
            <View style={styles.googleIconContainer}>
              <Image source={require('../assets/images/google_logo.png')} style={styles.googleLogo} />
            </View>
            <Text style={styles.googleText}>CONTINUE WITH GOOGLE</Text>
          </TouchableOpacity>

          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>OR LOG IN WITH EMAIL</Text>
            <View style={styles.dividerLine} />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Email address</Text>
            <TextInput style={styles.input} value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" placeholderTextColor="#B0B0C5" />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Password</Text>
            <TextInput style={styles.input} value={password} onChangeText={setPassword} secureTextEntry placeholderTextColor="#B0B0C5" />
          </View>

          <TouchableOpacity style={[styles.loginButton, (!email || !password) && styles.loginButtonDisabled]} onPress={handleLogin}>
            <Text style={styles.loginButtonText}>LOG IN</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.forgotPassword}>
            <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
          </TouchableOpacity>

          <View style={styles.signUpRow}>
            <Text style={styles.signUpText}>NOT A MEMBER? </Text>
            <TouchableOpacity onPress={handleSignUp}>
              <Text style={styles.signUpLink}>SIGN UP</Text>
            </TouchableOpacity>
          </View>

        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },
  container: { flexGrow: 1, paddingHorizontal: 24, paddingBottom: 40 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 16 },
  backBtn: { width: 40 },
  headerTitle: { fontSize: 16, fontWeight: '600', color: '#1A1A2E' },
  welcome: { fontSize: 28, fontWeight: '700', color: '#1A1A2E', textAlign: 'center', marginTop: 20, marginBottom: 32 },
  kakaoButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#FEE500', borderRadius: 30, paddingVertical: 16, marginBottom: 12, position: 'relative' },
  kakaoLogo: { width: 24, height: 24, position: 'absolute', left: 16 },
  kakaoText: { fontSize: 14, fontWeight: '700', color: '#000000', letterSpacing: 0.5 },
  googleButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFFFFF', borderRadius: 30, paddingVertical: 16, marginBottom: 24, borderWidth: 1, borderColor: '#E2E2EC', position: 'relative' },
  googleText: { fontSize: 14, fontWeight: '600', color: '#1A1A2E', letterSpacing: 0.5 },
  googleLogo: { width: 24, height: 24, resizeMode: 'contain' },
  googleIconContainer: { width: 36, height: 36, borderRadius: 18, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center', position: 'absolute', left: 12 },
  divider: { flexDirection: 'row', alignItems: 'center', marginBottom: 24 },
  dividerLine: { flex: 1, height: 1, backgroundColor: '#E2E2EC' },
  dividerText: { paddingHorizontal: 16, fontSize: 11, fontWeight: '600', color: '#B0B0C5', letterSpacing: 0.5 },
  inputContainer: { marginBottom: 20 },
  inputLabel: { fontSize: 14, color: '#B0B0C5', marginBottom: 8 },
  input: { fontSize: 16, color: '#1A1A2E', borderBottomWidth: 1, borderBottomColor: '#E2E2EC', paddingVertical: 12 },
  loginButton: { backgroundColor: '#6C3BFF', borderRadius: 30, paddingVertical: 18, alignItems: 'center', marginTop: 12, marginBottom: 20 },
  loginButtonDisabled: { opacity: 0.6 },
  loginButtonText: { fontSize: 16, fontWeight: '700', color: '#FFFFFF', letterSpacing: 1 },
  forgotPassword: { alignItems: 'center', marginBottom: 16 },
  forgotPasswordText: { fontSize: 14, fontWeight: '600', color: '#1A1A2E' },
  signUpRow: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center' },
  signUpText: { fontSize: 12, color: '#B0B0C5', letterSpacing: 0.5 },
  signUpLink: { fontSize: 12, fontWeight: '600', color: '#6C3BFF', letterSpacing: 0.5 },
});

export default LoginScreen;
