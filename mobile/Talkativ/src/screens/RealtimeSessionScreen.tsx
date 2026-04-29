import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Alert,
  ScrollView,
  PermissionsAndroid,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import {
  useNavigation,
  useRoute,
  useFocusEffect,
} from '@react-navigation/native';
import {
  Mic,
  MicOff,
  X,
  Volume2,
  VolumeX,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react-native';
import { Icon } from '../components';
import { endSession } from '../services/apiSession';
import {
  analyzeRealtimeAudio,
  TranscriptTurnResult,
  InsightResult,
} from '../services/realtimeAnalysisService';
import Sound, { RecordBackType } from 'react-native-nitro-sound';
import type { RootStackParamList } from '../navigation/AppNavigator';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type RealtimeSessionRoute = NativeStackScreenProps<
  RootStackParamList,
  'RealtimeSession'
>['route'];

type TranscriptTurn = {
  id: string;
  speaker: string;
  text: string;
  type: 'partial' | 'final';
};

type Insight = {
  id: string;
  kind: 'risk' | 'success';
  message: string;
  suggestion?: string;
  turnId: string;
};

const formatDuration = (seconds: number) => {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

function SessionBanner({
  speakerCount,
  situation,
}: {
  speakerCount: number;
  situation?: string;
}) {
  return (
    <View style={banner.container}>
      <View style={banner.pill}>
        <View style={banner.dot} />
        <Text style={banner.text}>실시간 분석 중</Text>
      </View>
      <Text style={banner.meta}>
        {speakerCount}명 참여 중 · {situation ?? '일상 대화'}
      </Text>
    </View>
  );
}

function InsightCard({ insight }: { insight: Insight }) {
  const isRisk = insight.kind === 'risk';

  return (
    <View
      style={[
        insightStyle.card,
        isRisk ? insightStyle.cardRisk : insightStyle.cardSuccess,
      ]}
    >
      <View style={insightStyle.row}>
        {isRisk ? (
          <AlertTriangle size={16} color="#B45309" />
        ) : (
          <CheckCircle size={16} color="#166534" />
        )}
        <Text
          style={[
            insightStyle.title,
            isRisk ? insightStyle.titleRisk : insightStyle.titleSuccess,
          ]}
        >
          {insight.message}
        </Text>
      </View>

      {insight.suggestion ? (
        <View style={insightStyle.suggestionBox}>
          <Text style={insightStyle.suggestionLabel}>추천 표현</Text>
          <Text
            style={[
              insightStyle.suggestionText,
              isRisk ? insightStyle.suggestionRisk : insightStyle.suggestionGreen,
            ]}
          >
            "{insight.suggestion}"
          </Text>
        </View>
      ) : null}
    </View>
  );
}

function TranscriptTurnRow({
  turn,
  insight,
}: {
  turn: TranscriptTurn;
  insight?: Insight;
}) {
  const isPartial = turn.type === 'partial';

  return (
    <View style={turnStyle.wrapper}>
      <Text style={turnStyle.speaker}>{turn.speaker}</Text>
      <View style={[turnStyle.bubble, isPartial && turnStyle.bubblePartial]}>
        <Text style={[turnStyle.text, isPartial && turnStyle.textPartial]}>
          {turn.text}
          {isPartial ? ' ▌' : ''}
        </Text>
      </View>
      {insight ? <InsightCard insight={insight} /> : null}
    </View>
  );
}

function WaveformIndicator({ isActive }: { isActive: boolean }) {
  const bars = [0.4, 0.7, 1.0, 0.7, 0.5, 0.9, 0.6, 0.4, 0.8, 0.5];
  const anims = useRef(bars.map(() => new Animated.Value(0.3))).current;

  useEffect(() => {
    if (!isActive) {
      anims.forEach((a) => a.setValue(0.3));
      return;
    }

    const loops = anims.map((anim, i) =>
      Animated.loop(
        Animated.sequence([
          Animated.timing(anim, {
            toValue: bars[i],
            duration: 300 + i * 60,
            useNativeDriver: true,
          }),
          Animated.timing(anim, {
            toValue: 0.3,
            duration: 300 + i * 60,
            useNativeDriver: true,
          }),
        ])
      )
    );

    loops.forEach((l) => l.start());
    return () => loops.forEach((l) => l.stop());
  }, [isActive, anims]);

  return (
    <View style={wave.container}>
      {anims.map((anim, i) => (
        <Animated.View
          key={i}
          style={[
            wave.bar,
            {
              transform: [{ scaleY: anim }],
              backgroundColor: isActive ? '#6C3BFF' : '#D1C4E9',
            },
          ]}
        />
      ))}
    </View>
  );
}

const normalizeTranscriptTurns = (
  turns: TranscriptTurnResult[] = []
): TranscriptTurn[] => {
  return turns.map((turn, index) => ({
    id: turn.id ?? `turn-${Date.now()}-${index}`,
    speaker: String(turn.speaker ?? 'Speaker'),
    text: turn.text ?? '',
    type: 'final',
  }));
};

const normalizeInsights = (insights: InsightResult[] = []): Insight[] => {
  return insights.map((insight, index) => ({
    id: insight.id ?? `insight-${Date.now()}-${index}`,
    kind: insight.kind === 'risk' ? 'risk' : 'success',
    message: insight.message ?? '',
    suggestion: insight.suggestion,
    turnId:
      ((insight as unknown as { turnId?: string }).turnId ??
        (insight as unknown as { turn_id?: string }).turn_id ??
        '') as string,
  }));
};

export default function RealtimeSessionScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<RealtimeSessionRoute>();
  const avatar = route.params?.avatar;
  const sessionId = route.params?.sessionId as string | undefined;
  const situation = route.params?.situation as string | undefined;

  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [duration, setDuration] = useState(0);
  const [isEnding, setIsEnding] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [turns, setTurns] = useState<TranscriptTurn[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [recordingUri, setRecordingUri] = useState<string>('');

  const pulseAnim = useRef(new Animated.Value(1)).current;
  const pulseLoop = useRef<Animated.CompositeAnimation | null>(null);
  const sessionEnded = useRef(false);
  const scrollRef = useRef<ScrollView>(null);

  useEffect(() => {
    const t = setInterval(() => setDuration((d) => d + 1), 1000);

    return () => {
      clearInterval(t);
      Sound.removeRecordBackListener();
      Sound.stopRecorder().catch(() => {});
    };
  }, []);

  useEffect(() => {
    if (isRecording) {
      pulseLoop.current = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      );
      pulseLoop.current.start();
    } else {
      pulseLoop.current?.stop();
      pulseAnim.setValue(1);
    }
  }, [isRecording, pulseAnim]);

  useEffect(() => {
    const timer = setTimeout(() => {
      scrollRef.current?.scrollToEnd({ animated: true });
    }, 120);

    return () => clearTimeout(timer);
  }, [turns]);

  useFocusEffect(
    useCallback(() => {
      const unsub = navigation.addListener('beforeRemove', (e: any) => {
        if (sessionEnded.current || isEnding) return;
        e.preventDefault();
        Alert.alert('세션 종료', '세션을 종료하시겠습니까?', [
          { text: '취소', style: 'cancel' },
          {
            text: '종료',
            style: 'destructive',
            onPress: () => finishSession(false),
          },
        ]);
      });
      return unsub;
    }, [navigation, isEnding])
  );

  async function requestMicPermission(): Promise<boolean> {
    if (Platform.OS !== 'android') return true;

    const granted = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
      {
        title: '마이크 권한',
        message: 'Talkativ이 대화를 녹음하려면 마이크 접근이 필요합니다.',
        buttonPositive: '허용',
        buttonNegative: '거부',
      }
    );

    if (granted !== PermissionsAndroid.RESULTS.GRANTED) {
      Alert.alert('권한 필요', '설정에서 마이크 접근을 허용해주세요.');
      return false;
    }

    return true;
  }

  const finishSession = async (goToFeedback: boolean) => {
    if (sessionEnded.current) return;
    sessionEnded.current = true;
    setIsEnding(true);

    try {
      if (isRecording) {
        setIsRecording(false);
        Sound.removeRecordBackListener();
        await Sound.stopRecorder();
      }
    } catch {}

    try {
      if (sessionId) await endSession(sessionId);
    } catch {}

    if (goToFeedback) {
      navigation.navigate('Feedback', {
        avatar,
        sessionId,
        situation,
        duration: formatDuration(duration),
        recordingUri,
        turns,
        insights,
      });
    } else {
      navigation.goBack();
    }
  };

  const handleMicPress = async () => {
    if (isEnding || isAnalyzing) return;

    try {
      if (isRecording) {
        setIsRecording(false);
        setIsAnalyzing(true);
        setTurns((prev) => prev.filter((t) => t.type !== 'partial'));

        Sound.removeRecordBackListener();
        const uri = await Sound.stopRecorder();

        if (!uri) {
          throw new Error('녹음 파일 경로를 가져오지 못했습니다.');
        }

        setRecordingUri(uri);

        const formData = new FormData();
        formData.append(
          'file',
          {
            uri,
            name: 'recording.m4a',
            type: 'audio/x-m4a',
          } as any
        );

        const result = await analyzeRealtimeAudio(formData);

        const normalizedTurns = normalizeTranscriptTurns(result?.turns ?? []);
        const normalizedInsights = normalizeInsights(result?.insights ?? []);

        setTurns((prev) => [...prev, ...normalizedTurns]);
        setInsights((prev) => [...prev, ...normalizedInsights]);
      } else {
        const granted = await requestMicPermission();
        if (!granted) return;

        setTurns([]);
        setInsights([]);
        setRecordingUri('');

        await Sound.startRecorder();

        Sound.addRecordBackListener((_e: RecordBackType) => {
        });

        setIsRecording(true);

        setTurns([
          {
            id: `partial-${Date.now()}`,
            speaker: '듣는 중...',
            text: '음성을 인식하고 있습니다',
            type: 'partial',
          },
        ]);
      }
    } catch (error: any) {
      console.error('handleMicPress error:', error);
      setIsRecording(false);
      Sound.removeRecordBackListener();
      Sound.stopRecorder().catch(() => {});
      setTurns((prev) => prev.filter((t) => t.type !== 'partial'));

      Alert.alert(
        '오류',
        error?.response?.data?.message ??
          error?.message ??
          '녹음 또는 분석 중 문제가 발생했습니다.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  const speakerCount =
    new Set(turns.filter((t) => t.type === 'final').map((t) => t.speaker)).size ||
    1;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.headerBtn}
          onPress={() => finishSession(false)}
          disabled={isEnding}
        >
          <X size={22} color="#E53935" />
        </TouchableOpacity>

        <View style={styles.timerBadge}>
          <View style={styles.timerDot} />
          <Text style={styles.timerText}>{formatDuration(duration)}</Text>
        </View>

        <TouchableOpacity
          style={styles.headerBtn}
          onPress={() => setIsMuted((m) => !m)}
        >
          {isMuted ? (
            <VolumeX size={22} color="#9E9E9E" />
          ) : (
            <Volume2 size={22} color="#6C3BFF" />
          )}
        </TouchableOpacity>
      </View>

      <SessionBanner speakerCount={speakerCount} situation={situation} />

      <ScrollView
        ref={scrollRef}
        style={styles.transcript}
        contentContainerStyle={styles.transcriptContent}
        showsVerticalScrollIndicator={false}
      >
        {turns.length === 0 ? (
          <View style={styles.emptyState}>
            <Mic size={36} color="#D1C4E9" />
            <Text style={styles.emptyTitle}>
              {isAnalyzing ? '분석 결과를 불러오는 중...' : '대화를 시작해보세요'}
            </Text>
            <Text style={styles.emptySubtitle}>
              {isAnalyzing
                ? '잠시만 기다리면 transcript와 분석이 표시돼요'
                : '말을 시작하면 실시간 분석이\n여기에 표시돼요'}
            </Text>
          </View>
        ) : (
          turns.map((turn) => (
            <TranscriptTurnRow
              key={turn.id}
              turn={turn}
              insight={insights.find((i) => i.turnId === turn.id)}
            />
          ))
        )}
      </ScrollView>

      <View style={styles.controls}>
        <WaveformIndicator isActive={isRecording} />

        <View style={styles.micRow}>
          <View
            style={[
              styles.avatarChip,
              { backgroundColor: avatar?.avatar_bg ?? '#EDE7F6' },
            ]}
          >
            <Icon name={avatar?.icon ?? 'user'} size={18} color="#FFFFFF" />
          </View>

          <TouchableOpacity
            style={[styles.micButton, isRecording && styles.micButtonActive]}
            onPress={handleMicPress}
            activeOpacity={0.85}
            disabled={isEnding || isAnalyzing}
          >
            <Animated.View
              style={{ transform: [{ scale: isRecording ? pulseAnim : 1 }] }}
            >
              {isAnalyzing ? (
                <Mic size={30} color="rgba(255,255,255,0.45)" />
              ) : isRecording ? (
                <MicOff size={30} color="#FFFFFF" />
              ) : (
                <Mic size={30} color="#FFFFFF" />
              )}
            </Animated.View>
          </TouchableOpacity>

          <View style={styles.avatarChip} />
        </View>

        <Text style={styles.micHint}>
          {isAnalyzing
            ? '분석 중입니다...'
            : isRecording
              ? '듣고 있어요 · 탭하여 중지 및 분석'
              : '탭하여 녹음 시작'}
        </Text>

        <TouchableOpacity
          style={[styles.endButton, isEnding && styles.endButtonDisabled]}
          onPress={() => finishSession(true)}
          disabled={isEnding || isRecording || isAnalyzing}
        >
          <Text style={styles.endButtonText}>
            {isEnding ? '종료 중...' : '세션 종료 및 피드백 보기'}
          </Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  headerBtn: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timerBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  timerDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#E53935',
  },
  timerText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1A1A2E',
  },

  transcript: {
    flex: 1,
    paddingHorizontal: 16,
  },
  transcriptContent: {
    paddingTop: 8,
    paddingBottom: 16,
    gap: 4,
  },

  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 60,
    gap: 12,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#9E9E9E',
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 13,
    color: '#BDBDBD',
    textAlign: 'center',
    lineHeight: 20,
  },

  controls: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 24,
    borderTopWidth: 1,
    borderTopColor: '#F0F0F5',
    gap: 12,
  },
  micRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  avatarChip: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  micButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#6C3BFF',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#6C3BFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 10,
    elevation: 8,
  },
  micButtonActive: {
    backgroundColor: '#E53935',
  },
  micHint: {
    textAlign: 'center',
    fontSize: 13,
    color: '#9E9E9E',
  },

  endButton: {
    backgroundColor: '#FFF0F0',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  endButtonDisabled: {
    backgroundColor: '#F5F5F5',
  },
  endButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#E53935',
  },
});

const banner = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F5',
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#EDE7F6',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#6C3BFF',
  },
  text: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C3BFF',
  },
  meta: {
    fontSize: 12,
    color: '#9E9E9E',
  },
});

const turnStyle = StyleSheet.create({
  wrapper: {
    marginBottom: 12,
  },
  speaker: {
    fontSize: 11,
    fontWeight: '700',
    color: '#9E9E9E',
    marginBottom: 4,
    letterSpacing: 0.5,
  },
  bubble: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 1,
  },
  bubblePartial: {
    backgroundColor: '#F7F7FB',
    borderWidth: 1,
    borderColor: '#E8E8F0',
  },
  text: {
    fontSize: 15,
    color: '#1A1A2E',
    lineHeight: 22,
  },
  textPartial: {
    color: '#9E9E9E',
  },
});

const insightStyle = StyleSheet.create({
  card: {
    borderRadius: 10,
    padding: 12,
    marginTop: 6,
  },
  cardRisk: {
    backgroundColor: '#FFFBEB',
  },
  cardSuccess: {
    backgroundColor: '#F0FDF4',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  title: {
    fontSize: 13,
    fontWeight: '600',
    flex: 1,
  },
  titleRisk: {
    color: '#92400E',
  },
  titleSuccess: {
    color: '#166534',
  },
  suggestionBox: {
    backgroundColor: 'rgba(0,0,0,0.04)',
    borderRadius: 8,
    padding: 8,
    marginTop: 4,
  },
  suggestionLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#9E9E9E',
    marginBottom: 2,
  },
  suggestionText: {
    fontSize: 13,
    fontWeight: '600',
    lineHeight: 20,
  },
  suggestionRisk: {
    color: '#B45309',
  },
  suggestionGreen: {
    color: '#166534',
  },
});

const wave = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 24,
    gap: 3,
  },
  bar: {
    width: 3,
    height: 16,
    borderRadius: 2,
  },
});