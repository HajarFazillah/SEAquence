import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  ScrollView, TouchableOpacity,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Mic, MicOff, Volume2, Info, ChevronRight } from 'lucide-react-native';
import { Header, Card, Button, StatusBadge, Icon } from '../components';
import { SYSTEM_AVATARS } from '../constants';

export default function RealtimeScreen() {
  const navigation = useNavigation<any>();
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>(null);

  const handleStartSession = () => {
    if (!selectedAvatar) return;
    const avatar = SYSTEM_AVATARS.find((a) => a.id === selectedAvatar);
    navigation.navigate('RealtimeSession', { avatar });
  };

  return (
    <SafeAreaView style={styles.safe}>
      <Header title="실시간 대화" showBack={false} showBell />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Info Banner */}
        <Card variant="elevated" style={styles.infoBanner}>
          <View style={styles.infoRow}>
            <View style={styles.infoIcon}>
              <Mic size={24} color="#6C3BFF" />
            </View>
            <View style={styles.infoText}>
              <Text style={styles.infoTitle}>음성 인식 대화</Text>
              <Text style={styles.infoSubtitle}>
                마이크로 말하면 AI가 실시간으로 대화해요
              </Text>
            </View>
          </View>
        </Card>

        {/* How it works */}
        <Text style={styles.sectionTitle}>이용 방법</Text>
        <View style={styles.stepsContainer}>
          <View style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>1</Text>
            </View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>아바타 선택</Text>
              <Text style={styles.stepDesc}>대화할 아바타를 선택하세요</Text>
            </View>
          </View>
          <View style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>2</Text>
            </View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>마이크 허용</Text>
              <Text style={styles.stepDesc}>음성 인식을 위해 마이크를 허용하세요</Text>
            </View>
          </View>
          <View style={styles.step}>
            <View style={styles.stepNumber}>
              <Text style={styles.stepNumberText}>3</Text>
            </View>
            <View style={styles.stepContent}>
              <Text style={styles.stepTitle}>대화 시작</Text>
              <Text style={styles.stepDesc}>버튼을 누르고 말하세요</Text>
            </View>
          </View>
        </View>

        {/* Avatar Selection */}
        <Text style={styles.sectionTitle}>아바타 선택</Text>
        <View style={styles.avatarList}>
          {SYSTEM_AVATARS.map((avatar) => (
            <Card
              key={avatar.id}
              variant={selectedAvatar === avatar.id ? 'outlined' : 'elevated'}
              style={[
                styles.avatarCard,
                selectedAvatar === avatar.id && styles.avatarCardSelected,
              ]}
              onPress={() => setSelectedAvatar(avatar.id)}
            >
              <View style={styles.avatarRow}>
                <View style={[styles.avatarIcon, { backgroundColor: avatar.avatarBg }]}>
                  <Icon name={avatar.icon} size={24} color="#FFFFFF" />
                </View>
                <View style={styles.avatarInfo}>
                  <Text style={styles.avatarName}>{avatar.name_ko}</Text>
                  <Text style={styles.avatarRole}>{avatar.description_ko}</Text>
                </View>
                <StatusBadge status={avatar.difficulty as 'easy' | 'medium' | 'hard'} />
              </View>
            </Card>
          ))}
        </View>

      </ScrollView>

      {/* Start Button */}
      <View style={styles.footer}>
        <Button
          title="세션 시작하기"
          onPress={handleStartSession}
          showArrow
          disabled={!selectedAvatar}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  // Info Banner
  infoBanner: {
    backgroundColor: '#F0EDFF',
    marginBottom: 24,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  infoIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoText: {
    flex: 1,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 2,
  },
  infoSubtitle: {
    fontSize: 13,
    color: '#6C6C80',
  },

  // Section
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 14,
  },

  // Steps
  stepsContainer: {
    marginBottom: 24,
  },
  step: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  stepNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#6C3BFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  stepNumberText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1A1A2E',
    marginBottom: 2,
  },
  stepDesc: {
    fontSize: 13,
    color: '#6C6C80',
  },

  // Avatar List
  avatarList: {
    gap: 12,
  },
  avatarCard: {},
  avatarCardSelected: {
    borderColor: '#6C3BFF',
    borderWidth: 2,
  },
  avatarRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInfo: {
    flex: 1,
  },
  avatarName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A2E',
    marginBottom: 2,
  },
  avatarRole: {
    fontSize: 12,
    color: '#6C6C80',
  },

  // Footer
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});
