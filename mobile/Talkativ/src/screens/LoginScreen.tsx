import React, { useState } from 'react';
import { login } from '@react-native-kakao/user';
import {
  View, Text, StyleSheet, SafeAreaView,
  TouchableOpacity, KeyboardAvoidingView, Platform,
  ScrollView, TextInput, Image, Alert
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { ChevronLeft, MessageSquare } from 'lucide-react-native';
import { loginUser } from '../services/apiAuth';

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
      const result = await login();
      console.log('Kakao login success:', result);
      navigation.navigate('Main');
    } catch (error: any) {
      console.log('Kakao login failed:', error);
      Alert.alert('Kakao Login Failed', error.message);
    }
};

  const handleGoogleLogin = () => {
    // TODO: Implement Google OAuth
    navigation.navigate('Main');
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={styles.container}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
              <ChevronLeft size={24} color="#1A1A2E" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>로그인</Text>
            <View style={styles.backBtn} />
          </View>

          {/* Welcome */}
          <Text style={styles.welcome}>Welcome to talkativ!</Text>

          <TouchableOpacity style={styles.kakaoButton} onPress={handleKakaoLogin}>
            <Image source={require('../assets/images/kakao_logo.png')} style={styles.kakaoLogo}/>
            <Text style={styles.kakaoText}>CONTINUE WITH KAKAO</Text>
            </TouchableOpacity>

          {/* Google Login */}
          <TouchableOpacity style={styles.googleButton} onPress={handleGoogleLogin}>
            <View style={styles.googleIconContainer}>
            <Image source={require('../assets/images/google_logo.png')} style={styles.googleLogo}/>
            </View>
            <Text style={styles.googleText}>CONTINUE WITH GOOGLE</Text>
          </TouchableOpacity>


          {/* Divider */}
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>OR LOG IN WITH EMAIL</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Email Input */}
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Email address</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder=""
              keyboardType="email-address"
              autoCapitalize="none"
              placeholderTextColor="#B0B0C5"
            />
          </View>

          {/* Password Input */}
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Password</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder=""
              secureTextEntry
              placeholderTextColor="#B0B0C5"
            />
          </View>

          {/* Login Button */}
          <TouchableOpacity
            style={[styles.loginButton, (!email || !password) && styles.loginButtonDisabled]}
            onPress={handleLogin}
          >
            <Text style={styles.loginButtonText}>LOG IN</Text>
          </TouchableOpacity>

          {/* Forgot Password */}
          <TouchableOpacity style={styles.forgotPassword}>
            <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
          </TouchableOpacity>

          {/* Sign Up */}
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
  container: {
    flexGrow: 1,
    paddingHorizontal: 24,
    paddingBottom: 40,
  },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
  },
  backBtn: { width: 40 },
  headerTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A2E',
  },

  // Welcome
  welcome: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1A1A2E',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 32,
  },

  // Kakao Button
  kakaoButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FEE500',
    borderRadius: 30,
    paddingVertical: 16,
    marginBottom: 12,
    position: 'relative',
  },
  kakaoLogo: {
    width: 24,
    height: 24,
    position: 'absolute',
    left: 16,
  },
  kakaoText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#000000',
    letterSpacing: 0.5,
  },

  // Google Button
  googleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 30,
    paddingVertical: 16,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#E2E2EC',
    position: 'relative',
  },
  googleIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
    left: 12,
    borderWidth: 1,
    borderColor: '#E2E2EC',
  },
  googleIconText: {
    fontSize: 20,
    fontWeight: '500',
    color: '#4285F4',
  },
  googleText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A2E',
    letterSpacing: 0.5,
  },
  googleLogo: {
    width: 24,
    height: 24,
    resizeMode: 'contain',
  },
  googleIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'absolute',
    left: 12,
  },


  // Divider
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#E2E2EC',
  },
  dividerText: {
    paddingHorizontal: 16,
    fontSize: 11,
    fontWeight: '600',
    color: '#B0B0C5',
    letterSpacing: 0.5,
  },

  // Input
  inputContainer: {
    marginBottom: 20,
  },
  inputLabel: {
    fontSize: 14,
    color: '#B0B0C5',
    marginBottom: 8,
  },
  input: {
    fontSize: 16,
    color: '#1A1A2E',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E2EC',
    paddingVertical: 12,
  },

  // Login Button
  loginButton: {
    backgroundColor: '#6C3BFF',
    borderRadius: 30,
    paddingVertical: 18,
    alignItems: 'center',
    marginTop: 12,
    marginBottom: 20,
  },
  loginButtonDisabled: {
    opacity: 0.6,
  },
  loginButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: 1,
  },

  // Forgot Password
  forgotPassword: {
    alignItems: 'center',
    marginBottom: 16,
  },
  forgotPasswordText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1A1A2E',
  },

  // Sign Up
  signUpRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  signUpText: {
    fontSize: 12,
    color: '#B0B0C5',
    letterSpacing: 0.5,
  },
  signUpLink: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C3BFF',
    letterSpacing: 0.5,
  },
});

export default LoginScreen;
