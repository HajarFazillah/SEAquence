import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  TouchableOpacity, KeyboardAvoidingView, Platform,
  ScrollView, Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { ChevronLeft } from 'lucide-react-native';
import { InputField, Button } from '../components';

export default function SignUpScreen() {
  const navigation = useNavigation<any>();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const isValid = email.trim().length > 0 
    && password.length >= 6 
    && password === confirmPassword;

  const handleNext = () => {
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match.');
      return;
    }
    // Pass email + password to Step 1
    navigation.navigate('CreateProfileStep1', { email, password });
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity style={styles.backBtn} onPress={() => navigation.goBack()}>
              <ChevronLeft size={24} color="#1A1A2E" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>회원가입</Text>
            <View style={styles.backBtn} />
          </View>

          <Text style={styles.title}>계정을 만들어주세요</Text>
          <Text style={styles.subtitle}>로그인에 사용할 이메일과 비밀번호를 입력하세요</Text>

          <InputField
            label="Email address"
            value={email}
            onChangeText={setEmail}
            placeholder="example@email.com"
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <InputField
            label="Password (6자 이상)"
            value={password}
            onChangeText={setPassword}
            placeholder=""
            secureTextEntry
          />

          <InputField
            label="Confirm Password"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            placeholder=""
            secureTextEntry
          />

          <View style={styles.footer}>
            <Button
              title="다음"
              onPress={handleNext}
              disabled={!isValid}
              showArrow
            />
          </View>
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
  title: { fontSize: 26, fontWeight: '700', color: '#1A1A2E', marginTop: 20, marginBottom: 8 },
  subtitle: { fontSize: 14, color: '#6C6C80', marginBottom: 32, lineHeight: 20 },
  footer: { marginTop: 24 },
});