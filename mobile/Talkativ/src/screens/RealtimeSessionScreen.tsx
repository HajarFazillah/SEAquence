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
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, useFocusEffect } from '@react-navigation/native';
import {
  Mic, MicOff,
  CircleDashed, ArrowRight, Star,
  Bookmark, BookmarkCheck, BookOpen, X as XIcon, Target, Lightbulb, ArrowLeft,
} from 'lucide-react-native';
import { Icon, type IconName } from '../components';
import { createSession, endSession } from '../services/apiSession';
import { makePreviewPayload, saveConversationPreview } from '../services/conversationPreview';
import {
  analyzeRealtimeAudio,
  TranscriptTurnResult,
  InsightResult,
} from '../services/realtimeAnalysisService';
import { REALTIME_WS_URL, AI_API_BASE_URL } from '../constants';
import Sound, { RecordBackType } from 'react-native-nitro-sound';
import RNFS from 'react-native-fs';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { RootStackParamList } from '../navigation/AppNavigator';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';

type RealtimeSessionRoute = NativeStackScreenProps<
  RootStackParamList, 'RealtimeSession'
>['route'];

type TranscriptTurn = {
  id: string; speaker: string; text: string; type: 'partial' | 'final';
  suggestions?: string[];
};
type Insight = {
  id: string; kind: 'risk' | 'success'; message: string;
  suggestion?: string; turnId: string;
};
type SavedExpression = {
  id: string; original: string; corrected: string; note: string;
};

const EMPTY_TIPS = [
  '자연스럽게 말씀해 보세요',
  '또박또박 천천히 말해보세요',
  '새로운 표현에 도전해 보세요',
  '짧은 문장부터 시작해도 좋아요',
];

// ─── Tokens ───────────────────────────────────────────────────────────────────
const C = {
  // Base
  canvas:   '#F2F1F7',
  paper:    '#F8F7FC',
  white:    '#FFFFFF',

  // Greyscale
  ink100:   '#111118',
  ink70:    '#4A4858',
  ink40:    '#9694A8',
  ink20:    '#C8C6D8',
  ink10:    '#E4E2EF',

  // Accent — purple
  terra:    '#5B35E8',
  terraFg:  '#EDEAFC',

  // Semantic
  risk:     '#7C3AED',
  riskFg:   '#F3EEFF',
  riskLine: '#C4B5FD',

  ok:       '#4338CA',
  okFg:     '#EEF0FF',
  okLine:   '#A5B4FC',

  // Mic states
  recRed:   '#D63B2F',
} as const;

const WAVE_H = [0.25, 0.5, 0.8, 1.0, 0.7, 0.4, 0.9, 0.55, 0.35, 0.75, 0.45];
const STREAM_CHUNK_MS = 5000;

const pad2 = (n: number) => n.toString().padStart(2, '0');
const fmt = (s: number) => `${pad2(Math.floor(s / 60))}:${pad2(s % 60)}`;

// ─── Waveform ─────────────────────────────────────────────────────────────────
function Waveform({ active }: { active: boolean }) {
  const bars = useRef(WAVE_H.map(() => new Animated.Value(0.2))).current;
  useEffect(() => {
    if (!active) {
      bars.forEach(b => Animated.timing(b, { toValue: 0.2, duration: 400, useNativeDriver: true }).start());
      return;
    }
    const loops = bars.map((b, i) =>
      Animated.loop(Animated.sequence([
        Animated.timing(b, { toValue: WAVE_H[i], duration: 220 + i * 38, useNativeDriver: true }),
        Animated.timing(b, { toValue: 0.2, duration: 220 + i * 38, useNativeDriver: true }),
      ]))
    );
    loops.forEach(l => l.start());
    return () => loops.forEach(l => l.stop());
  }, [active, bars]);

  return (
    <View style={wv.row}>
      {bars.map((b, i) => (
        <Animated.View key={i} style={[wv.bar, {
          transform: [{ scaleY: b }],
          backgroundColor: active ? C.recRed : C.ink20,
        }]} />
      ))}
    </View>
  );
}

// ─── Insight ──────────────────────────────────────────────────────────────────
function Insight({ item, onSave, saved }: { item: Insight; onSave?: () => void; saved?: boolean }) {
  const risk = item.kind === 'risk';
  const canSave = risk && !!item.suggestion && !!onSave;
  return (
    <View style={[ins.wrap, { backgroundColor: risk ? C.riskFg : C.okFg }]}>
      <View style={ins.header}>
        <Text style={[ins.badge, { color: risk ? C.risk : C.ok }]}>
          {risk ? '주의' : '잘함'}
        </Text>
        <Text style={ins.msg} numberOfLines={2}>{item.message}</Text>
        {canSave ? (
          <TouchableOpacity onPress={onSave} hitSlop={8} style={ins.saveBtn}>
            {saved
              ? <BookmarkCheck size={16} color={C.terra} fill={C.terra} />
              : <Bookmark size={16} color={C.risk} />}
          </TouchableOpacity>
        ) : null}
      </View>
      {item.suggestion ? (
        <Text style={[ins.sugg, { color: risk ? C.risk : C.ok }]}>
          → {item.suggestion}
        </Text>
      ) : null}
    </View>
  );
}

// ─── Suggestion Cards ────────────────────────────────────────────────────────
function SuggestionCards({ suggestions }: { suggestions: string[] }) {
  return (
    <View style={sg.wrap}>
      <Text style={sg.label}>💬 답변 제안</Text>
      {suggestions.map((s, i) => (
        <TouchableOpacity key={i} style={sg.card} activeOpacity={0.7}>
          <Text style={sg.text} numberOfLines={2}>{s}</Text>
          <ArrowRight size={12} color={C.terra} />
        </TouchableOpacity>
      ))}
    </View>
  );
}

// ─── Turn ─────────────────────────────────────────────────────────────────────
function Turn({
  turn, insight, avatarName, onSaveInsight, isInsightSaved,
}: {
  turn: TranscriptTurn; insight?: Insight; avatarName?: string;
  onSaveInsight?: (insight: Insight, turn: TranscriptTurn) => void;
  isInsightSaved?: (insight: Insight) => boolean;
}) {
  const live = turn.type === 'partial';
  const isUser = !avatarName || turn.speaker !== avatarName;
  const hasSuggestions = !isUser && !live && (turn.suggestions?.length ?? 0) > 0;

  return (
    <View style={tn.row}>
      <View style={[tn.bubble, isUser ? tn.bubbleUser : tn.bubblePartner, live && tn.bubbleLive]}>
        <Text style={[tn.text, live && tn.textLive]}>
          {turn.text}{live ? ' ▌' : ''}
        </Text>
        {live && <Text style={tn.recDot}>● 녹음 중</Text>}
      </View>
      {insight ? (
        <View style={tn.insightWrap}>
          <Insight
            item={insight}
            onSave={onSaveInsight ? () => onSaveInsight(insight, turn) : undefined}
            saved={isInsightSaved ? isInsightSaved(insight) : false}
          />
        </View>
      ) : null}
      {hasSuggestions ? (
        <View style={tn.insightWrap}>
          <SuggestionCards suggestions={turn.suggestions!} />
        </View>
      ) : null}
    </View>
  );
}

// ─── Empty (initial state only) ───────────────────────────────────────────────
const BAR_HEIGHTS = [10, 18, 26, 18, 10];
function Empty() {
  const [tipIdx, setTipIdx] = useState(0);
  const fade = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    const interval = setInterval(() => {
      Animated.sequence([
        Animated.timing(fade, { toValue: 0, duration: 250, useNativeDriver: true }),
        Animated.timing(fade, { toValue: 1, duration: 250, useNativeDriver: true }),
      ]).start();
      setTimeout(() => setTipIdx(i => (i + 1) % EMPTY_TIPS.length), 250);
    }, 3000);
    return () => clearInterval(interval);
  }, [fade]);
  return (
    <View style={em.wrap}>
      <View style={em.barsRow}>
        {BAR_HEIGHTS.map((h, i) => (
          <View key={i} style={[em.bar, { height: h }]} />
        ))}
      </View>
      <Text style={em.title}>대화를 시작하세요</Text>
      <Text style={em.sub}>아래 버튼을 눌러 녹음을 시작해보세요</Text>
      <Animated.View style={[em.tipChip, { opacity: fade }]}>
        <Lightbulb size={13} color={C.terra} strokeWidth={2} />
        <Text style={em.tipText}>{EMPTY_TIPS[tipIdx]}</Text>
      </Animated.View>
    </View>
  );
}

// ─── Analyzing placeholder (mid-session) ──────────────────────────────────────
function AnalyzingRow() {
  const op = useRef(new Animated.Value(0.4)).current;
  useEffect(() => {
    const loop = Animated.loop(Animated.sequence([
      Animated.timing(op, { toValue: 1,   duration: 600, useNativeDriver: true }),
      Animated.timing(op, { toValue: 0.4, duration: 600, useNativeDriver: true }),
    ]));
    loop.start();
    return () => loop.stop();
  }, [op]);

  return (
    <Animated.View style={[em.analyzeRow, { opacity: op }]}>
      {[0, 1, 2].map(i => (
        <View key={i} style={em.analyzeDot} />
      ))}
      <Text style={em.analyzeText}>분석 중</Text>
    </Animated.View>
  );
}

// ─── Normalizers ─────────────────────────────────────────────────────────────
const normTurns = (turns: TranscriptTurnResult[] = []): TranscriptTurn[] =>
  turns.map((t, i) => ({
    id: t.id ?? `t-${Date.now()}-${i}`,
    speaker: String(t.speaker ?? 'Speaker'),
    text: t.text ?? '',
    type: 'final',
    suggestions: t.suggestions,
  }));

const normInsights = (items: InsightResult[] = []): Insight[] =>
  items.map((it, i) => ({
    id: it.id ?? `i-${Date.now()}-${i}`,
    kind: it.kind === 'risk' ? 'risk' : 'success',
    message: it.message ?? '',
    suggestion: it.suggestion,
    turnId: ((it as any).turnId ?? (it as any).turn_id ?? '') as string,
  }));

const normalizeRecordingUri = (uri: string) =>
  uri.startsWith('file://') ? uri : `file://${uri}`;

// ─── Screen ───────────────────────────────────────────────────────────────────
export default function RealtimeSessionScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<RealtimeSessionRoute>();
  const avatar   = route.params?.avatar;
  const routeSessionId = route.params?.sessionId as string | undefined;
  const situation  = route.params?.situation;
  const scenarioObj = situation && typeof situation === 'object' && situation.name_ko ? situation : null;
  const [scenarioBannerVisible, setScenarioBannerVisible] = useState(!!scenarioObj);

  // Stable session id for the whole realtime session (so DB-saved mistakes group together).
  const sessionIdRef = useRef(
    routeSessionId || `realtime-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  );
  const sessionId = sessionIdRef.current;

  const [userId, setUserId] = useState('test-user-1');
  useEffect(() => {
    (async () => {
      const id = (await AsyncStorage.getItem('userId')) || (await AsyncStorage.getItem('user_id'));
      if (id) setUserId(id);
    })();
  }, []);

  // Fetch avatar opening line when in avatar practice mode
  useEffect(() => {
    if (!scenarioObj || !avatar) return;
    fetch(`${AI_API_BASE_URL}/chat/avatar-respond`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        avatar,
        scenario: scenarioObj,
        conversation_history: [],
        user_message: null,
        speech_level: expectedSpeechLevel,
      }),
    })
      .then(r => r.json())
      .then(data => {
        const text: string = data?.response;
        if (text && text.trim()) {
          const openerTurn: TranscriptTurn = {
            id: `avatar-opener-${Date.now()}`,
            speaker: avatar.name_ko,
            text: text.trim(),
            type: 'final',
          };
          setTurns([openerTurn]);
          conversationHistoryRef.current = [{ speaker: 'avatar', text: text.trim() }];
        }
      })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Register this session in the DB so stats (completedSessions, practiceMinutes) are tracked.
  // Skip when resuming an existing session — the DB record already exists.
  useEffect(() => {
    if (routeSessionId) return;
    createSession({
      avatarId: String(avatar?.id ?? 'system'),
      avatarName: avatar?.name_ko ?? '상대방',
      avatarIcon: avatar?.icon ?? 'user',
      avatarBg: avatar?.avatar_bg ?? '#555',
      situation: typeof situation === 'object' ? (situation as any)?.name_ko : (situation ?? '일상 대화'),
      difficulty: avatar?.difficulty ?? 'medium',
    }).then(s => {
      sessionIdRef.current = s.sessionId;
    }).catch(() => {});
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Restore turns when resuming an existing session ─────────────────────────
  useEffect(() => {
    if (!routeSessionId) return;
    AsyncStorage.getItem(`realtime_turns_${routeSessionId}`)
      .then(raw => {
        if (!raw) return;
        try {
          const prev: TranscriptTurn[] = JSON.parse(raw);
          if (Array.isArray(prev) && prev.length > 0) {
            setTurns(prev);
            setHasStarted(true);
            setHasRecorded(true);
            // Rebuild conversation history so AI context is preserved
            conversationHistoryRef.current = prev
              .filter(t => t.type === 'final')
              .map(t => ({
                speaker: t.speaker === '나' ? 'user' : 'avatar',
                text: t.text,
              }))
              .slice(-16);
          }
        } catch {}
      })
      .catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Map avatar's expected speech level (from user) to backend code (formal|polite|informal).
  const expectedSpeechLevel: string = (() => {
    const role = avatar?.role || '';
    if (role === 'professor' || role === 'boss' || role === 'ceo' || role === 'client') return 'formal';
    if (role === 'friend' || role === 'close_friend' || role === 'classmate' || role === 'younger_sibling') return 'informal';
    return 'polite';
  })();

  const [recording, setRecording]     = useState(false);
  const [hasStarted, setHasStarted]   = useState(false);
  const [hasRecorded, setHasRecorded] = useState(false);
  const [duration, setDuration]       = useState(0);
  const [ending, setEnding]           = useState(false);
  const [analyzing, setAnalyzing]     = useState(false);
  const [showRating, setShowRating]   = useState(false);
  const [pendingRating, setPendingRating] = useState(0);
  const [processingChunks, setProcessingChunks] = useState(0);
  const [turns, setTurns]           = useState<TranscriptTurn[]>([]);
  const [insights, setInsights]     = useState<Insight[]>([]);
  const [recUri, setRecUri]         = useState('');
  const [savedExpressions, setSavedExpressions] = useState<SavedExpression[]>([]);
  const [showSavedModal, setShowSavedModal] = useState(false);
  const conversationHistoryRef = useRef<{speaker: string; text: string}[]>([]);

  const handleSaveInsight = useCallback((insight: Insight, turn: TranscriptTurn) => {
    if (!insight.suggestion || !turn.text) return;
    setSavedExpressions(prev => {
      if (prev.some(e => e.id === insight.id)) {
        return prev.filter(e => e.id !== insight.id);
      }
      return [...prev, {
        id: insight.id,
        original: turn.text,
        corrected: insight.suggestion!,
        note: insight.message,
      }];
    });
  }, []);

  const isInsightSaved = useCallback(
    (insight: Insight) => savedExpressions.some(e => e.id === insight.id),
    [savedExpressions],
  );

  const rippleScale   = useRef(new Animated.Value(1)).current;
  const rippleOpacity = useRef(new Animated.Value(0)).current;
  const rippleLoop    = useRef<Animated.CompositeAnimation | null>(null);
  const ended         = useRef(false);
  const hasSpeechRef  = useRef(false);
  const wsRef         = useRef<WebSocket | null>(null);
  const scrollRef     = useRef<ScrollView>(null);
  const recordingRef  = useRef(false);
  const rotatingRef   = useRef(false);
  const recorderActiveRef = useRef(false);
  const chunkTimerRef    = useRef<ReturnType<typeof setInterval> | null>(null);
  const durationTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const chunkIndexRef = useRef(0);

  const setRecordingState = (value: boolean) => {
    recordingRef.current = value;
    setRecording(value);
  };

  useEffect(() => {
    setAnalyzing(processingChunks > 0);
  }, [processingChunks]);

  useEffect(() => {
    return () => {
      if (durationTimerRef.current) clearInterval(durationTimerRef.current);
      if (chunkTimerRef.current) clearInterval(chunkTimerRef.current);
      Sound.removeRecordBackListener();
      Sound.stopRecorder().catch(() => {});
      recorderActiveRef.current = false;
    };
  }, []);

  // ─── WebSocket connection ─────────────────────────────────────────────────
  useEffect(() => {
    const ws = new WebSocket(REALTIME_WS_URL);
    wsRef.current = ws;
    ws.onopen  = () => console.log('[WS] connected');
    ws.onerror = (e) => console.warn('[WS] error', e);
    ws.onclose = () => console.log('[WS] closed');
    return () => { ws.close(); wsRef.current = null; };
  }, []);

  useEffect(() => {
    if (recording) {
      rippleLoop.current = Animated.loop(
        Animated.parallel([
          Animated.sequence([
            Animated.timing(rippleScale,   { toValue: 1.7,  duration: 1000, useNativeDriver: true }),
            Animated.timing(rippleScale,   { toValue: 1,    duration: 0,    useNativeDriver: true }),
          ]),
          Animated.sequence([
            Animated.timing(rippleOpacity, { toValue: 0,    duration: 1000, useNativeDriver: true }),
            Animated.timing(rippleOpacity, { toValue: 0.25, duration: 0,    useNativeDriver: true }),
          ]),
        ])
      );
      rippleLoop.current.start();
    } else {
      rippleLoop.current?.stop();
      rippleScale.setValue(1);
      rippleOpacity.setValue(0);
    }
  }, [recording, rippleScale, rippleOpacity]);

  useEffect(() => {
    const t = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    return () => clearTimeout(t);
  }, [turns]);

  async function askMicPerm(): Promise<boolean> {
    if (Platform.OS !== 'android') return true;
    const r = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
      { title: '마이크 권한', message: 'Talkativ이 녹음하려면 마이크 접근이 필요합니다.', buttonPositive: '허용', buttonNegative: '거부' }
    );
    if (r !== PermissionsAndroid.RESULTS.GRANTED) { Alert.alert('권한 필요', '설정에서 마이크를 허용해주세요.'); return false; }
    return true;
  }

  const finish = useCallback(async (rating = 0) => {
    if (ended.current) return;
    ended.current = true;
    setEnding(true);
    try {
      if (recordingRef.current) {
        setRecordingState(false);
        if (chunkTimerRef.current) clearInterval(chunkTimerRef.current);
        chunkTimerRef.current = null;
        Sound.removeRecordBackListener();
        await Sound.stopRecorder();
        recorderActiveRef.current = false;
      }
    } catch {}
    try { if (sessionIdRef.current) await endSession(sessionIdRef.current); } catch {}

    const finalTurns = turns.filter(t => t.type === 'final');

    // Save a preview so the session appears on the home screen "최근 대화" section
    // and in ConversationHistory (기록 보기).
    const lastUserTurn   = finalTurns.filter(t => t.speaker === '나').slice(-1)[0];
    const lastAvatarTurn = finalTurns.filter(t => t.speaker !== '나').slice(-1)[0];
    saveConversationPreview(makePreviewPayload({
      sessionId:       sessionIdRef.current,
      avatarId:        String(avatar?.id ?? 'system'),
      avatarName:      avatar?.name_ko ?? '아바타',
      situation:       typeof situation === 'object' ? (situation as any)?.name_ko : (situation ?? '일상 대화'),
      messageCount:    finalTurns.length,
      lastUserMessage: lastUserTurn?.text,
      lastAiMessage:   lastAvatarTurn?.text,
      sessionType:     'realtime',
    })).catch(() => {});

    navigation.navigate('Analytics', {
      avatar,
      duration: fmt(duration),
      turns: finalTurns,
      insights,
      sessionId: sessionIdRef.current,
      rating,
      source: 'session',
      savedExpressions,
    });
  }, [navigation, avatar, situation, duration, turns, insights, savedExpressions]);

  const cancelSession = useCallback(async () => {
    if (ended.current) return;
    ended.current = true;
    try {
      if (recordingRef.current) {
        setRecordingState(false);
        if (chunkTimerRef.current) clearInterval(chunkTimerRef.current);
        chunkTimerRef.current = null;
        Sound.removeRecordBackListener();
        await Sound.stopRecorder();
        recorderActiveRef.current = false;
      }
    } catch {}
    try { if (sessionIdRef.current) await endSession(sessionIdRef.current); } catch {}
    navigation.goBack();
  }, [navigation]);

  const onCancelPress = useCallback(() => {
    Alert.alert(
      '세션 취소',
      '세션을 취소하면 분석 결과가 저장되지 않습니다.',
      [
        { text: '계속하기', style: 'cancel' },
        { text: '나가기', style: 'destructive', onPress: cancelSession },
      ]
    );
  }, [cancelSession]);

  useFocusEffect(useCallback(() => {
    const u = navigation.addListener('beforeRemove', (e: any) => {
      if (ended.current || ending) return;
      e.preventDefault();
      onCancelPress();
    });
    return u;
  }, [navigation, ending, onCancelPress]));

  const processAnalysisResult = useCallback((res: { turns?: TranscriptTurnResult[]; insights?: InsightResult[]; avatarResponse?: string } | null, chunkIndex: number) => {
    const nextTurns = normTurns(res?.turns ?? []).filter(t => t.text.trim().length > 0);
    const seenLabels: string[] = [];
    for (const t of nextTurns) {
      if (!seenLabels.includes(t.speaker)) seenLabels.push(t.speaker);
    }
    const userLabel = seenLabels[0];
    const avatarLabel = seenLabels[1];
    for (const t of nextTurns) {
      if (userLabel && t.speaker === userLabel) t.speaker = '나';
      else if (avatarLabel && avatar?.name_ko && t.speaker === avatarLabel) t.speaker = avatar.name_ko;
    }
    const nextInsights = normInsights(res?.insights ?? []);
    if (nextTurns.length > 0) hasSpeechRef.current = true;
    if (nextTurns.length === 0 && nextInsights.length === 0 && !recordingRef.current && !hasSpeechRef.current) {
      nextInsights.push({
        id: `i-empty-${Date.now()}`,
        kind: 'risk',
        message: '음성이 업로드됐지만 인식된 문장이 없어요.',
        suggestion: '한 문장 이상 또렷하게 말한 뒤 다시 시도해 보세요.',
        turnId: '',
      });
    }

    // Build avatar response turn and update conversation history
    const avatarResponseText = res?.avatarResponse?.trim();
    const avatarTurn: TranscriptTurn | null = avatarResponseText && avatar?.name_ko ? {
      id: `avatar-reply-${chunkIndex}-${Date.now()}`,
      speaker: avatar.name_ko,
      text: avatarResponseText,
      type: 'final',
    } : null;

    if (nextTurns.length > 0 || avatarTurn) {
      const userText = nextTurns.map(t => t.text).join(' ').trim();
      const newHistory = [...conversationHistoryRef.current];
      if (userText) newHistory.push({ speaker: 'user', text: userText });
      if (avatarResponseText) newHistory.push({ speaker: 'avatar', text: avatarResponseText });
      conversationHistoryRef.current = newHistory.slice(-16);
    }

    const allNewTurns = avatarTurn ? [...nextTurns, avatarTurn] : nextTurns;
    setTurns(p => {
      const combined = [...p.filter(t => t.type !== 'partial'), ...allNewTurns];
      // Persist final turns so session can be resumed with full history
      const finalTurns = combined.filter(t => t.type === 'final');
      if (finalTurns.length > 0) {
        AsyncStorage.setItem(
          `realtime_turns_${sessionIdRef.current}`,
          JSON.stringify(finalTurns),
        ).catch(() => {});
      }
      return combined;
    });
    setInsights(p => {
      const seen = new Set(p.map(i => i.message));
      return [...p, ...nextInsights.filter(i => !seen.has(i.message))];
    });
    setProcessingChunks(count => Math.max(0, count - 1));
  }, [avatar]);

  const uploadRecordedChunk = useCallback(async (rawUri: string, chunkIndex: number) => {
    const uri = normalizeRecordingUri(rawUri);
    setProcessingChunks(count => count + 1);

    // ── WebSocket path (faster) ──────────────────────────────────────────────
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        const filePath = uri.replace('file://', '');
        const audio = await RNFS.readFile(filePath, 'base64');
        ws.onmessage = (event) => {
          try {
            processAnalysisResult(JSON.parse(event.data), chunkIndex);
          } catch { setProcessingChunks(c => Math.max(0, c - 1)); }
        };
        ws.send(JSON.stringify({
          audio,
          sessionId: sessionIdRef.current,
          userId,
          avatarRole: avatar?.role ?? '',
          avatarName: avatar?.name_ko ?? '',
          avatar: avatar ?? null,
          scenario: scenarioObj ?? null,
          expectedSpeechLevel,
          chunkIndex,
          conversationHistory: conversationHistoryRef.current.slice(-8),
        }));
        return;
      } catch (e) {
        console.warn('[WS] send failed, falling back to HTTP', e);
        setProcessingChunks(count => Math.max(0, count - 1));
        setProcessingChunks(count => count + 1);
      }
    }

    // ── HTTP fallback ────────────────────────────────────────────────────────
    try {
      const form = new FormData();
      form.append('file', { uri, name: `recording-${chunkIndex}.m4a`, type: 'audio/mp4' } as any);
      if (sessionIdRef.current) form.append('sessionId', sessionIdRef.current);
      if (avatar?.role) form.append('avatarRole', avatar.role);
      form.append('userId', userId);
      form.append('expectedSpeechLevel', expectedSpeechLevel);
      form.append('chunkIndex', String(chunkIndex));

      const res = await analyzeRealtimeAudio(form);
      processAnalysisResult(res, chunkIndex);
    } catch (e: any) {
      setProcessingChunks(count => Math.max(0, count - 1));
      throw e;
    }
  }, [avatar, expectedSpeechLevel, userId, processAnalysisResult]);

  const rotateRecordingChunk = useCallback(async (restart: boolean) => {
    if (rotatingRef.current) return;
    if (!recorderActiveRef.current) return;
    rotatingRef.current = true;
    try {
      setTurns(p => p.filter(t => t.type !== 'partial'));
      Sound.removeRecordBackListener();
      const rawUri = await Sound.stopRecorder();
      recorderActiveRef.current = false;
      if (!rawUri) throw new Error('녹음 경로를 가져오지 못했습니다.');
      const chunkIndex = chunkIndexRef.current;
      chunkIndexRef.current += 1;

      if (restart && recordingRef.current) {
        await Sound.startRecorder();
        recorderActiveRef.current = true;
        Sound.addRecordBackListener((_: RecordBackType) => {});
        setTurns(p => [
          ...p,
          { id: `live-${Date.now()}`, speaker: '듣는 중', text: '다음 음성 조각을 듣고 있습니다', type: 'partial' },
        ]);
      }

      uploadRecordedChunk(rawUri, chunkIndex).catch((e: any) => {
        Alert.alert('분석 오류', e?.response?.data?.message ?? e?.message ?? '음성 조각 분석에 실패했습니다.');
      });
    } finally {
      rotatingRef.current = false;
    }
  }, [uploadRecordedChunk]);

  const startStreamingCapture = useCallback(async () => {
    if (!(await askMicPerm())) return;
    setHasStarted(true);
    if (!durationTimerRef.current) {
      durationTimerRef.current = setInterval(() => setDuration(d => d + 1), 1000);
    }
    await Sound.startRecorder();
    recorderActiveRef.current = true;
    Sound.addRecordBackListener((_: RecordBackType) => {});
    setRecordingState(true);
    setTurns(p => [
      ...p.filter(t => t.type !== 'partial'),
      { id: `live-${Date.now()}`, speaker: '듣는 중', text: '음성 스트림을 듣고 있습니다', type: 'partial' },
    ]);
    chunkTimerRef.current = setInterval(() => {
      if (recordingRef.current) {
        rotateRecordingChunk(true).catch((e: any) => {
          Alert.alert('오류', e?.message ?? '음성 조각을 처리하지 못했습니다.');
        });
      }
    }, STREAM_CHUNK_MS);
  }, [rotateRecordingChunk]);

  const stopStreamingCapture = useCallback(async () => {
    setHasRecorded(true);
    setRecordingState(false);
    if (chunkTimerRef.current) clearInterval(chunkTimerRef.current);
    chunkTimerRef.current = null;
    while (rotatingRef.current) {
      await new Promise<void>(resolve => setTimeout(resolve, 50));
    }
    if (recorderActiveRef.current) {
      await rotateRecordingChunk(false);
    }
  }, [rotateRecordingChunk]);

  const onMic = async () => {
    if (ending) return;
    try {
      if (recordingRef.current) {
        await stopStreamingCapture();
      } else {
        await startStreamingCapture();
      }
    } catch (e: any) {
      setRecordingState(false);
      if (chunkTimerRef.current) clearInterval(chunkTimerRef.current);
      chunkTimerRef.current = null;
      Sound.removeRecordBackListener();
      Sound.stopRecorder().catch(() => {});
      recorderActiveRef.current = false;
      setTurns(p => p.filter(t => t.type !== 'partial'));
      Alert.alert('오류', e?.response?.data?.message ?? e?.message ?? '문제가 발생했습니다.');
    }
  };



  const ok    = insights.filter(i => i.kind === 'success').length;
  const risk  = insights.filter(i => i.kind === 'risk').length;
  const solo  = insights.filter(i => !i.turnId);
  const final = turns.filter(t => t.type === 'final').length;
  const busy  = ending || recording || analyzing || !hasRecorded;

  return (
    <SafeAreaView style={s.safe} edges={['top']}>

      {/* ── Session card ── */}
      <View style={s.sessionCard}>
        <View style={s.sessionTopRow}>
          <TouchableOpacity onPress={onCancelPress} hitSlop={8} style={s.cancelBtn}>
            <ArrowLeft size={20} color={C.ink40} strokeWidth={2} />
          </TouchableOpacity>
          <View style={[s.sessionAvatar, { backgroundColor: avatar?.avatar_bg ?? '#555' }]}>
            <Icon name={(avatar?.icon ?? 'user') as IconName} size={18} color="#FFF" />
          </View>
          <View style={s.sessionInfo}>
            <Text style={s.sessionName}>{avatar?.name_ko ?? '아바타'}</Text>
            <Text style={s.sessionStatus}>
              {analyzing ? '분석 중' : recording ? '녹음 중' : '대기'}
            </Text>
          </View>
          {savedExpressions.length > 0 ? (
            <TouchableOpacity
              style={s.savedChip}
              onPress={() => setShowSavedModal(true)}
              activeOpacity={0.75}
            >
              <BookOpen size={13} color={C.terra} />
              <Text style={s.savedChipText}>{savedExpressions.length}</Text>
            </TouchableOpacity>
          ) : null}
        </View>
        {(final > 0 || ok > 0 || risk > 0) ? (
          <View style={s.statsStrip}>
            <View style={s.statItem}>
              <Text style={s.statNum}>{final}</Text>
              <Text style={s.statLabel}>발화</Text>
            </View>
            <View style={s.statDivider} />
            <View style={s.statItem}>
              <Text style={[s.statNum, { color: C.ok }]}>{ok}</Text>
              <Text style={s.statLabel}>잘함</Text>
            </View>
            <View style={s.statDivider} />
            <View style={s.statItem}>
              <Text style={[s.statNum, { color: C.risk }]}>{risk}</Text>
              <Text style={s.statLabel}>주의</Text>
            </View>
          </View>
        ) : null}
      </View>

      {/* ── Scenario banner (avatar practice mode only) ── */}
      {scenarioObj && scenarioBannerVisible ? (
        <View style={s.scenarioBanner}>
          <Target size={13} color={C.terra} strokeWidth={2} />
          <Text style={s.scenarioBannerText} numberOfLines={1}>{scenarioObj.name_ko}</Text>
          <TouchableOpacity onPress={() => setScenarioBannerVisible(false)} hitSlop={8}>
            <XIcon size={14} color={C.ink40} strokeWidth={2} />
          </TouchableOpacity>
        </View>
      ) : null}

      {/* ── Transcript ── */}
      <View style={s.feed}>
        <ScrollView
          ref={scrollRef}
          style={s.scroll}
          contentContainerStyle={s.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {turns.length === 0
            ? !hasStarted
              ? <Empty />
              : <AnalyzingRow />
            : turns.map(turn => (
                <Turn
                  key={turn.id} turn={turn}
                  avatarName={avatar?.name_ko}
                  insight={insights.find(i => i.turnId === turn.id)}
                  onSaveInsight={handleSaveInsight}
                  isInsightSaved={isInsightSaved}
                />
              ))}
          {solo.length > 0 && (
            <View style={s.soloWrap}>
              {solo.map(it => <Insight key={it.id} item={it} />)}
            </View>
          )}
        </ScrollView>
      </View>

      {/* ── Controls ── */}
      <View style={s.dock}>
        {/* Timer + waveform in one row */}
        <View style={s.timerRow}>
          {recording && <Waveform active />}
          <View style={[s.timerDot, recording && s.timerDotRec]} />
          <Text style={s.timerText}>{fmt(duration)}</Text>
        </View>

        {/* Mic centered */}
        <View style={s.micWrap}>
          {recording && (
            <Animated.View style={[s.ripple, {
              transform: [{ scale: rippleScale }], opacity: rippleOpacity,
            }]} />
          )}
          <TouchableOpacity
            style={[s.mic, recording && s.micRec, analyzing && !recording && s.micBusy]}
            onPress={onMic} activeOpacity={0.8}
            disabled={ending}
          >
            {recording
              ? <MicOff size={22} color="#FFF" strokeWidth={2.3} />
              : analyzing
                ? <Mic size={22} color="rgba(255,255,255,0.3)" strokeWidth={2} />
                : <Mic size={22} color="#FFF" strokeWidth={2.3} />}
          </TouchableOpacity>
        </View>

        <Text style={s.micHint}>
          {recording
            ? '녹음 중 · 탭하여 중지'
            : processingChunks > 0
              ? '분석 중...'
              : '탭하여 녹음 시작'}
        </Text>

        <TouchableOpacity
          style={[s.endBtn, busy && s.endBtnOff]}
          onPress={() => { setPendingRating(0); setShowRating(true); }}
          disabled={busy} activeOpacity={0.85}
        >
          <Text style={[s.endText, busy && s.endTextOff]}>
            {ending ? '종료 중...' : '세션 종료 · 피드백 보기'}
          </Text>
          {!busy && <ArrowRight size={15} color="#FFFFFF" strokeWidth={2.5} />}
        </TouchableOpacity>
      </View>
      {/* ── Saved expressions modal ── */}
      <Modal visible={showSavedModal} transparent animationType="slide" onRequestClose={() => setShowSavedModal(false)}>
        <View style={sm.backdrop}>
          <View style={sm.sheet}>
            <View style={sm.header}>
              <View style={sm.headerLeft}>
                <BookOpen size={18} color={C.terra} />
                <Text style={sm.title}>배운 표현</Text>
                <Text style={sm.count}>{savedExpressions.length}</Text>
              </View>
              <TouchableOpacity onPress={() => setShowSavedModal(false)} hitSlop={8}>
                <XIcon size={20} color={C.ink70} />
              </TouchableOpacity>
            </View>
            {savedExpressions.length === 0 ? (
              <View style={sm.emptyWrap}>
                <Text style={sm.emptyTitle}>저장된 표현이 없어요</Text>
                <Text style={sm.emptySub}>대화 중 북마크 아이콘을 눌러 표현을 저장할 수 있어요</Text>
              </View>
            ) : (
              <ScrollView style={sm.scroll} contentContainerStyle={sm.scrollContent}>
                {savedExpressions.map(e => (
                  <View key={e.id} style={sm.item}>
                    <Text style={sm.itemOriginal}>{e.original}</Text>
                    <View style={sm.itemArrowRow}>
                      <ArrowRight size={12} color={C.terra} />
                      <Text style={sm.itemCorrected}>{e.corrected}</Text>
                    </View>
                    <Text style={sm.itemNote}>{e.note}</Text>
                  </View>
                ))}
              </ScrollView>
            )}
          </View>
        </View>
      </Modal>

      {/* ── Rating modal ── */}
      <Modal visible={showRating} transparent animationType="fade" onRequestClose={() => setShowRating(false)}>
        <View style={rm.backdrop}>
          <View style={rm.sheet}>
            <Text style={rm.title}>세션 평점</Text>
            <Text style={rm.sub}>이번 대화 어떠셨나요?</Text>
            <View style={rm.stars}>
              {[1, 2, 3, 4, 5].map(n => (
                <TouchableOpacity key={n} onPress={() => setPendingRating(n)} activeOpacity={0.7}>
                  <Star
                    size={36}
                    color={C.terra}
                    fill={n <= pendingRating ? C.terra : 'none'}
                    strokeWidth={1.8}
                  />
                </TouchableOpacity>
              ))}
            </View>
            <View style={rm.actions}>
              <TouchableOpacity style={rm.skipBtn} onPress={() => { setShowRating(false); finish(0); }}>
                <Text style={rm.skipText}>건너뛰기</Text>
              </TouchableOpacity>
              <TouchableOpacity style={rm.confirmBtn} onPress={() => { setShowRating(false); finish(pendingRating); }}>
                <Text style={rm.confirmText}>완료</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },

  cancelBtn: {
    padding: 4,
  },

  // Session card
  sessionCard: {
    marginHorizontal: 16, marginTop: 12, marginBottom: 10,
    paddingHorizontal: 16, paddingVertical: 13,
    backgroundColor: C.white,
    borderRadius: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 8,
    elevation: 3,
  },
  sessionTopRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  sessionAvatar: {
    width: 42, height: 42, borderRadius: 21,
    alignItems: 'center', justifyContent: 'center',
  },
  sessionInfo: { flex: 1 },
  sessionName: { fontSize: 15, fontWeight: '700', color: C.ink100 },
  sessionStatus: { fontSize: 12, color: C.ink40, marginTop: 2 },
  sessionCounts: { flexDirection: 'row', gap: 8 },
  sessionCount: { fontSize: 13, fontWeight: '700' },
  savedChip: {
    flexDirection: 'row', alignItems: 'center', gap: 5,
    backgroundColor: C.terraFg, paddingHorizontal: 10, paddingVertical: 6,
    borderRadius: 99,
  },
  savedChipText: { fontSize: 12, fontWeight: '700', color: C.terra },
  statsStrip: {
    flexDirection: 'row', alignItems: 'center',
    marginTop: 12, paddingTop: 12,
    borderTopWidth: 1, borderTopColor: C.ink10,
  },
  statItem: { flex: 1, alignItems: 'center', gap: 2 },
  statNum: { fontSize: 17, fontWeight: '800', color: C.ink100 },
  statLabel: { fontSize: 10, fontWeight: '600', color: C.ink40, letterSpacing: 0.5, textTransform: 'uppercase' },
  statDivider: { width: 1, height: 28, backgroundColor: C.ink10 },

  // Timer (now in dock)
  timerRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7 },
  timerDot: { width: 7, height: 7, borderRadius: 3.5, backgroundColor: C.ink20 },
  timerDotRec: { backgroundColor: C.recRed },
  timerText: { fontSize: 20, fontWeight: '700', color: C.ink100, letterSpacing: 1 },

  // Scenario banner
  scenarioBanner: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    marginHorizontal: 16, marginBottom: 8,
    paddingHorizontal: 14, paddingVertical: 9,
    backgroundColor: C.terraFg, borderRadius: 12,
  },
  scenarioBannerText: { flex: 1, fontSize: 13, fontWeight: '600', color: C.terra },

  // Feed
  feed: { flex: 1, paddingHorizontal: 16 },
  feedHeader: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between', marginBottom: 12,
  },
  feedLabel: { fontSize: 11, fontWeight: '700', color: C.ink40, letterSpacing: 1.2, textTransform: 'uppercase' },
  feedCount: {
    fontSize: 11, fontWeight: '700', color: C.white,
    backgroundColor: C.ink40, paddingHorizontal: 7, paddingVertical: 2,
    borderRadius: 99, overflow: 'hidden',
  },
  scroll: { flex: 1 },
  scrollContent: { flexGrow: 1, gap: 4, paddingBottom: 8 },
  soloWrap: { marginTop: 8, gap: 4 },

  // Dock
  dock: {
    backgroundColor: C.white,
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 22,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.06,
    shadowRadius: 12,
    elevation: 12,
    gap: 8,
    alignItems: 'center',
  },
  micWrap: { width: 64, height: 64, alignItems: 'center', justifyContent: 'center' },
  ripple: {
    position: 'absolute',
    width: 64, height: 64, borderRadius: 32,
    backgroundColor: C.recRed,
  },
  mic: {
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: C.terra,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: C.terra,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 6,
  },
  micRec: { backgroundColor: C.recRed, shadowColor: C.recRed },
  micBusy: { backgroundColor: C.ink20, shadowOpacity: 0, elevation: 0 },
  muteChip: {
    width: 40, height: 40, borderRadius: 12,
    backgroundColor: C.canvas,
    borderWidth: 1, borderColor: C.ink10,
    alignItems: 'center', justifyContent: 'center',
  },
  micHint: {
    textAlign: 'center', fontSize: 12,
    color: C.ink40, fontWeight: '500',
  },
  endBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 8, paddingVertical: 13, borderRadius: 16,
    backgroundColor: C.terra, width: '100%',
  },
  endBtnOff: { backgroundColor: C.ink10 },
  endText: { fontSize: 15, fontWeight: '700', color: '#FFFFFF' },
  endTextOff: { color: C.ink40 },
});

// Waveform
const wv = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', height: 20, gap: 3 },
  bar: { width: 2.5, height: 16, borderRadius: 1.5 },
});

// Turn — centered transcript style
const tn = StyleSheet.create({
  row: {
    alignItems: 'center',
    paddingVertical: 5,
    gap: 5,
  },
  recDot: { fontSize: 10, color: C.recRed, marginTop: 4 },

  bubble: {
    width: '100%', borderRadius: 14,
    paddingHorizontal: 16, paddingVertical: 12,
  },
  bubbleUser: { backgroundColor: '#EDE9FF' },
  bubblePartner: {
    backgroundColor: C.white,
    borderWidth: 1, borderColor: C.ink10,
  },
  bubbleLive: { opacity: 0.7 },

  text: { fontSize: 15, lineHeight: 23, color: C.ink100, textAlign: 'center' },
  textLive: { color: C.ink70 },

  insightWrap: { width: '100%' },
});

// Insight — compact note style
const ins = StyleSheet.create({
  wrap: {
    borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 8,
    gap: 4,
  },
  header: {
    flexDirection: 'row', alignItems: 'center', gap: 7, flexWrap: 'wrap',
  },
  badge: {
    fontSize: 10, fontWeight: '800',
    letterSpacing: 0.8, textTransform: 'uppercase',
  },
  msg: { fontSize: 13, color: C.ink70, lineHeight: 18, flex: 1 },
  sugg: { fontSize: 12, fontWeight: '600', lineHeight: 18, paddingLeft: 2 },
  saveBtn: { padding: 2 },
});

// Suggestion cards
const sg = StyleSheet.create({
  wrap: { marginTop: 6, gap: 6 },
  label: { fontSize: 11, color: C.ink40, fontWeight: '600', marginBottom: 2 },
  card: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    backgroundColor: C.terraFg,
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8, gap: 8,
  },
  text: { fontSize: 13, color: C.terra, fontWeight: '500', flex: 1 },
});

// Empty
const em = StyleSheet.create({
  wrap: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, paddingBottom: 40 },
  barsRow: { flexDirection: 'row', alignItems: 'center', gap: 6, height: 36, marginBottom: 6 },
  bar: { width: 4, borderRadius: 2, backgroundColor: C.ink10 },
  title: { fontSize: 19, fontWeight: '700', color: C.ink100 },
  sub: { fontSize: 14, color: C.ink40, textAlign: 'center', lineHeight: 22 },

  analyzeRow: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'center', gap: 6,
    paddingVertical: 16,
  },
  analyzeDot: {
    width: 6, height: 6, borderRadius: 3,
    backgroundColor: C.terra,
  },
  analyzeText: { fontSize: 13, color: C.terra, fontWeight: '600' },
  tipChip: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    marginTop: 16, paddingHorizontal: 14, paddingVertical: 8,
    borderRadius: 99, backgroundColor: C.terraFg,
  },
  tipText: { fontSize: 13, color: C.terra, fontWeight: '600' },
});

// Saved expressions modal
const sm = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: C.white,
    borderTopLeftRadius: 22, borderTopRightRadius: 22,
    paddingHorizontal: 20, paddingTop: 18, paddingBottom: 28,
    maxHeight: '75%',
  },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    marginBottom: 12,
  },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  title: { fontSize: 17, fontWeight: '800', color: C.ink100 },
  count: {
    fontSize: 12, fontWeight: '700', color: C.terra,
    backgroundColor: C.terraFg, paddingHorizontal: 8, paddingVertical: 2,
    borderRadius: 99, overflow: 'hidden',
  },
  scroll: { maxHeight: 480 },
  scrollContent: { gap: 10, paddingBottom: 8 },
  item: {
    backgroundColor: C.paper, borderRadius: 12,
    paddingHorizontal: 14, paddingVertical: 12, gap: 5,
  },
  itemOriginal: { fontSize: 14, color: C.ink70, lineHeight: 20 },
  itemArrowRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  itemCorrected: { fontSize: 14, fontWeight: '700', color: C.terra, flex: 1 },
  itemNote: { fontSize: 11, color: C.ink40, marginTop: 2, lineHeight: 16 },
  emptyWrap: { alignItems: 'center', paddingVertical: 32, gap: 8 },
  emptyTitle: { fontSize: 15, fontWeight: '700', color: C.ink70 },
  emptySub: { fontSize: 13, color: C.ink40, textAlign: 'center', paddingHorizontal: 20, lineHeight: 19 },
});

// Rating modal
const rm = StyleSheet.create({
  backdrop: {
    flex: 1, backgroundColor: 'rgba(0,0,0,0.45)',
    alignItems: 'center', justifyContent: 'center',
  },
  sheet: {
    width: '82%', backgroundColor: C.white,
    borderRadius: 24, padding: 28,
    alignItems: 'center', gap: 10,
  },
  title: { fontSize: 18, fontWeight: '700', color: C.ink100 },
  sub:   { fontSize: 14, color: C.ink70, marginBottom: 4 },
  stars: { flexDirection: 'row', gap: 12, marginVertical: 8 },
  actions: { flexDirection: 'row', gap: 12, marginTop: 8, width: '100%' },
  skipBtn: {
    flex: 1, paddingVertical: 13, borderRadius: 12,
    backgroundColor: C.canvas, alignItems: 'center',
  },
  skipText: { fontSize: 15, fontWeight: '600', color: C.ink70 },
  confirmBtn: {
    flex: 2, paddingVertical: 13, borderRadius: 12,
    backgroundColor: C.terra, alignItems: 'center',
  },
  confirmText: { fontSize: 15, fontWeight: '700', color: C.white },
});
