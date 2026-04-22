import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput,
  KeyboardAvoidingView, Platform, ActivityIndicator, Animated,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import {
  ChevronLeft, X, Send, Smile, Meh, Frown, Angry, Heart,
  CheckCircle, AlertCircle, Lightbulb,
} from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SpeechLevelBadge, Icon } from '../components';

const AI_SERVER = 'http://10.0.2.2:8000';

type HistoryRole = 'user' | 'assistant';
interface HistoryItem { role: HistoryRole; content: string; }

interface Correction {
  original:    string;
  corrected:   string;
  explanation: string;
  severity:    'error' | 'warning' | 'info';
  tip?:        string;
  type?:       string;
}

interface NaturalAlternative {
  expression:  string;
  explanation: string;
}

interface SpeechAnalysis {
  detected_speech_level: string;
  detected_speech_level_code?: string;
  detected_speech_confidence?: number;
  speech_level_correct:  boolean;
  expected_speech_level: string;
  expected_speech_level_code?: string;
  input_kind?: string;
  verdict?: string;
  has_errors:            boolean;
  accuracy_score:        number | null;
  scorable?:             boolean;
  corrections:           Correction[];
  natural_alternatives:  NaturalAlternative[];
  encouragement?:        string;
  summary?:              string;
}

interface Message {
  id:       string;
  text:     string;
  sender:   'user' | 'ai';
  feedback?: SpeechAnalysis;
}

const getMoodConfig = (mood: number) => {
  if (mood >= 80) return { icon: Heart,  color: '#E91E63', label: '아주 좋아요!' };
  if (mood >= 60) return { icon: Smile,  color: '#4CAF50', label: '좋아요'       };
  if (mood >= 40) return { icon: Meh,    color: '#F4A261', label: '그저 그래요'  };
  if (mood >= 20) return { icon: Frown,  color: '#FF9800', label: '조금 힘들어요' };
  return           { icon: Angry,  color: '#E53935', label: '화나요!'       };
};

const buildHistoryFromMessages = (messages: Message[]): HistoryItem[] =>
  messages
    .map(m => ({ role: (m.sender === 'user' ? 'user' : 'assistant') as HistoryRole, content: m.text }))
    .filter(m => m.content.trim().length > 0);

const LEVEL_LABELS: Record<string, string> = {
  formal: '합쇼체',
  polite: '해요체',
  informal: '반말',
};

const LEVEL_EXAMPLES: Record<string, string> = {
  formal: '안녕하십니까. 만나서 반갑습니다.',
  polite: '안녕하세요. 만나서 반가워요.',
  informal: '안녕. 만나서 반가워.',
};

const SPEECH_LEVEL_TERMS: Record<string, { code: string; label: string }> = {
  formal: { code: 'formal', label: '합쇼체' },
  'formal speech': { code: 'formal', label: '합쇼체' },
  합쇼체: { code: 'formal', label: '합쇼체' },
  격식체: { code: 'formal', label: '합쇼체' },
  격식: { code: 'formal', label: '합쇼체' },
  격식적: { code: 'formal', label: '합쇼체' },
  합니다체: { code: 'formal', label: '합쇼체' },
  polite: { code: 'polite', label: '해요체' },
  존댓말: { code: 'polite', label: '해요체' },
  존대: { code: 'polite', label: '해요체' },
  높임말: { code: 'polite', label: '해요체' },
  공손: { code: 'polite', label: '해요체' },
  '공손한 말투': { code: 'polite', label: '해요체' },
  공손한말투: { code: 'polite', label: '해요체' },
  해요체: { code: 'polite', label: '해요체' },
  informal: { code: 'informal', label: '반말' },
  casual: { code: 'informal', label: '반말' },
  비격식: { code: 'informal', label: '반말' },
  편한말: { code: 'informal', label: '반말' },
  '편한 말': { code: 'informal', label: '반말' },
  반말: { code: 'informal', label: '반말' },
};

const normalizeInputToken = (text: string) =>
  text
    .trim()
    .toLowerCase()
    .replace(/[.,!?…。？！]+$/g, '')
    .replace(/\s+/g, ' ');

const normalizeExpectedLevelCode = (level?: string) => {
  if (!level) return '';
  const normalized = String(level).trim().toLowerCase();
  if (LEVEL_LABELS[normalized]) return normalized;
  const compact = normalized.replace(/\s+/g, '');
  return SPEECH_LEVEL_TERMS[normalized]?.code || SPEECH_LEVEL_TERMS[compact]?.code || '';
};

const detectLikelySpeechLevel = (text: string) => {
  const compact = text.trim().replace(/\s+/g, ' ');
  if (!/[가-힣]/.test(compact)) return null;

  if (/(안녕하십니까|감사합니다|죄송합니다|부탁드립니다|입니다|합니다|했습니다|하겠습니다|습니까|십니까|니다[.!?…。！？”"')\]\s]*$)/.test(compact)) {
    return 'formal';
  }

  if (/(안녕하세요|고마워요|감사해요|미안해요|죄송해요|반가워요|괜찮아요|좋아요|있어요|없어요|이에요|예요|세요|해요|아요|어요|나요|죠|지요|네요|군요|까요|요[.!?…。！？”"')\]\s]*$)/.test(compact)) {
    return 'polite';
  }

  if (/(^|\s)(안녕|응|아니|고마워|미안해|반가워|괜찮아|좋아|있어|없어|뭐해|가자|갈래|먹어|마셔|봐|해|자)([.!?…。！？”"')\]\s]|$)/.test(compact)
      || /(어떻게 지내|뭐 해|뭐해|잘 지내|했어|할래|줄래|니\?|냐\?|야[.!?…。！？”"')\]\s]*$)/.test(compact)) {
    return 'informal';
  }

  return null;
};

const COMMON_TYPO_FIXES: Array<{ pattern: RegExp; original: string; corrected: string; explanation: string }> = [
  { pattern: /안녕하새요/, original: '안녕하새요', corrected: '안녕하세요', explanation: "'안녕하새요'는 오타이고, 표준 표현은 '안녕하세요'입니다." },
  { pattern: /안녕하세여/, original: '안녕하세여', corrected: '안녕하세요', explanation: "'안녕하세여'는 채팅식 표기이고, 연습 문장에서는 '안녕하세요'가 자연스럽습니다." },
  { pattern: /감사함니다/, original: '감사함니다', corrected: '감사합니다', explanation: "'감사함니다'가 아니라 '감사합니다'로 적는 것이 맞습니다." },
  { pattern: /어떻개/, original: '어떻개', corrected: '어떻게', explanation: "'어떻개'는 오타이고, '어떻게'가 맞습니다." },
  { pattern: /어떡게/, original: '어떡게', corrected: '어떻게', explanation: "'어떡게'는 오타이고, '어떻게'가 맞습니다." },
  { pattern: /괜찬/, original: '괜찬', corrected: '괜찮', explanation: "'괜찬'보다 '괜찮'이 맞는 표기입니다." },
  { pattern: /할께/, original: '할께', corrected: '할게', explanation: "미래의 의지를 말할 때는 '할게'가 자연스럽고 맞는 표기입니다." },
  { pattern: /되요/, original: '되요', corrected: '돼요', explanation: "'되요'보다 '돼요'가 맞는 표기입니다." },
  { pattern: /됬/, original: '됬', corrected: '됐', explanation: "'됬'은 잘못된 표기이고, '됐'이 맞습니다." },
  { pattern: /오랫만/, original: '오랫만', corrected: '오랜만', explanation: "'오랫만'이 아니라 '오랜만'이 맞는 표기입니다." },
  { pattern: /몇일/, original: '몇일', corrected: '며칠', explanation: "'몇일'보다 '며칠'이 표준어입니다." },
  { pattern: /왠만/, original: '왠만', corrected: '웬만', explanation: "'왠만'이 아니라 '웬만'이 맞습니다." },
  { pattern: /설겆이/, original: '설겆이', corrected: '설거지', explanation: "'설겆이'보다 '설거지'가 표준어입니다." },
  { pattern: /반가워여/, original: '반가워여', corrected: '반가워요', explanation: "'반가워여'는 채팅식 표기이고, 연습 문장에서는 '반가워요'가 자연스럽습니다." },
  { pattern: /고마워여/, original: '고마워여', corrected: '고마워요', explanation: "'고마워여'는 채팅식 표기이고, 연습 문장에서는 '고마워요'가 자연스럽습니다." },
  { pattern: /미안해여/, original: '미안해여', corrected: '미안해요', explanation: "'미안해여'는 채팅식 표기이고, 연습 문장에서는 '미안해요'가 자연스럽습니다." },
];

const getLocalTypoCorrections = (text: string): Correction[] =>
  COMMON_TYPO_FIXES
    .filter(item => item.pattern.test(text))
    .map(item => ({
      original: item.original,
      corrected: item.corrected,
      explanation: item.explanation,
      severity: 'error',
      type: 'spelling',
    }));

const applyLocalSpellingFixes = (text: string) =>
  COMMON_TYPO_FIXES.reduce((result, item) => result.replace(item.pattern, item.corrected), text);

const replaceAll = (text: string, pairs: Array<[RegExp, string]>) =>
  pairs.reduce((result, [pattern, replacement]) => result.replace(pattern, replacement), text);

const makeSpeechLevelSuggestion = (text: string, expectedCode: string) => {
  const spellingFixedText = applyLocalSpellingFixes(text);

  if (expectedCode === 'informal') {
    const changed = replaceAll(spellingFixedText, [
      [/안녕하십니까|안녕하세요/g, '안녕'],
      [/만나서 반갑습니다|만나서 반가워요/g, '만나서 반가워'],
      [/감사합니다|고마워요/g, '고마워'],
      [/죄송합니다|죄송해요|미안해요/g, '미안해'],
      [/어떻게 지내세요[?？]?|어떻게 지내요[?？]?/g, '어떻게 지내?'],
      [/이에요/g, '이야'],
      [/예요/g, '야'],
      [/입니다/g, '이야'],
      [/([가-힣])요([.!?…。！]?)/g, '$1$2'],
      [/습니다/g, '어'],
      [/니다/g, '야'],
    ]).trim();
    return changed && changed !== text ? changed : LEVEL_EXAMPLES.informal;
  }

  if (expectedCode === 'formal') {
    const changed = replaceAll(spellingFixedText, [
      [/안녕하세요|안녕/g, '안녕하십니까'],
      [/만나서 반가워요|만나서 반가워/g, '만나서 반갑습니다'],
      [/고마워요|고마워/g, '감사합니다'],
      [/미안해요|미안해/g, '죄송합니다'],
      [/어떻게 지내세요[?？]?|어떻게 지내요[?？]?|어떻게 지내[?？]?/g, '어떻게 지내십니까?'],
      [/이에요|예요/g, '입니다'],
    ]).trim();
    return changed && changed !== text ? changed : LEVEL_EXAMPLES.formal;
  }

  const changed = replaceAll(spellingFixedText, [
    [/안녕하십니까|안녕/g, '안녕하세요'],
    [/만나서 반갑습니다|만나서 반가워/g, '만나서 반가워요'],
    [/감사합니다|고마워/g, '고마워요'],
    [/죄송합니다|미안해/g, '미안해요'],
    [/어떻게 지내십니까[?？]?|어떻게 지내[?？]?/g, '어떻게 지내세요?'],
  ]).trim();
  return changed && changed !== text ? changed : LEVEL_EXAMPLES.polite;
};

const buildLocalSpeechMismatch = (text: string, expectedLevel?: string) => {
  const expectedCode = normalizeExpectedLevelCode(expectedLevel);
  if (!expectedCode) return null;

  const spellingFixedText = applyLocalSpellingFixes(text);
  const detectedCode = detectLikelySpeechLevel(spellingFixedText);
  if (!detectedCode || detectedCode === expectedCode) return null;

  const expectedLabel = LEVEL_LABELS[expectedCode];
  const detectedLabel = LEVEL_LABELS[detectedCode];
  const corrected = makeSpeechLevelSuggestion(text, expectedCode);

  return {
    detectedCode,
    expectedCode,
    detectedLabel,
    expectedLabel,
    corrected,
    score: expectedCode === 'formal' && detectedCode === 'polite' ? 75 : 60,
    summary: `추천 말투는 ${expectedLabel}인데, 이 문장은 ${detectedLabel}에 가까워요. ${expectedLabel} 상황에 맞게 문장 끝맺음을 바꿔 주세요.`,
    correction: {
      original: text,
      corrected,
      explanation: `${detectedLabel} 표현이라 현재 상대에게 요구되는 ${expectedLabel}와 맞지 않습니다.`,
      severity: 'warning' as const,
      type: 'speech_level',
      tip: `${expectedLabel} 예시: ${LEVEL_EXAMPLES[expectedCode]}`,
    },
  };
};

const getLocalInputOverride = (text: string) => {
  const normalized = normalizeInputToken(text);
  const compact = normalized.replace(/\s+/g, '');
  const speechTerm = SPEECH_LEVEL_TERMS[normalized] || SPEECH_LEVEL_TERMS[compact];

  if (!speechTerm) return null;

  return {
    input_kind: 'speech_level_term',
    verdict: 'speech_level_term',
    detected_speech_level: speechTerm.label,
    detected_speech_level_code: speechTerm.code,
    summary: `'${text.trim()}'은(는) 말투 이름이라 실제 대화 문장으로 점수를 매기기 어려워요.`,
    natural_alternatives: [
      {
        expression: `${speechTerm.label}로 말해 볼게요.`,
        explanation: '말투 이름만 말하는 것보다 자연스러운 연습 문장입니다.',
      },
    ],
  };
};

const applyLocalFeedbackGuard = (
  text: string,
  feedback: SpeechAnalysis | null,
  expectedLevel?: string,
): SpeechAnalysis | null => {
  const localOverride = getLocalInputOverride(text);
  if (localOverride) {
    return {
      detected_speech_level: localOverride.detected_speech_level,
      detected_speech_level_code: localOverride.detected_speech_level_code,
      speech_level_correct: true,
      expected_speech_level: feedback?.expected_speech_level || '',
      expected_speech_level_code: feedback?.expected_speech_level_code,
      input_kind: localOverride.input_kind,
      verdict: localOverride.verdict,
      has_errors: false,
      accuracy_score: null,
      scorable: false,
      corrections: [],
      natural_alternatives: localOverride.natural_alternatives,
      encouragement: '',
      summary: localOverride.summary,
    };
  }

  const typoCorrections = getLocalTypoCorrections(text);
  const speechMismatch = buildLocalSpeechMismatch(text, expectedLevel);

  if (typoCorrections.length === 0 && !speechMismatch) return feedback;

  const spellingFixedText = applyLocalSpellingFixes(text);
  const fallbackExpectedCode = normalizeExpectedLevelCode(expectedLevel);
  const expectedCode = speechMismatch?.expectedCode || feedback?.expected_speech_level_code || fallbackExpectedCode;
  const detectedCode = speechMismatch?.detectedCode || feedback?.detected_speech_level_code || detectLikelySpeechLevel(text) || '';
  const typoSummary = typoCorrections
    .map(c => `'${c.original}'는 '${c.corrected}'`)
    .join(', ');
  const finalSpeechCorrection: Correction | null = speechMismatch ? {
    original: text,
    corrected: speechMismatch.corrected,
    explanation: typoCorrections.length > 0
      ? `먼저 ${typoSummary}로 고친 뒤, ${speechMismatch.detectedLabel} 표현을 ${speechMismatch.expectedLabel}에 맞게 바꿔야 합니다.`
      : `${speechMismatch.detectedLabel} 표현이라 현재 상대에게 요구되는 ${speechMismatch.expectedLabel}와 맞지 않습니다.`,
    severity: 'warning',
    type: typoCorrections.length > 0 ? 'spelling_speech_level' : 'speech_level',
    tip: `${speechMismatch.expectedLabel} 예시: ${LEVEL_EXAMPLES[speechMismatch.expectedCode]}`,
  } : null;
  const localCorrections = finalSpeechCorrection ? [finalSpeechCorrection] : typoCorrections;
  const localScore = Math.min(
    speechMismatch?.score ?? 100,
    typoCorrections.length > 0 ? 70 : 100,
  );
  const backendScore = feedback?.accuracy_score ?? 100;
  const summary = [
    speechMismatch?.summary,
    typoCorrections.length > 0 ? '오타가 보여서 자연스러운 표기로 고쳐 봤어요.' : '',
  ].filter(Boolean).join(' ');
  const localEncouragement = speechMismatch
    ? '문장 끝맺음만 맞춰도 훨씬 자연스럽게 들려요.'
    : '오타만 고치면 더 자연스럽게 들려요.';

  return {
    detected_speech_level: detectedCode ? LEVEL_LABELS[detectedCode] : feedback?.detected_speech_level || '',
    detected_speech_level_code: detectedCode || feedback?.detected_speech_level_code,
    speech_level_correct: speechMismatch ? false : feedback?.speech_level_correct ?? true,
    expected_speech_level: expectedCode ? LEVEL_LABELS[expectedCode] : feedback?.expected_speech_level || '',
    expected_speech_level_code: expectedCode || feedback?.expected_speech_level_code,
    input_kind: feedback?.input_kind,
    verdict: speechMismatch
      ? typoCorrections.length > 0
        ? 'speech_and_spelling'
        : 'wrong_speech_level'
      : 'spelling',
    has_errors: true,
    accuracy_score: Math.min(backendScore, localScore),
    scorable: true,
    corrections: localCorrections,
    natural_alternatives: speechMismatch
      ? [{ expression: speechMismatch.corrected, explanation: `${speechMismatch.expectedLabel}로 더 자연스럽게 바꾼 최종 문장입니다.` }]
      : spellingFixedText !== text
        ? [{ expression: spellingFixedText, explanation: '오타를 고친 자연스러운 문장입니다.' }]
        : feedback?.natural_alternatives || [],
    encouragement: localEncouragement,
    summary: summary || feedback?.summary || '',
  };
};

const isScorableFeedback = (fb: SpeechAnalysis) =>
  fb.scorable !== false &&
  fb.accuracy_score !== null &&
  fb.accuracy_score !== undefined &&
  fb.verdict !== 'speech_level_term' &&
  fb.input_kind !== 'speech_level_term';

const normalizeSpeechLevelCode = (level: any, explicitCode?: string) => {
  if (explicitCode) return explicitCode;
  if (typeof level === 'object' && level?.code) return String(level.code);
  if (typeof level === 'string') {
    const normalized = level.trim().toLowerCase();
    return LEVEL_LABELS[normalized] ? normalized : '';
  }
  return '';
};

const normalizeSpeechLevelLabel = (level: any, explicitLabel?: string) => {
  if (explicitLabel) return explicitLabel;
  if (typeof level === 'object') {
    const label = level?.label_ko || level?.label || level?.name_ko;
    if (label) return String(label);
    if (level?.code) return LEVEL_LABELS[String(level.code).toLowerCase()] || String(level.code);
  }
  if (typeof level === 'string') {
    const normalized = level.trim().toLowerCase();
    return LEVEL_LABELS[normalized] || level;
  }
  return '';
};

const normalizeConfidence = (level: any, explicitConfidence?: number) => {
  if (typeof explicitConfidence === 'number') return explicitConfidence;
  if (typeof level === 'object' && typeof level?.confidence === 'number') return level.confidence;
  return undefined;
};

const normalizeScore = (score: any) => {
  const parsed = Number(score);
  if (!Number.isFinite(parsed)) return 80;
  return Math.max(0, Math.min(100, Math.round(parsed)));
};

const sendMessageToAI = async (
  text:      string,
  history:   HistoryItem[],
  avatar:    any,
  situation: any,
  user_id:   string,
  expectedSpeechLevel?: string,
) => {
  const res = await fetch(`${AI_SERVER}/api/v1/chat`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_message:         text,
      conversation_history: history,
      avatar: {
        id:                 avatar?.id                 || 'test',
        name_ko:            avatar?.name_ko            || '아바타',
        role:               avatar?.role               || 'friend',
        personality_traits: avatar?.personality_traits || [],
        interests:          avatar?.interests          || [],
        dislikes:           avatar?.dislikes           || [],
      },
      situation: situation?.name_ko || situation?.title || null,
      user_id,
    }),
  });

  if (!res.ok) throw new Error(`AI server error: ${res.status}`);
  const data = await res.json();

  const correction = data.correction;
  const detectedRaw = correction?.detected_speech_level || correction?.detected_level;
  const expectedRaw = correction?.expected_speech_level || correction?.expected_level;
  const speech_analysis: SpeechAnalysis | null = correction ? {
    detected_speech_level: normalizeSpeechLevelLabel(
      detectedRaw,
      correction.detected_speech_level_label || correction.detected_level_label,
    ),
    detected_speech_level_code: normalizeSpeechLevelCode(
      detectedRaw,
      correction.detected_speech_level_code || correction.detected_level_code,
    ),
    detected_speech_confidence: normalizeConfidence(
      detectedRaw,
      correction.detected_speech_level_confidence || correction.detected_confidence,
    ),
    speech_level_correct: correction.speech_level_correct ?? true,
    expected_speech_level: normalizeSpeechLevelLabel(
      expectedRaw,
      correction.expected_speech_level_label || correction.expected_level_label,
    ),
    expected_speech_level_code: normalizeSpeechLevelCode(
      expectedRaw,
      correction.expected_speech_level_code || correction.expected_level_code,
    ),
    input_kind: correction.input_kind || correction.inputKind,
    verdict: correction.verdict,
    has_errors: correction.has_errors ?? false,
    accuracy_score: normalizeScore(correction.accuracy_score),
    scorable: correction.scorable,
    corrections: correction.corrections || [],
    natural_alternatives: correction.natural_alternatives || [],
    encouragement: correction.encouragement || '',
    summary: correction.summary || correction.overall_feedback || '',
  } : null;

  return {
    message:        data.message,
    speech_analysis: applyLocalFeedbackGuard(text, speech_analysis, expectedSpeechLevel),
    mood_change:    data.mood_change    || 0,
    current_mood:   data.current_mood   || 70,
    mood_emoji:     data.mood_emoji     || '😊',
    correct_streak: data.correct_streak || 0,
  };
};

const analyzeSessionWithAI = async (avatar: any, history: HistoryItem[]) => {
  const res = await fetch(`${AI_SERVER}/api/v1/chat/analyze`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ avatar, conversation_history: history }),
  });
  if (!res.ok) throw new Error(`Analyze error: ${res.status}`);
  return res.json();
};

const severityColor = (s: string) =>
  s === 'error' ? '#E53935' : s === 'warning' ? '#F4A261' : '#6C3BFF';

const feedbackTitle = (fb: SpeechAnalysis) => {
  const detected = normalizeSpeechLevelLabel(fb.detected_speech_level);
  const expected = normalizeSpeechLevelLabel(fb.expected_speech_level);

  if (fb.verdict === 'speech_level_term' || fb.input_kind === 'speech_level_term') return '말투 이름만 입력됨';
  if (fb.verdict === 'not_scorable' || fb.scorable === false) return '분석 제외';
  if (fb.verdict === 'speech_and_spelling') return '말투와 오타 수정 필요';
  if (fb.verdict === 'practice_expression') return `${detected || expected || '말투'} 연습 표현`;
  if (fb.verdict === 'fragment') return '표현 조각';
  if (fb.verdict === 'spelling' || fb.corrections.some(c => c.type === 'spelling')) return '오타 수정 필요';
  if (fb.verdict === 'wrong_speech_level') return detected ? `${detected} 사용됨` : '말투 수정 필요';
  if (fb.verdict === 'needs_revision') return '수정이 필요한 표현';
  if (fb.verdict === 'unclear') return '말투를 판단하기 어려워요';

  if (fb.input_kind === 'meta_practice') return `${detected || expected || '말투'} 연습 표현`;
  if (fb.input_kind === 'fragment') return '표현 조각';
  if (fb.input_kind === 'non_korean') return '한국어 표현 아님';

  if (!detected) return fb.expected_speech_level || '말투 분석';
  if (detected.includes('연습 표현') || detected.includes('표현 분석')) {
    return detected;
  }
  if (fb.detected_speech_confidence && fb.detected_speech_confidence < 0.75) {
    return `${detected}에 가까워요`;
  }
  return `${detected} 감지`;
};

export default function ChatScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();

  const avatar           = route.params?.avatar;
  const situation        = route.params?.situation;
  const recommendedLevel = route.params?.recommendedLevel || avatar?.formality_from_user || 'polite';
  const profileName      = route.params?.name     || avatar?.name_ko || '아바타';
  const profileBg        = route.params?.avatarBg || avatar?.avatar_bg || '#FFB6C1';

  const flatListRef = useRef<FlatList>(null);

  const [messages,         setMessages]         = useState<Message[]>([]);
  const [input,            setInput]            = useState('');
  const [loading,          setLoading]          = useState(false);
  const [avatarMood,       setAvatarMood]       = useState(70);
  const [startTime]        = useState(Date.now());
  const [userId,           setUserId]           = useState('test-user-1');
  const [correctStreak,    setCorrectStreak]    = useState(0);
  const [expandedFeedback, setExpandedFeedback] = useState<Record<string, boolean>>({});

  const moodAnim    = useRef(new Animated.Value(70)).current;

  useEffect(() => {
    AsyncStorage.getItem('user_id').then(id => { if (id) setUserId(id); });
  }, []);

  useEffect(() => {
    if (messages.length > 0)
      setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
  }, [messages]);

  useEffect(() => {
    Animated.spring(moodAnim, { toValue: avatarMood, useNativeDriver: false, friction: 8 }).start();
  }, [avatarMood, moodAnim]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const text    = input.trim();
    const userMsg: Message = { id: Date.now().toString(), text, sender: 'user' };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const history: HistoryItem[] = [
        ...buildHistoryFromMessages(messages),
        { role: 'user', content: text },
      ];

      const data = await sendMessageToAI(text, history, avatar, situation, userId, recommendedLevel);
      const aiMsg: Message = { id: (Date.now() + 1).toString(), text: data.message, sender: 'ai' };

      setAvatarMood(data.current_mood);
      setCorrectStreak(data.correct_streak);

      setMessages(prev => {
        const updated = prev.map(m =>
          m.id === userMsg.id ? { ...m, feedback: data.speech_analysis ?? undefined } : m
        );
        return [...updated, aiMsg];
      });

      // 피드백 있으면 항상 펼침
      if (data.speech_analysis) {
        setExpandedFeedback(prev => ({ ...prev, [userMsg.id]: true }));
      }

    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        text: '네, 그렇군요! 더 이야기해주세요.',
        sender: 'ai',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleEndChat = async () => {
    const duration    = Math.floor((Date.now() - startTime) / 1000);
    const durationStr = `${String(Math.floor(duration/60)).padStart(2,'0')}:${String(duration%60).padStart(2,'0')}`;
    const history     = buildHistoryFromMessages(messages);

    const sessionCorrections = messages
      .filter(m => m.sender === 'user' && m.feedback && isScorableFeedback(m.feedback))
      .map(m => ({
        message:        m.text,
        accuracy_score: m.feedback!.accuracy_score,
        has_errors:     m.feedback!.has_errors,
        corrections:    m.feedback!.corrections,
        detected_level: m.feedback!.detected_speech_level,
        encouragement:  m.feedback!.encouragement,
      }));

    const avgScore = sessionCorrections.length > 0
      ? Math.round(sessionCorrections.reduce((s, c) => s + (c.accuracy_score ?? 0), 0) / sessionCorrections.length)
      : 100;

    let sessionReport = null;
    try { sessionReport = await analyzeSessionWithAI(avatar, history); } catch {}

    navigation.navigate('ConversationSummary', {
      avatar, duration: durationStr, situation,
      conversationHistory: history, finalMood: avatarMood,
      sessionReport, sessionCorrections, avgScore,
    });
  };

  // ── 피드백 카드 ───────────────────────────────────────────────
  const renderFeedbackCard = (item: Message) => {
    if (!item.feedback) return null;

    const fb           = item.feedback;
    const expanded     = expandedFeedback[item.id] ?? true;
    const hasError     = fb.has_errors;
    const isScorable   = isScorableFeedback(fb);
    const feedbackColor = hasError ? '#E53935' : isScorable ? '#4CAF50' : '#6C3BFF';
    const alternatives = fb.natural_alternatives || [];
    const hasAlts      = alternatives.length > 0;
    const primaryCorrection = hasError && fb.corrections.length > 0 ? fb.corrections[0] : null;
    const scoreLabel = isScorable ? `${fb.accuracy_score}점` : '분석 제외';

    return (
      <TouchableOpacity
        style={[
          styles.feedbackCard,
          hasError ? styles.feedbackCardError : isScorable ? styles.feedbackCardOk : styles.feedbackCardInfo,
        ]}
        onPress={() => setExpandedFeedback(prev => ({ ...prev, [item.id]: !expanded }))}
        activeOpacity={0.8}
      >
        {/* ── 요약 행 ── */}
        <View style={styles.feedbackSummaryRow}>
          <View style={[
            styles.feedbackIconBadge,
            hasError ? styles.feedbackIconBadgeError : styles.feedbackIconBadgeOk,
          ]}>
            {hasError
              ? <AlertCircle size={15} color="#FFFFFF" />
              : <CheckCircle size={15} color="#FFFFFF" />}
          </View>
          <View style={styles.feedbackTitleBlock}>
            <Text style={[styles.feedbackSummaryText, { color: feedbackColor }]}>
              {feedbackTitle(fb)}
            </Text>
            <Text style={styles.feedbackSubtitle}>
              {hasError ? '아래 교정 문장을 먼저 확인해 보세요' : '자연스러운 표현이에요'}
            </Text>
          </View>
          <View style={[
            styles.feedbackScorePill,
            hasError ? styles.feedbackScorePillError : styles.feedbackScorePillOk,
          ]}>
            <Text style={[
              styles.feedbackScore,
              hasError && styles.feedbackScoreError,
              !isScorable && styles.feedbackScoreMuted,
            ]}>
              {scoreLabel}
            </Text>
          </View>
          <Text style={styles.feedbackExpand}>{expanded ? '▲' : '▼'}</Text>
        </View>

        {expanded && (
          <View style={styles.feedbackDetail}>
            {primaryCorrection && (
              <View style={styles.finalCorrectionPanel}>
                <Text style={styles.finalCorrectionLabel}>추천 교정</Text>
                <View style={styles.finalCorrectionCompare}>
                  <View style={styles.finalOriginalBox}>
                    <Text style={styles.finalBoxLabel}>입력</Text>
                    <Text style={styles.finalOriginalText}>{primaryCorrection.original}</Text>
                  </View>
                  <Text style={styles.finalArrow}>→</Text>
                  <View style={styles.finalFixedBox}>
                    <Text style={styles.finalBoxLabelFixed}>수정</Text>
                    <Text style={styles.finalFixedText}>{primaryCorrection.corrected}</Text>
                  </View>
                </View>
              </View>
            )}

            {fb.summary ? (
              <Text style={styles.feedbackSummaryNote}>{fb.summary}</Text>
            ) : null}

            {/* ── 오류가 없을 때: 이렇게도 말할 수 있어요 우선 표시 ── */}
            {!hasError && hasAlts && (
              <View style={styles.alternativesSection}>
                <View style={styles.alternativesHeader}>
                  <Lightbulb size={14} color="#6C3BFF" />
                  <Text style={styles.alternativesTitle}>이렇게도 말할 수 있어요</Text>
                </View>
                {alternatives.map((alt, i) => (
                  <View key={i} style={[
                    styles.alternativeItem,
                    i < alternatives.length - 1 && styles.alternativeItemBorder,
                  ]}>
                    <Text style={styles.alternativeExpression}>"{alt.expression}"</Text>
                    {alt.explanation ? (
                      <Text style={styles.alternativeExplain}>{alt.explanation}</Text>
                    ) : null}
                  </View>
                ))}
              </View>
            )}

            {/* 격려 메시지 — 대안 없을 때만 표시 */}
            {(!hasAlts || hasError) && fb.encouragement ? (
              <Text style={styles.feedbackEncouragement}>{fb.encouragement}</Text>
            ) : null}

            {/* ── 오류 있을 때: 교정 목록 ── */}
            {hasError && fb.corrections.length > 0 && (
              <View style={styles.correctionList}>
                <Text style={styles.detailSectionTitle}>왜 고쳐야 하나요?</Text>
                {fb.corrections.map((c, i) => (
                  <View key={i} style={[styles.correctionItem, { borderLeftColor: severityColor(c.severity) }]}>
                    <View style={styles.correctionItemHeader}>
                      <Text style={styles.correctionTypeLabel}>
                        {c.type === 'spelling' || c.type === 'spelling_speech_level' ? '오타' : '말투'}
                      </Text>
                      <Text style={styles.correctionSeverityText}>
                        {c.severity === 'error' ? '꼭 수정' : '수정 추천'}
                      </Text>
                    </View>
                    <View style={styles.correctionCompareRow}>
                      <Text style={styles.correctionOriginal}>{c.original}</Text>
                      <Text style={styles.correctionArrow}>→</Text>
                      <Text style={styles.correctionFixed}>{c.corrected}</Text>
                    </View>
                    <Text style={styles.correctionExplain}>{c.explanation}</Text>
                    {c.tip ? <Text style={styles.correctionTip}>Tip: {c.tip}</Text> : null}
                  </View>
                ))}
              </View>
            )}

            {/* 오류 있을 때도 대안 표현 */}
            {hasError && hasAlts && (
              <View style={[styles.alternativesSection, { marginTop: 10 }]}>
                <View style={styles.alternativesHeader}>
                  <Lightbulb size={14} color="#6C3BFF" />
                  <Text style={styles.alternativesTitle}>이렇게도 말할 수 있어요</Text>
                </View>
                {alternatives.map((alt, i) => (
                  <View key={i} style={[
                    styles.alternativeItem,
                    i < alternatives.length - 1 && styles.alternativeItemBorder,
                  ]}>
                    <Text style={styles.alternativeExpression}>"{alt.expression}"</Text>
                    {alt.explanation ? (
                      <Text style={styles.alternativeExplain}>{alt.explanation}</Text>
                    ) : null}
                  </View>
                ))}
              </View>
            )}

          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={styles.messageWrapper}>
      <View style={[styles.bubbleRow, item.sender === 'user' ? styles.bubbleRowUser : styles.bubbleRowAi]}>
        {item.sender === 'ai' && (
          <View style={[styles.bubbleAvatar, { backgroundColor: profileBg }]}>
            <Icon name={avatar?.icon || 'user'} size={16} color="#FFFFFF" />
          </View>
        )}
        <View style={[
          styles.bubble,
          item.sender === 'user' ? styles.bubbleUser : styles.bubbleAi,
          item.feedback?.has_errors && styles.bubbleWarning,
          item.sender === 'user' && item.feedback?.has_errors && styles.bubbleUserWarning,
        ]}>
          <Text style={[styles.bubbleText, item.sender === 'user' && styles.bubbleTextUser]}>
            {item.text}
          </Text>
        </View>
      </View>
      {item.sender === 'user' && item.feedback && renderFeedbackCard(item)}
    </View>
  );

  const moodConfig = getMoodConfig(avatarMood);
  const MoodIcon   = moodConfig.icon;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <ChevronLeft size={24} color="#1A1A2E" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <View style={[styles.headerAvatar, { backgroundColor: profileBg }]}>
            <Icon name={avatar?.icon || 'user'} size={16} color="#FFFFFF" />
          </View>
          <View>
            <Text style={styles.headerName}>{profileName}</Text>
            <Text style={styles.headerSituation}>{situation?.name_ko || '대화'}</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.headerBtn} onPress={handleEndChat}>
          <X size={24} color="#E53935" />
        </TouchableOpacity>
      </View>

      <View style={styles.moodBarContainer}>
        <MoodIcon size={18} color={moodConfig.color} />
        <Text style={[styles.moodLabel, { color: moodConfig.color }]}>{moodConfig.label}</Text>
        <View style={styles.moodBarTrack}>
          <Animated.View style={[styles.moodBarFill, {
            backgroundColor: moodConfig.color,
            width: moodAnim.interpolate({ inputRange: [0,100], outputRange: ['0%','100%'] }),
          }]} />
        </View>
        <Text style={styles.moodPercent}>{avatarMood}%</Text>
        {correctStreak >= 3 && (
          <View style={styles.streakBadge}>
            <Text style={styles.streakText}>🔥 {correctStreak}연속</Text>
          </View>
        )}
      </View>

      <View style={styles.levelBanner}>
        <Text style={styles.levelLabel}>추천 말투:</Text>
        <SpeechLevelBadge level={recommendedLevel} size="small" />
      </View>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.messageList}
          renderItem={renderMessage}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />

        {loading && (
          <View style={styles.loadingRow}>
            <View style={[styles.bubbleAvatar, { backgroundColor: profileBg }]}>
              <Icon name={avatar?.icon || 'user'} size={16} color="#FFFFFF" />
            </View>
            <View style={styles.loadingBubble}>
              <ActivityIndicator size="small" color="#6C3BFF" />
            </View>
          </View>
        )}

        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            placeholder="메시지를 입력하세요..."
            placeholderTextColor="#C0C0D0"
            value={input}
            onChangeText={setInput}
            returnKeyType="send"
            onSubmitEditing={handleSend}
            editable={!loading}
          />
          <TouchableOpacity
            style={[styles.sendBtn, (loading || !input.trim()) && styles.sendBtnDisabled]}
            onPress={handleSend}
            disabled={loading || !input.trim()}
          >
            <Send size={20} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },

  header:          { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#F0F0F8', backgroundColor: '#FFFFFF' },
  headerBtn:       { width: 40, alignItems: 'center' },
  headerCenter:    { flexDirection: 'row', alignItems: 'center', gap: 10 },
  headerAvatar:    { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  headerName:      { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },
  headerSituation: { fontSize: 11, color: '#6C6C80' },

  moodBarContainer: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#F7F7FB', paddingVertical: 10, paddingHorizontal: 16 },
  moodLabel:        { fontSize: 12, fontWeight: '600', width: 80 },
  moodBarTrack:     { flex: 1, height: 8, backgroundColor: '#E2E2EC', borderRadius: 4, overflow: 'hidden' },
  moodBarFill:      { height: '100%', borderRadius: 4 },
  moodPercent:      { fontSize: 12, fontWeight: '600', color: '#6C6C80', width: 36, textAlign: 'right' },
  streakBadge:      { backgroundColor: '#FFF3E0', borderRadius: 10, paddingHorizontal: 8, paddingVertical: 2 },
  streakText:       { fontSize: 11, fontWeight: '600', color: '#E65100' },

  levelBanner: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 8, backgroundColor: '#FFFFFF', borderBottomWidth: 1, borderBottomColor: '#F0F0F8', gap: 8 },
  levelLabel:  { fontSize: 12, color: '#6C6C80' },

  messageList:    { padding: 16, gap: 4 },
  messageWrapper: { marginBottom: 12 },

  bubbleRow:      { flexDirection: 'row', alignItems: 'flex-end' },
  bubbleRowAi:    { justifyContent: 'flex-start' },
  bubbleRowUser:  { justifyContent: 'flex-end' },
  bubbleAvatar:   { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', marginRight: 8 },
  bubble:         { maxWidth: '75%', paddingHorizontal: 14, paddingVertical: 10, borderRadius: 18 },
  bubbleAi:       { backgroundColor: '#F5F5FA', borderBottomLeftRadius: 4 },
  bubbleUser:     { backgroundColor: '#6C3BFF', borderBottomRightRadius: 4 },
  bubbleWarning:  { borderWidth: 1.5, borderColor: '#E35D3E' },
  bubbleUserWarning: { backgroundColor: '#CF493C' },
  bubbleText:     { fontSize: 14, color: '#1A1A2E', lineHeight: 20 },
  bubbleTextUser: { color: '#FFFFFF' },

  feedbackCard:      { marginTop: 8, marginLeft: 22, marginRight: 8, borderRadius: 20, padding: 13, borderWidth: 1.5, shadowColor: '#2B1B12', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.08, shadowRadius: 18, elevation: 3 },
  feedbackCardOk:    { backgroundColor: '#F2FFF6', borderColor: '#9BD6AA' },
  feedbackCardError: { backgroundColor: '#FFF7ED', borderColor: '#F08A62' },
  feedbackCardInfo:  { backgroundColor: '#F5F2FF', borderColor: '#C8B4F8' },

  feedbackSummaryRow:  { flexDirection: 'row', alignItems: 'center', gap: 9 },
  feedbackIconBadge:   { width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  feedbackIconBadgeError: { backgroundColor: '#E35D3E' },
  feedbackIconBadgeOk:    { backgroundColor: '#42A66B' },
  feedbackTitleBlock:  { flex: 1 },
  feedbackSummaryText: { fontSize: 14, fontWeight: '900', letterSpacing: -0.2 },
  feedbackSubtitle:    { marginTop: 2, fontSize: 11, fontWeight: '600', color: '#8A7D6A' },
  feedbackScorePill:   { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999 },
  feedbackScorePillError: { backgroundColor: '#FFE4D8' },
  feedbackScorePillOk:    { backgroundColor: '#DFF7E8' },
  feedbackScore:       { fontSize: 12, fontWeight: '900', color: '#2E7D32' },
  feedbackScoreError:  { color: '#C83F2E' },
  feedbackScoreMuted:  { color: '#6C6C80' },
  feedbackExpand:      { fontSize: 10, color: '#9F9384', marginLeft: 2 },

  feedbackDetail:        { marginTop: 13, paddingTop: 13, borderTopWidth: 1, borderTopColor: '#F0D8C7' },
  feedbackSummaryNote:   { fontSize: 12, color: '#5B4B3F', lineHeight: 18, marginBottom: 11, fontWeight: '600' },
  feedbackEncouragement: { fontSize: 13, color: '#3D8B6D', lineHeight: 18, fontWeight: '700' },

  finalCorrectionPanel: { backgroundColor: '#FFFFFF', borderRadius: 17, padding: 13, marginBottom: 11, borderWidth: 1, borderColor: '#F0D3BF' },
  finalCorrectionLabel: { fontSize: 11, fontWeight: '900', color: '#C83F2E', marginBottom: 9, letterSpacing: 0.4 },
  finalCorrectionCompare: { flexDirection: 'row', alignItems: 'stretch', gap: 8 },
  finalOriginalBox: { flex: 1, borderRadius: 13, padding: 10, backgroundColor: '#FFF0EC', borderWidth: 1, borderColor: '#FFD2C4' },
  finalFixedBox: { flex: 1, borderRadius: 13, padding: 10, backgroundColor: '#ECFFF3', borderWidth: 1, borderColor: '#BDE8C8' },
  finalBoxLabel: { fontSize: 10, fontWeight: '800', color: '#C83F2E', marginBottom: 4 },
  finalBoxLabelFixed: { fontSize: 10, fontWeight: '800', color: '#2E7D32', marginBottom: 4 },
  finalOriginalText: { fontSize: 15, fontWeight: '800', color: '#B03326', lineHeight: 20 },
  finalFixedText: { fontSize: 15, fontWeight: '900', color: '#1E7A45', lineHeight: 20 },
  finalArrow: { alignSelf: 'center', fontSize: 17, fontWeight: '900', color: '#A78B74' },

  correctionList: { gap: 9, marginBottom: 10 },
  detailSectionTitle: { fontSize: 12, fontWeight: '900', color: '#3F3027', marginBottom: 1 },
  correctionItem: { borderLeftWidth: 4, paddingLeft: 11, paddingVertical: 9, paddingRight: 9, backgroundColor: 'rgba(255,255,255,0.72)', borderRadius: 13 },
  correctionItemHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 7 },
  correctionTypeLabel: { fontSize: 10, fontWeight: '900', color: '#6C3BFF', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 999, backgroundColor: '#F0ECFF' },
  correctionSeverityText: { fontSize: 10, fontWeight: '800', color: '#A85A32' },
  correctionCompareRow:  { flexDirection: 'row', alignItems: 'center', gap: 7, flexWrap: 'wrap', marginBottom: 5 },
  correctionOriginal: { fontSize: 13, color: '#C83F2E', textDecorationLine: 'line-through', fontWeight: '700' },
  correctionArrow:    { fontSize: 13, color: '#9A8D7A', fontWeight: '900' },
  correctionFixed:    { fontSize: 14, color: '#1E7A45', fontWeight: '900' },
  correctionExplain:  { fontSize: 12, color: '#65584B', lineHeight: 18 },
  correctionTip:      { fontSize: 11, color: '#6C3BFF', marginTop: 5, fontWeight: '700' },

  alternativesSection:   { backgroundColor: '#F0ECFF', borderRadius: 14, padding: 12 },
  alternativesHeader:    { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 10 },
  alternativesTitle:     { fontSize: 12, fontWeight: '700', color: '#6C3BFF' },
  alternativeItem:       { paddingBottom: 8 },
  alternativeItemBorder: { borderBottomWidth: 1, borderBottomColor: '#DDD6FF', marginBottom: 8 },
  alternativeExpression: { fontSize: 15, fontWeight: '700', color: '#3D1F8D', marginBottom: 2 },
  alternativeExplain:    { fontSize: 11, color: '#7B6FB5', lineHeight: 16 },

  loadingRow:    { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 16, paddingBottom: 8 },
  loadingBubble: { backgroundColor: '#F5F5FA', borderRadius: 18, paddingHorizontal: 20, paddingVertical: 12 },

  inputBar:        { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12, borderTopWidth: 1, borderTopColor: '#F0F0F8', backgroundColor: '#FFFFFF', gap: 10 },
  input:           { flex: 1, backgroundColor: '#F5F5FA', borderRadius: 24, paddingHorizontal: 16, paddingVertical: 10, fontSize: 14, color: '#1A1A2E' },
  sendBtn:         { width: 44, height: 44, borderRadius: 22, backgroundColor: '#6C3BFF', alignItems: 'center', justifyContent: 'center' },
  sendBtnDisabled: { opacity: 0.5 },
});
