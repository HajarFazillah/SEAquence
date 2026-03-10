// mobile/Talkativ/src/screens/LoginScreen.tsx
import React from 'react';
import { useNavigation } from '@react-navigation/native';
import { View, Text, StyleSheet, TouchableOpacity, TextInput, SafeAreaView, ScrollView } from 'react-native';

export const LoginScreen: React.FC = () => {
  const navigation = useNavigation();

  const handleKakao = () => {
    // TODO: later → call stub /auth/kakao, then real backend
    console.log('Kakao login pressed');
  };

  const handleGoogle = () => {
    console.log('Google login pressed');
  };

  const handleEmailLogin = () => {
    navigation.navigate('Main' as never);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        {/* Top bar */}
        <View style={styles.topBar}>
          <Text style={styles.topTitle}>로그인</Text>
        </View>

        {/* Welcome text */}
        <Text style={styles.welcome}>Welcome to talkativ!</Text>

        {/* Kakao button */}
        <TouchableOpacity style={styles.kakaoButton} onPress={handleKakao}>
          <Text style={styles.kakaoText}>CONTINUE WITH KAKAO</Text>
        </TouchableOpacity>

        {/* Google button */}
        <TouchableOpacity style={styles.googleButton} onPress={handleGoogle}>
          <Text style={styles.googleText}>CONTINUE WITH GOOGLE</Text>
        </TouchableOpacity>

        {/* Divider text */}
        <Text style={styles.dividerText}>OR LOG IN WITH EMAIL</Text>

        {/* Email + password */}
        <TextInput
          style={styles.input}
          placeholder="Email address"
          placeholderTextColor="#C8C8D3"
          keyboardType="email-address"
        />
        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#C8C8D3"
          secureTextEntry
        />

        {/* Login button */}
        <TouchableOpacity style={styles.loginButton} onPress={handleEmailLogin}>
          <Text style={styles.loginText}>LOG IN</Text>
        </TouchableOpacity>

        {/* Footer text */}
        <Text style={styles.forgot}>Forgot Password?</Text>
        <Text style={styles.signup}>
          NOT A MEMBER? <Text style={styles.signupLink}>SIGN UP</Text>
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    paddingHorizontal: 24,
    paddingTop: 32,
    paddingBottom: 24,
  },
  topBar: {
    alignItems: 'center',
    marginBottom: 24,
  },
  topTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  welcome: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 24,
  },
  kakaoButton: {
    backgroundColor: '#FEE500',
    borderRadius: 32,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 12,
  },
  kakaoText: {
    fontWeight: '600',
  },
  googleButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 32,
    paddingVertical: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E2E2EC',
    marginBottom: 24,
  },
  googleText: {
    fontWeight: '600',
  },
  dividerText: {
    textAlign: 'center',
    color: '#B0B0C5',
    fontSize: 12,
    marginBottom: 16,
  },
  input: {
    backgroundColor: '#F5F5FA',
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 12,
  },
  loginButton: {
    backgroundColor: '#6C3BFF',
    borderRadius: 32,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
    marginBottom: 16,
  },
  loginText: {
    color: '#FFFFFF',
    fontWeight: '600',
    letterSpacing: 1,
  },
  forgot: {
    textAlign: 'center',
    color: '#6C6C80',
    marginBottom: 8,
  },
  signup: {
    textAlign: 'center',
    color: '#B0B0C5',
  },
  signupLink: {
    color: '#6C3BFF',
    fontWeight: '600',
  },
});
