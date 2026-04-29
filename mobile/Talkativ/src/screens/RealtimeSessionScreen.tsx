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
import { useNavigation, useRoute, useFocusEffect } from '@react-navigation/native';
import {
  Mic, MicOff, X, Volume2, VolumeX,
  CircleDashed, ArrowRight,
} from 'lucide-react-native';
import { Icon, type IconName } from '../components';
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
  RootStackParamList, 'RealtimeSession'
>['route'];

type TranscriptTurn = {
  id: string; speaker: string; text: string; type: 'partial' | 'final';
};
type Insight = {
  id: string; kind: 'risk' | 'success'; message: string;
  suggestion?: string; turnId: string;
};

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
function Insight({ item }: { item: Insight }) {
  const risk = item.kind === 'risk';
  return (
    <View style={[ins.wrap, { borderLeftColor: risk ? C.risk : C.ok }]}>
      <Text style={[ins.label, { color: risk ? C.risk : C.ok }]}>
        {risk ? '주의' : '잘함'}
      </Text>
      <Text style={ins.msg}>{item.message}</Text>
      {item.suggestion ? (
        <Text style={[ins.sugg, { color: risk ? C.risk : C.ok }]}>
          → {item.suggestion}
        </Text>
      ) : null}
    </View>
  );
}

// ─── Turn ─────────────────────────────────────────────────────────────────────
function Turn({ turn, insight, avatarName }: { turn: TranscriptTurn; insight?: Insight; avatarName?: string }) {
  const live = turn.type === 'partial';
  // User = not the avatar and not an unknown partner label
  const isUser = !avatarName || turn.speaker !== avatarName;

  return (
    <View style={[tn.row, isUser ? tn.rowUser : tn.rowPartner]}>
      {/* Bubble + label */}
      <View style={[tn.col, isUser ? tn.colUser : tn.colPartner]}>
        <View style={tn.labelRow}>
          {!isUser && <View style={[tn.dot, { backgroundColor: C.ink40 }]} />}
          <Text style={[tn.speaker, isUser && tn.speakerUser]}>
            {live ? '나 (녹음 중)' : isUser ? '나' : turn.speaker}
          </Text>
          {isUser && <View style={[tn.dot, { backgroundColor: '#6C3BFF' }]} />}
          {live && (
            <CircleDashed size={9} color={C.recRed} strokeWidth={2.5} />
          )}
        </View>

        <View style={[tn.bubble, isUser ? tn.bubbleUser : tn.bubblePartner, live && tn.bubbleLive]}>
          <Text style={[tn.text, isUser ? tn.textUser : tn.textPartner, live && tn.textLive]}>
            {turn.text}{live ? ' ▌' : ''}
          </Text>
        </View>
      </View>

      {insight ? (
        <View style={[tn.insightWrap, isUser ? tn.insightUser : tn.insightPartner]}>
          <Insight item={insight} />
        </View>
      ) : null}
    </View>
  );
}

// ─── Empty ────────────────────────────────────────────────────────────────────
function Empty({ analyzing }: { analyzing: boolean }) {
  const scale = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    const loop = Animated.loop(Animated.sequence([
      Animated.timing(scale, { toValue: 1.06, duration: 1600, useNativeDriver: true }),
      Animated.timing(scale, { toValue: 1, duration: 1600, useNativeDriver: true }),
    ]));
    loop.start();
    return () => loop.stop();
  }, [scale]);

  return (
    <View style={em.wrap}>
      <Animated.View style={[em.ring, { transform: [{ scale }] }]} />
      <View style={em.circle}>
        <Mic size={22} color={C.ink70} strokeWidth={1.6} />
      </View>
      <Text style={em.title}>
        {analyzing ? '분석 중...' : '대화를 시작하세요'}
      </Text>
      <Text style={em.sub}>
        {analyzing
          ? '잠시 후 내용이 표시됩니다'
          : '아래 버튼을 눌러\n녹음을 시작해보세요'}
      </Text>
    </View>
  );
}

// ─── Normalizers ─────────────────────────────────────────────────────────────
const normTurns = (turns: TranscriptTurnResult[] = []): TranscriptTurn[] =>
  turns.map((t, i) => ({
    id: t.id ?? `t-${Date.now()}-${i}`,
    speaker: String(t.speaker ?? 'Speaker'),
    text: t.text ?? '',
    type: 'final',
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
  const sessionId  = route.params?.sessionId as string | undefined;
  const situation  = route.params?.situation as string | undefined;

  const [recording, setRecording]   = useState(false);
  const [muted, setMuted]           = useState(false);
  const [duration, setDuration]     = useState(0);
  const [ending, setEnding]         = useState(false);
  const [analyzing, setAnalyzing]   = useState(false);
  const [turns, setTurns]           = useState<TranscriptTurn[]>([]);
  const [insights, setInsights]     = useState<Insight[]>([]);
  const [recUri, setRecUri]         = useState('');

  const rippleScale   = useRef(new Animated.Value(1)).current;
  const rippleOpacity = useRef(new Animated.Value(0)).current;
  const rippleLoop    = useRef<Animated.CompositeAnimation | null>(null);
  const ended         = useRef(false);
  const scrollRef     = useRef<ScrollView>(null);

  useEffect(() => {
    const t = setInterval(() => setDuration(d => d + 1), 1000);
    return () => { clearInterval(t); Sound.removeRecordBackListener(); Sound.stopRecorder().catch(() => {}); };
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

  const finish = useCallback(async (feedback: boolean) => {
    if (ended.current) return;
    ended.current = true;
    setEnding(true);
    try { if (recording) { setRecording(false); Sound.removeRecordBackListener(); await Sound.stopRecorder(); } } catch {}
    try { if (sessionId) await endSession(sessionId); } catch {}
    if (feedback) {
      navigation.navigate('Feedback', { avatar, sessionId, situation, duration: fmt(duration), recordingUri: recUri, turns, insights });
    } else navigation.goBack();
  }, [recording, sessionId, navigation, avatar, situation, duration, recUri, turns, insights]);

  useFocusEffect(useCallback(() => {
    const u = navigation.addListener('beforeRemove', (e: any) => {
      if (ended.current || ending) return;
      e.preventDefault();
      Alert.alert('세션 종료', '세션을 종료하시겠습니까?', [
        { text: '취소', style: 'cancel' },
        { text: '종료', style: 'destructive', onPress: () => finish(false) },
      ]);
    });
    return u;
  }, [navigation, ending, finish]));

  const onMic = async () => {
    if (ending || analyzing) return;
    try {
      if (recording) {
        setRecording(false); setAnalyzing(true);
        setTurns(p => p.filter(t => t.type !== 'partial'));
        Sound.removeRecordBackListener();
        const rawUri = await Sound.stopRecorder();
        if (!rawUri) throw new Error('녹음 경로를 가져오지 못했습니다.');
        const uri = normalizeRecordingUri(rawUri);
        setRecUri(uri);
        const form = new FormData();
        form.append('file', { uri, name: 'recording.m4a', type: 'audio/mp4' } as any);
        if (sessionId) form.append('sessionId', sessionId);
        if (avatar?.role) form.append('avatarRole', avatar.role);
        const res = await analyzeRealtimeAudio(form);
        const nextTurns = normTurns(res?.turns ?? []).filter(t => t.text.trim().length > 0);

        // Map raw CLOVA speaker labels (e.g. "0", "1") to user vs. avatar.
        // First speaker to appear = user, second = avatar.
        const seenLabels: string[] = [];
        for (const t of nextTurns) {
          if (!seenLabels.includes(t.speaker)) seenLabels.push(t.speaker);
        }
        const avatarLabel = seenLabels[1];
        if (avatarLabel && avatar?.name_ko) {
          for (const t of nextTurns) {
            if (t.speaker === avatarLabel) t.speaker = avatar.name_ko;
          }
        }

        const nextInsights = normInsights(res?.insights ?? []);

        if (nextTurns.length === 0 && nextInsights.length === 0) {
          nextInsights.push({
            id: `i-empty-${Date.now()}`,
            kind: 'risk',
            message: '음성이 업로드됐지만 인식된 문장이 없어요.',
            suggestion: '한 문장 이상 또렷하게 말한 뒤 다시 시도해 보세요.',
            turnId: '',
          });
        }

        setTurns(p => [...p, ...nextTurns]);
        setInsights(p => [...p, ...nextInsights]);
      } else {
        if (!(await askMicPerm())) return;
        setTurns([]); setInsights([]); setRecUri('');
        await Sound.startRecorder();
        Sound.addRecordBackListener((_: RecordBackType) => {});
        setRecording(true);
        setTurns([{ id: `live-${Date.now()}`, speaker: '듣는 중', text: '음성 인식 중입니다', type: 'partial' }]);
      }
    } catch (e: any) {
      setRecording(false); Sound.removeRecordBackListener(); Sound.stopRecorder().catch(() => {});
      setTurns(p => p.filter(t => t.type !== 'partial'));
      Alert.alert('오류', e?.response?.data?.message ?? e?.message ?? '문제가 발생했습니다.');
    } finally { setAnalyzing(false); }
  };

  const ok    = insights.filter(i => i.kind === 'success').length;
  const risk  = insights.filter(i => i.kind === 'risk').length;
  const solo  = insights.filter(i => !i.turnId);
  const final = turns.filter(t => t.type === 'final').length;
  const busy  = ending || recording || analyzing;

  return (
    <SafeAreaView style={s.safe} edges={['top']}>

      {/* ── Top bar ── */}
      <View style={s.topBar}>
        <TouchableOpacity style={s.closeBtn} onPress={() => finish(false)} disabled={ending} activeOpacity={0.6}>
          <X size={17} color={C.ink70} strokeWidth={2.5} />
        </TouchableOpacity>

        <View style={s.timerRow}>
          <View style={[s.timerDot, recording && s.timerDotRec]} />
          <Text style={s.timerText}>{fmt(duration)}</Text>
        </View>

        <TouchableOpacity style={s.muteBtn} onPress={() => setMuted(m => !m)} activeOpacity={0.6}>
          {muted
            ? <VolumeX size={17} color={C.ink40} strokeWidth={2} />
            : <Volume2 size={17} color={C.ink70} strokeWidth={2} />}
        </TouchableOpacity>
      </View>

      {/* ── Session info strip ── */}
      <View style={s.strip}>
        <View style={[s.avatarDot, { backgroundColor: avatar?.avatar_bg ?? '#555' }]}>
          <Icon name={(avatar?.icon ?? 'user') as IconName} size={15} color="#FFF" />
        </View>
        <Text style={s.stripName}>{avatar?.name_ko ?? '아바타'}</Text>
        <Text style={s.stripDivider}>·</Text>
        <Text style={s.stripStatus}>
          {analyzing ? '분석 중' : recording ? '녹음 중' : '대기'}
        </Text>
        {(ok > 0 || risk > 0) && (
          <>
            <Text style={s.stripDivider}>·</Text>
            {ok > 0   && <Text style={[s.stripCount, { color: C.ok }]}>✓ {ok}</Text>}
            {risk > 0 && <Text style={[s.stripCount, { color: C.risk }]}>⚠ {risk}</Text>}
          </>
        )}
      </View>

      {/* ── Transcript ── */}
      <View style={s.feed}>
        <View style={s.feedHeader}>
          <Text style={s.feedLabel}>대화</Text>
          {final > 0 && <Text style={s.feedCount}>{final}</Text>}
        </View>

        <ScrollView
          ref={scrollRef}
          style={s.scroll}
          contentContainerStyle={s.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {turns.length === 0
            ? <Empty analyzing={analyzing} />
            : turns.map(turn => (
                <Turn
                  key={turn.id} turn={turn}
                  avatarName={avatar?.name_ko}
                  insight={insights.find(i => i.turnId === turn.id)}
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
        {recording && <Waveform active />}

        <View style={s.dockInner}>
          {/* Avatar chip */}
          <View style={[s.avatarChip, { backgroundColor: avatar?.avatar_bg ?? '#555' }]}>
            <Icon name={(avatar?.icon ?? 'user') as IconName} size={15} color="#FFF" />
          </View>

          {/* Mic */}
          <View style={s.micWrap}>
            {recording && (
              <Animated.View style={[s.ripple, {
                transform: [{ scale: rippleScale }], opacity: rippleOpacity,
              }]} />
            )}
            <TouchableOpacity
              style={[s.mic, recording && s.micRec, analyzing && s.micBusy]}
              onPress={onMic} activeOpacity={0.8}
              disabled={ending || analyzing}
            >
              {analyzing
                ? <Mic size={24} color="rgba(255,255,255,0.3)" strokeWidth={2} />
                : recording
                  ? <MicOff size={24} color="#FFF" strokeWidth={2.3} />
                  : <Mic size={24} color="#FFF" strokeWidth={2.3} />}
            </TouchableOpacity>
          </View>

          {/* Mute chip */}
          <TouchableOpacity style={s.muteChip} onPress={() => setMuted(m => !m)} activeOpacity={0.6}>
            {muted
              ? <VolumeX size={15} color={C.ink40} strokeWidth={2} />
              : <Volume2 size={15} color={C.ink70} strokeWidth={2} />}
          </TouchableOpacity>
        </View>

        <Text style={s.micHint}>
          {analyzing ? '분석 중입니다...' : recording ? '탭하여 중지 및 분석' : '탭하여 녹음 시작'}
        </Text>

        <TouchableOpacity
          style={[s.endBtn, busy && s.endBtnOff]}
          onPress={() => finish(true)}
          disabled={busy} activeOpacity={0.85}
        >
          <Text style={[s.endText, busy && s.endTextOff]}>
            {ending ? '종료 중...' : '세션 종료 · 피드백 보기'}
          </Text>
          {!busy && <ArrowRight size={15} color="#FFFFFF" strokeWidth={2.5} />}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.white },

  // Top bar
  topBar: {
    flexDirection: 'row', alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20, paddingVertical: 12,
  },
  closeBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: C.paper,
    borderWidth: 1, borderColor: C.ink10,
    alignItems: 'center', justifyContent: 'center',
  },
  timerRow: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  timerDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: C.ink20 },
  timerDotRec: { backgroundColor: C.recRed },
  timerText: { fontSize: 16, fontWeight: '700', color: C.ink100, letterSpacing: 0.5 },
  muteBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: C.paper,
    borderWidth: 1, borderColor: C.ink10,
    alignItems: 'center', justifyContent: 'center',
  },

  // Strip
  strip: {
    flexDirection: 'row', alignItems: 'center',
    paddingHorizontal: 20, paddingBottom: 14,
    gap: 6,
  },
  avatarDot: {
    width: 24, height: 24, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
  },
  stripName: { fontSize: 13, fontWeight: '600', color: C.ink100 },
  stripDivider: { fontSize: 13, color: C.ink20 },
  stripStatus: { fontSize: 13, color: C.ink70 },
  stripCount: { fontSize: 13, fontWeight: '600' },

  // Feed
  feed: { flex: 1, paddingHorizontal: 20 },
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
  scrollContent: { gap: 2, paddingBottom: 8 },
  soloWrap: { marginTop: 8, gap: 2 },

  // Dock
  dock: {
    backgroundColor: C.white,
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 30,
    borderTopWidth: 1,
    borderTopColor: C.ink10,
    gap: 12,
  },
  dockInner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  avatarChip: {
    width: 40, height: 40, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
  },
  micWrap: { width: 80, height: 80, alignItems: 'center', justifyContent: 'center' },
  ripple: {
    position: 'absolute',
    width: 70, height: 70, borderRadius: 35,
    backgroundColor: C.recRed,
  },
  mic: {
    width: 64, height: 64, borderRadius: 32,
    backgroundColor: C.ink100,
    alignItems: 'center', justifyContent: 'center',
  },
  micRec: { backgroundColor: C.recRed },
  micBusy: { backgroundColor: C.ink40 },
  muteChip: {
    width: 40, height: 40, borderRadius: 12,
    backgroundColor: C.canvas,
    borderWidth: 1, borderColor: C.ink10,
    alignItems: 'center', justifyContent: 'center',
  },
  micHint: {
    textAlign: 'center', fontSize: 13,
    color: C.ink70, fontWeight: '500',
  },
  endBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: 8, paddingVertical: 15, borderRadius: 14,
    backgroundColor: '#6C3BFF',
    shadowColor: '#6C3BFF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  endBtnOff: {
    backgroundColor: C.ink10,
    shadowOpacity: 0,
    elevation: 0,
  },
  endText: { fontSize: 15, fontWeight: '700', color: '#FFFFFF' },
  endTextOff: { color: C.ink40 },
});

// Waveform
const wv = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', height: 20, gap: 3 },
  bar: { width: 2.5, height: 16, borderRadius: 1.5 },
});

// Turn
const tn = StyleSheet.create({
  // Outer row — controls which side the bubble sits on
  row: {
    paddingVertical: 6,
  },
  rowUser: { alignItems: 'flex-end' },
  rowPartner: { alignItems: 'flex-start' },

  // Column holds label + bubble, capped at 80% width
  col: { maxWidth: '80%' },
  colUser: { alignItems: 'flex-end' },
  colPartner: { alignItems: 'flex-start' },

  // Speaker label row
  labelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginBottom: 4,
    paddingHorizontal: 2,
  },
  dot: { width: 5, height: 5, borderRadius: 2.5 },
  speaker: { fontSize: 10, fontWeight: '700', color: C.ink40, letterSpacing: 0.5, textTransform: 'uppercase' },
  speakerUser: { color: '#6C3BFF' },

  // Bubbles
  bubble: {
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  bubbleUser: {
    backgroundColor: '#EDEAFC',
    borderBottomRightRadius: 4,
  },
  bubblePartner: {
    backgroundColor: C.paper,
    borderWidth: 1,
    borderColor: C.ink10,
    borderBottomLeftRadius: 4,
  },
  bubbleLive: { opacity: 0.7 },

  // Text
  text: { fontSize: 15, lineHeight: 22 },
  textUser: { color: C.ink100 },
  textPartner: { color: C.ink100 },
  textLive: { color: C.ink70 },

  // Insight offset
  insightWrap: { marginTop: 6, maxWidth: '80%' },
  insightUser: { alignSelf: 'flex-end' },
  insightPartner: { alignSelf: 'flex-start' },
});

// Insight
const ins = StyleSheet.create({
  wrap: {
    borderLeftWidth: 2.5,
    paddingLeft: 12,
    paddingVertical: 2,
    gap: 3,
  },
  label: { fontSize: 10, fontWeight: '800', letterSpacing: 0.8, textTransform: 'uppercase' },
  msg: { fontSize: 13, color: C.ink70, lineHeight: 19 },
  sugg: { fontSize: 13, fontWeight: '600', lineHeight: 19 },
});

// Empty
const em = StyleSheet.create({
  wrap: { alignItems: 'center', paddingVertical: 60, gap: 14 },
  ring: {
    position: 'absolute', top: 42,
    width: 72, height: 72, borderRadius: 36,
    borderWidth: 1, borderColor: C.ink10,
  },
  circle: {
    width: 52, height: 52, borderRadius: 26,
    borderWidth: 1, borderColor: C.ink10,
    backgroundColor: C.paper,
    alignItems: 'center', justifyContent: 'center',
    marginBottom: 4,
  },
  title: { fontSize: 16, fontWeight: '700', color: C.ink100 },
  sub: { fontSize: 13, color: C.ink70, textAlign: 'center', lineHeight: 21 },
});
