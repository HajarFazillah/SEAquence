import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView,
  TouchableOpacity, Animated,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Mic, MicOff, X, Volume2, VolumeX } from 'lucide-react-native';
import { Card, Icon } from '../components';

export default function RealtimeSessionScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const avatar = route.params?.avatar;

  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState('안녕하세요! 오늘 어떻게 지내세요?');
  const [duration, setDuration] = useState(0);
  
  const pulseAnim = new Animated.Value(1);

  useEffect(() => {
    const timer = setInterval(() => {
      setDuration((d) => d + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (isRecording) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.2,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isRecording]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleMicPress = () => {
    setIsRecording(!isRecording);
    if (!isRecording) {
      // Start recording - simulate transcript
      setTimeout(() => {
        setTranscript('오늘 날씨가 좋네요.');
      }, 2000);
    }
  };

  const handleEndSession = () => {
    navigation.navigate('Feedback', {
      avatar,
      duration: formatDuration(duration),
    });
  };

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerBtn} onPress={handleEndSession}>
          <X size={24} color="#E53935" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <View style={styles.timerBadge}>
            <View style={styles.timerDot} />
            <Text style={styles.timerText}>{formatDuration(duration)}</Text>
          </View>
        </View>
        <TouchableOpacity 
          style={styles.headerBtn}
          onPress={() => setIsMuted(!isMuted)}
        >
          {isMuted ? (
            <VolumeX size={24} color="#6C6C80" />
          ) : (
            <Volume2 size={24} color="#6C3BFF" />
          )}
        </TouchableOpacity>
      </View>

      <View style={styles.content}>
        {/* Avatar */}
        <View style={styles.avatarSection}>
          <View style={[styles.avatarCircle, { backgroundColor: avatar?.avatarBg || '#FFB6C1' }]}>
            <Icon name={avatar?.icon || 'user'} size={48} color="#FFFFFF" />
          </View>
          <Text style={styles.avatarName}>{avatar?.name_ko || '아바타'}</Text>
          <Text style={styles.avatarStatus}>
            {isRecording ? '듣고 있어요...' : '말씀하세요'}
          </Text>
        </View>

        {/* Response Bubble */}
        <Card variant="elevated" style={styles.responseBubble}>
          <Text style={styles.responseText}>{response}</Text>
        </Card>

        {/* Transcript */}
        {transcript && (
          <View style={styles.transcriptSection}>
            <Text style={styles.transcriptLabel}>내가 말한 것:</Text>
            <Text style={styles.transcriptText}>{transcript}</Text>
          </View>
        )}

        {/* Spacer */}
        <View style={{ flex: 1 }} />

        {/* Mic Button */}
        <View style={styles.micSection}>
          <Text style={styles.micHint}>
            {isRecording ? '말하고 있어요...' : '버튼을 눌러 말하세요'}
          </Text>
          <TouchableOpacity
            style={[styles.micButton, isRecording && styles.micButtonActive]}
            onPress={handleMicPress}
            activeOpacity={0.8}
          >
            <Animated.View style={{ transform: [{ scale: isRecording ? pulseAnim : 1 }] }}>
              {isRecording ? (
                <MicOff size={36} color="#FFFFFF" />
              ) : (
                <Mic size={36} color="#FFFFFF" />
              )}
            </Animated.View>
          </TouchableOpacity>
          <Text style={styles.micStatus}>
            {isRecording ? '탭하여 중지' : '탭하여 말하기'}
          </Text>
        </View>

        {/* End Button */}
        <TouchableOpacity style={styles.endButton} onPress={handleEndSession}>
          <Text style={styles.endButtonText}>세션 종료</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  headerBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerCenter: {
    alignItems: 'center',
  },
  timerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    gap: 8,
  },
  timerDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#E53935',
  },
  timerText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
  },

  content: {
    flex: 1,
    paddingHorizontal: 20,
  },

  // Avatar
  avatarSection: {
    alignItems: 'center',
    marginVertical: 24,
  },
  avatarCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  avatarName: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 4,
  },
  avatarStatus: {
    fontSize: 14,
    color: '#6C6C80',
  },

  // Response
  responseBubble: {
    backgroundColor: '#FFFFFF',
    marginBottom: 16,
  },
  responseText: {
    fontSize: 16,
    color: '#1A1A2E',
    lineHeight: 24,
    textAlign: 'center',
  },

  // Transcript
  transcriptSection: {
    backgroundColor: '#F0EDFF',
    borderRadius: 12,
    padding: 14,
  },
  transcriptLabel: {
    fontSize: 11,
    color: '#6C3BFF',
    fontWeight: '600',
    marginBottom: 4,
  },
  transcriptText: {
    fontSize: 14,
    color: '#1A1A2E',
  },

  // Mic
  micSection: {
    alignItems: 'center',
    marginBottom: 24,
  },
  micHint: {
    fontSize: 14,
    color: '#6C6C80',
    marginBottom: 16,
  },
  micButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#6C3BFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    shadowColor: '#6C3BFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  micButtonActive: {
    backgroundColor: '#E53935',
  },
  micStatus: {
    fontSize: 13,
    color: '#6C6C80',
  },

  // End Button
  endButton: {
    backgroundColor: '#FFEBEE',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 20,
  },
  endButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#E53935',
  },
});
