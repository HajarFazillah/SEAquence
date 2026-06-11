import React, { useState } from 'react';
import {
  View, Text, StyleSheet,
  TouchableOpacity, KeyboardAvoidingView, Platform,
  ScrollView, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { ChevronLeft, Mail, KeyRound } from 'lucide-react-native';
import { InputField, Button } from '../components';
import { forgotPassword, resetPassword } from '../services/apiAuth';

type Step = 'email' | 'reset';

export default function ForgotPasswordScreen() {
  const navigation = useNavigation<any>();

  const [step, setStep] = useState<Step>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleBack = () => {
    if (step === 'reset') {
      setStep('email');
    } else {
      navigation.goBack();
    }
  };

  const handleSendCode = async () => {
    if (!email.trim()) return;
    setIsLoading(true);
    try {
      await forgotPassword(email.trim());
      setStep('reset');
    } catch (error: any) {
      Alert.alert('오류', error.message ?? '인증 코드 전송에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (newPassword !== confirmPassword) {
      Alert.alert('오류', '비밀번호가 일치하지 않습니다.');
      return;
    }
    if (newPassword.length < 6) {
      Alert.alert('오류', '비밀번호는 6자 이상이어야 합니다.');
      return;
    }
    setIsLoading(true);
    try {
      await resetPassword(email.trim(), code.trim(), newPassword);
      Alert.alert('완료', '비밀번호가 재설정되었습니다. 새 비밀번호로 로그인해주세요.', [
        { text: '로그인', onPress: () => navigation.navigate('Login') },
      ]);
    } catch (error: any) {
      Alert.alert('오류', error.message ?? '비밀번호 재설정에 실패했습니다. 코드를 확인하고 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const emailValid = email.trim().length > 0 && email.includes('@');
  const resetValid = code.trim().length > 0 && newPassword.length >= 6 && newPassword === confirmPassword;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity style={styles.backBtn} onPress={handleBack}>
              <ChevronLeft size={24} color="#1A1A2E" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>비밀번호 찾기</Text>
            <View style={styles.backBtn} />
          </View>

          {/* Icon */}
          <View style={styles.iconWrap}>
            <View style={styles.iconCircle}>
              {step === 'email'
                ? <Mail size={32} color="#6C3BFF" />
                : <KeyRound size={32} color="#6C3BFF" />}
            </View>
          </View>

          {step === 'email' ? (
            <>
              <Text style={styles.title}>이메일을 입력해주세요</Text>
              <Text style={styles.subtitle}>
                가입하신 이메일로 비밀번호 재설정 코드를 보내드립니다
              </Text>

              <InputField
                label="이메일 주소"
                value={email}
                onChangeText={setEmail}
                placeholder="example@email.com"
                keyboardType="email-address"
                autoCapitalize="none"
              />

              <View style={styles.footer}>
                <Button
                  title={isLoading ? '전송 중...' : '인증 코드 전송'}
                  onPress={handleSendCode}
                  disabled={!emailValid || isLoading}
                  showArrow={!isLoading}
                />
              </View>
            </>
          ) : (
            <>
              <Text style={styles.title}>새 비밀번호 설정</Text>
              <Text style={styles.subtitle}>
                <Text style={styles.emailHighlight}>{email}</Text>
                {'\n'}로 전송된 코드를 입력하고 새 비밀번호를 설정하세요
              </Text>

              <InputField
                label="인증 코드"
                value={code}
                onChangeText={setCode}
                placeholder="인증 코드 6자리"
                keyboardType="numeric"
                autoCapitalize="none"
              />

              <InputField
                label="새 비밀번호 (6자 이상)"
                value={newPassword}
                onChangeText={setNewPassword}
                placeholder=""
                secureTextEntry
              />

              <InputField
                label="비밀번호 확인"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                placeholder=""
                secureTextEntry
                error={confirmPassword.length > 0 && newPassword !== confirmPassword ? '비밀번호가 일치하지 않습니다' : undefined}
              />

              <TouchableOpacity style={styles.resendRow} onPress={handleSendCode} disabled={isLoading}>
                <Text style={styles.resendText}>코드를 받지 못하셨나요? </Text>
                <Text style={styles.resendLink}>재전송</Text>
              </TouchableOpacity>

              <View style={styles.footer}>
                <Button
                  title={isLoading ? '처리 중...' : '비밀번호 재설정'}
                  onPress={handleResetPassword}
                  disabled={!resetValid || isLoading}
                  showArrow={!isLoading}
                />
              </View>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },
  container: { flexGrow: 1, paddingHorizontal: 24, paddingBottom: 40 },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
  },
  backBtn: { width: 40 },
  headerTitle: { fontSize: 16, fontWeight: '600', color: '#1A1A2E' },

  iconWrap: { alignItems: 'center', marginTop: 24, marginBottom: 24 },
  iconCircle: {
    width: 72, height: 72, borderRadius: 36,
    backgroundColor: '#F0EDFF',
    alignItems: 'center', justifyContent: 'center',
  },

  title: { fontSize: 26, fontWeight: '700', color: '#1A1A2E', marginBottom: 8 },
  subtitle: { fontSize: 14, color: '#6C6C80', marginBottom: 32, lineHeight: 22 },
  emailHighlight: { fontWeight: '600', color: '#6C3BFF' },

  resendRow: { flexDirection: 'row', justifyContent: 'center', marginTop: 8, marginBottom: 4 },
  resendText: { fontSize: 13, color: '#6C6C80' },
  resendLink: { fontSize: 13, fontWeight: '600', color: '#6C3BFF' },

  footer: { marginTop: 24 },
});
