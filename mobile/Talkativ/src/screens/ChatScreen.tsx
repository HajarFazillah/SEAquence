import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput,
  KeyboardAvoidingView, Platform, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { ChevronLeft, Send, ChevronDown, AlertCircle, CheckCircle, Lightbulb } from 'lucide-react-native';
import Svg, { Path, Circle, Polygon } from 'react-native-svg';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { SpeechLevelBadge, Icon } from '../components';
import { makePreviewPayload, saveConversationPreview } from '../services/conversationPreview';

const AI_SERVER = 'http://10.0.2.2:8000';

// ─── Types ────────────────────────────────────────────────────────────────────

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
  corrected_message?: string;
  detected_speech_level:      string;
  detected_speech_level_code?: string;
  detected_speech_confidence?: number;
  speech_level_correct:       boolean;
  expected_speech_level:      string;
  expected_speech_level_code?: string;
  input_kind?:  string;
  verdict?:     string;
  has_errors:   boolean;
  accuracy_score: number | null;
  scorable?:    boolean;
  corrections:  Correction[];
  natural_alternatives: NaturalAlternative[];
  encouragement?: string;
  summary?:     string;
}

interface Message {
  id:       string;
  text:     string;
  sender:   'user' | 'ai';
  feedback?: SpeechAnalysis;
}

interface CorrectionContext {
  session_id:                  string;
  expected_speech_level_code:  string;
  expected_speech_level_label: string;
  latest_user_message:         string;
  corrected_user_message:      string;
  latest_feedback: {
    verdict?:                    string;
    has_errors:                  boolean;
    accuracy_score:              number | null;
    detected_speech_level?:      string;
    detected_speech_level_code?: string;
    summary?:                    string;
    corrections:                 Correction[];
  } | null;
  recent_mistakes: Array<{
    message:   string;
    corrected: string;
    verdict?:  string;
    summary?:  string;
  }>;
  response_guidance: string[];
}

// ─── Mood helpers ─────────────────────────────────────────────────────────────

interface MoodState {
  label: string;
  lbrow: string; rbrow: string;
  leye:  string; reye:  string;
  mouth: string;
}

const MOOD_STATES: MoodState[] = [
  { label: '화나요!',      lbrow: 'M18 29 Q24 27 28 29', rbrow: 'M44 29 Q48 27 54 29', leye: 'M19 35 Q23 39 27 35', reye: 'M45 35 Q49 39 53 35', mouth: 'M23 50 Q36 44 49 50' },
  { label: '힘들어요',     lbrow: 'M18 26 Q24 23 28 26', rbrow: 'M44 26 Q48 23 54 26', leye: 'M19 32 Q23 29 27 32', reye: 'M45 32 Q49 29 53 32', mouth: 'M23 48 Q36 44 49 48' },
  { label: '그저 그래요',  lbrow: 'M18 24 Q24 22 28 24', rbrow: 'M44 24 Q48 22 54 24', leye: 'M19 30 Q23 27 27 30', reye: 'M45 30 Q49 27 53 30', mouth: 'M23 46 Q36 46 49 46' },
  { label: '좋아요',       lbrow: 'M18 24 Q24 21 28 24', rbrow: 'M44 24 Q48 21 54 24', leye: 'M19 30 Q23 27 27 30', reye: 'M45 30 Q49 27 53 30', mouth: 'M23 46 Q36 56 49 46' },
  { label: '아주 좋아요!', lbrow: 'M18 22 Q24 17 28 22', rbrow: 'M44 22 Q48 17 54 22', leye: 'M19 29 Q23 24 27 29', reye: 'M45 29 Q49 24 53 29', mouth: 'M21 43 Q36 58 51 43' },
];

const getMoodState = (mood: number): MoodState => {
  if (mood >= 80) return MOOD_STATES[4];
  if (mood >= 60) return MOOD_STATES[3];
  if (mood >= 40) return MOOD_STATES[2];
  if (mood >= 20) return MOOD_STATES[1];
  return MOOD_STATES[0];
};

const moodColor = (mood: number): string => {
  if (mood >= 70) return '#22C55E';
  if (mood >= 40) return '#EAB308';
  return '#FF4D4D';
};

const scoreColor = (score: number | null): string => {
  if (score === null) return '#999';
  if (score >= 70) return '#22C55E';
  if (score >= 40) return '#EAB308';
  return '#FF4D4D';
};

// ─── MoodFace component ───────────────────────────────────────────────────────

const MoodFace = ({ mood }: { mood: number }) => {
  const s = getMoodState(mood);
  const col = '#6C3BFF';
  return (
    <Svg width={52} height={52} viewBox="0 0 72 72">
      <Circle cx={36} cy={36} r={34} fill="rgba(108,59,255,0.12)" />
      <Path d={s.lbrow} stroke={col} strokeWidth={2.2} strokeLinecap="round" fill="none" />
      <Path d={s.rbrow} stroke={col} strokeWidth={2.2} strokeLinecap="round" fill="none" />
      <Path d={s.leye}  stroke={col} strokeWidth={2.5} strokeLinecap="round" fill="none" />
      <Path d={s.reye}  stroke={col} strokeWidth={2.5} strokeLinecap="round" fill="none" />
      <Path d={s.mouth} stroke={col} strokeWidth={2.5} strokeLinecap="round" fill="none" />
    </Svg>
  );
};

// ─── Star streak icon ─────────────────────────────────────────────────────────

const StarIcon = () => (
  <Svg width={11} height={11} viewBox="0 0 10 10">
    <Polygon
      points="5,0.5 6.5,4 10,4 7.3,6.2 8.2,9.8 5,7.8 1.8,9.8 2.7,6.2 0,4 3.5,4"
      fill="#6C3BFF"
    />
  </Svg>
);

// ─── Helpers ──────────────────────────────────────────────────────────────────

const buildHistoryFromMessages = (messages: Message[]): HistoryItem[] =>
  messages
    .map(m => ({ role: (m.sender === 'user' ? 'user' : 'assistant') as HistoryRole, content: m.text }))
    .filter(m => m.content.trim().length > 0);

const buildLatestPreviewPayload = (
  messages: Message[],
  avatar: any,
  situation: any,
  sessionId: string
) => {
  const latestUser = [...messages].reverse().find((message) => message.sender === 'user')?.text;
  const latestAi = [...messages].reverse().find((message) => message.sender === 'ai')?.text;
  const avatarId = String(avatar?.id || avatar?.avatarId || avatar?.name_ko || 'unknown-avatar');

  return makePreviewPayload({
    sessionId,
    avatarId,
    avatarName: avatar?.name_ko,
    situation: situation?.name_ko || situation?.title,
    messageCount: messages.length,
    lastUserMessage: latestUser,
    lastAiMessage: latestAi,
  });
};

// ─── Constants ────────────────────────────────────────────────────────────────

const LEVEL_LABELS: Record<string, string> = {
  formal: '합쇼체', polite: '해요체', informal: '반말',
};

const LEVEL_EXAMPLES: Record<string, string> = {
  formal:   '안녕하십니까. 만나서 반갑습니다.',
  polite:   '안녕하세요. 만나서 반가워요.',
  informal: '안녕. 만나서 반가워.',
};

const DECORATIVE_REPLY_SYMBOLS = /😊|😂|❤️|❤|✨|😍|🥰|😘|💕|💖|💗|💝|💞|💓|😄|😆|😁|😃|🤣|🙂|😉|☺️|☺|🌟|⭐/g;
const BAD_ALT_PATTERNS = [
  /^이렇게도 말할 수 있어요/i,
  /^더 자연스러운 .*표현/i,
  /^원래 문장이 이미 자연스러워/,
  /^변경할 필요가 없/,
];

const SITUATION_CATEGORY_LABELS: Record<string, string> = {
  casual: '일상', service: '서비스', formal: '격식', work: '업무',
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

// ─── Utility functions (unchanged) ───────────────────────────────────────────

const normalizeInputToken = (text: string) =>
  text.trim().toLowerCase().replace(/[.,!?…。？！]+$/g, '').replace(/\s+/g, ' ');

const normalizeExpectedLevelCode = (level?: string) => {
  if (!level) return '';
  const normalized = String(level).trim().toLowerCase();
  if (LEVEL_LABELS[normalized]) return normalized;
  const compact = normalized.replace(/\s+/g, '');
  return SPEECH_LEVEL_TERMS[normalized]?.code || SPEECH_LEVEL_TERMS[compact]?.code || '';
};

const splitTrailingPunctuation = (text: string) => {
  const match = text.match(/([.!?…。？！"')\]\s]*)$/);
  const trailing = match?.[1] || '';
  return { core: text.slice(0, text.length - trailing.length), trailing };
};

const getFinalConsonantIndex = (char: string) => {
  if (!char || char.length !== 1) return -1;
  const code = char.charCodeAt(0);
  if (code < 0xac00 || code > 0xd7a3) return -1;
  return (code - 0xac00) % 28;
};

const hasBatchimBieup = (char: string) => getFinalConsonantIndex(char) === 17;
const removeFinalBieup = (char: string) =>
  hasBatchimBieup(char) ? String.fromCharCode(char.charCodeAt(0) - 17) : char;

const endsWithHapsidaFormal = (text: string) => {
  const { core } = splitTrailingPunctuation(text.trim());
  if (!core) return false;
  if (core.endsWith('읍시다') || core.endsWith('십시다')) return true;
  if (!core.endsWith('시다') || core.length < 3) return false;
  return hasBatchimBieup(core.charAt(core.length - 3));
};

const convertHapsidaToInformal = (text: string) => {
  const { core, trailing } = splitTrailingPunctuation(text.trim());
  if (!core) return null;
  if (core.endsWith('읍시다') && core.length >= 4)
    return `${core.slice(0, -4)}${core.charAt(core.length - 4)}자${trailing}`;
  if (core.endsWith('시다') && core.length >= 3) {
    const lead = core.charAt(core.length - 3);
    if (hasBatchimBieup(lead))
      return `${core.slice(0, -3)}${removeFinalBieup(lead)}자${trailing}`;
  }
  return null;
};

const detectLikelySpeechLevel = (text: string) => {
  const compact = text.trim().replace(/\s+/g, ' ');
  if (!/[가-힣]/.test(compact)) return null;
  if (endsWithHapsidaFormal(compact)) return 'formal';
  if (/(안녕하십니까|감사합니다|죄송합니다|부탁드립니다|입니다|합니다|했습니다|하겠습니다|습니까|십니까|니다[.!?…。！？""')\]\s]*$)/.test(compact)) return 'formal';
  if (/(안녕하세요|고마워요|감사해요|미안해요|죄송해요|반가워요|괜찮아요|좋아요|있어요|없어요|이에요|예요|세요|해요|아요|어요|나요|죠|지요|네요|군요|까요|요[.!?…。！？""')\]\s]*$)/.test(compact)) return 'polite';
  if (/(^|\s)(안녕|응|아니|고마워|미안해|반가워|괜찮아|좋아|있어|없어|뭐해|가자|갈래|먹어|마셔|봐|해|자)([.!?…。！？""')\]\s]|$)/.test(compact)
    || /(어떻게 지내|뭐 해|뭐해|잘 지내|했어|할래|줄래|니\?|냐\?|야[.!?…。！？""')\]\s]*$)/.test(compact)) return 'informal';
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
  { pattern: /한잔/, original: '한잔', corrected: '한 잔', explanation: "'한잔'보다 '한 잔'처럼 띄어 쓰는 것이 자연스럽습니다." },
  { pattern: /두개/, original: '두개', corrected: '두 개', explanation: "'두개'보다 '두 개'처럼 띄어 쓰는 것이 자연스럽습니다." },
  { pattern: /세개/, original: '세개', corrected: '세 개', explanation: "'세개'보다 '세 개'처럼 띄어 쓰는 것이 자연스럽습니다." },
  { pattern: /갑시당/, original: '갑시당', corrected: '갑시다', explanation: "'갑시당'은 장난스러운 채팅식 표기이고, 연습 문장에서는 '갑시다'가 자연스럽습니다." },
  { pattern: /봅시당/, original: '봅시당', corrected: '봅시다', explanation: "'봅시당'은 장난스러운 채팅식 표기이고, 연습 문장에서는 '봅시다'가 자연스럽습니다." },
  { pattern: /합시당/, original: '합시당', corrected: '합시다', explanation: "'합시당'은 장난스러운 채팅식 표기이고, 연습 문장에서는 '합시다'가 자연스럽습니다." },
];

const getLocalTypoCorrections = (text: string): Correction[] =>
  COMMON_TYPO_FIXES.filter(item => item.pattern.test(text)).map(item => ({
    original: item.original, corrected: item.corrected,
    explanation: item.explanation, severity: 'error', type: 'spelling',
  }));

const applyLocalSpellingFixes = (text: string) =>
  COMMON_TYPO_FIXES.reduce((result, item) => result.replace(item.pattern, item.corrected), text);

const replaceAll = (text: string, pairs: Array<[RegExp, string]>) =>
  pairs.reduce((result, [pattern, replacement]) => result.replace(pattern, replacement), text);

const bestEffortInformalToPolite = (text: string) => {
  const trimmed = text.trim();
  if (!trimmed) return trimmed;
  const match = trimmed.match(/([.!?…。？！"')\]\s]*)$/);
  const trailing = match?.[1] || '';
  const core = trailing ? trimmed.slice(0, trimmed.length - trailing.length) : trimmed;

  const replacements: Array<[RegExp, string]> = [
    [/뭐해$/g, '뭐 해요'],
    [/좋아해$/g, '좋아해요'],
    [/싫어해$/g, '싫어해요'],
    [/괜찮아$/g, '괜찮아요'],
    [/좋아$/g, '좋아요'],
    [/싫어$/g, '싫어요'],
    [/있어$/g, '있어요'],
    [/없어$/g, '없어요'],
    [/맞아$/g, '맞아요'],
    [/알아$/g, '알아요'],
    [/몰라$/g, '몰라요'],
    [/해$/g, '해요'],
    [/가$/g, '가요'],
    [/와$/g, '와요'],
    [/봐$/g, '봐요'],
    [/먹어$/g, '먹어요'],
    [/마셔$/g, '마셔요'],
    [/줘$/g, '주세요'],
    [/주라$/g, '주세요'],
    [/주면\s*돼$/g, '주세요'],
    [/이야$/g, '이에요'],
    [/야$/g, '예요'],
  ];

  let converted = core;
  for (const [pattern, replacement] of replacements) {
    const updated = converted.replace(pattern, replacement);
    if (updated !== converted) {
      converted = updated;
      break;
    }
  }

  if (converted === core && !/(요|니다|습니다|세요|까요)$/.test(core)) {
    if (/(어|아|해)$/.test(core)) converted = `${core}요`;
    else if (/(니|냐)$/.test(core)) converted = `${core.slice(0, -1)}나요`;
  }

  return `${converted}${trailing}`.trim();
};

const makeSpeechLevelSuggestion = (text: string, expectedCode: string) => {
  const spellingFixedText = applyLocalSpellingFixes(text);
  if (expectedCode === 'informal') {
    const convertedHapsida = convertHapsidaToInformal(spellingFixedText);
    if (convertedHapsida && convertedHapsida !== text) return convertedHapsida;
    const changed = replaceAll(spellingFixedText, [
      [/안녕하십니까|안녕하세요/g, '안녕'],
      [/만나서 반갑습니다|만나서 반가워요/g, '만나서 반가워'],
      [/감사합니다|고마워요/g, '고마워'],
      [/죄송합니다|죄송해요|미안해요/g, '미안해'],
      [/어떻게 지내세요[?？]?|어떻게 지내요[?？]?/g, '어떻게 지내?'],
      [/이에요/g, '이야'], [/예요/g, '야'], [/입니다/g, '이야'],
      [/([가-힣])요([.!?…。！]?)/g, '$1$2'], [/습니다/g, '어'], [/니다/g, '야'],
    ]).trim();
    return changed && changed !== text ? changed : spellingFixedText;
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
    return changed && changed !== text ? changed : spellingFixedText;
  }
  const changed = replaceAll(spellingFixedText, [
    [/안녕하십니까|안녕/g, '안녕하세요'],
    [/만나서 반갑습니다|만나서 반가워/g, '만나서 반가워요'],
    [/감사합니다|고마워/g, '고마워요'],
    [/죄송합니다|미안해/g, '미안해요'],
    [/어떻게 지내십니까[?？]?|어떻게 지내[?？]?/g, '어떻게 지내세요?'],
  ]).trim();
  const bestEffort = bestEffortInformalToPolite(spellingFixedText);
  if (bestEffort && bestEffort !== text) return bestEffort;
  return changed && changed !== text ? changed : spellingFixedText;
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
    detectedCode, expectedCode, detectedLabel, expectedLabel, corrected,
    score: expectedCode === 'formal' && detectedCode === 'polite' ? 75 : 60,
    summary: `추천 말투는 ${expectedLabel}인데, 이 문장은 ${detectedLabel}에 가까워요. ${expectedLabel} 상황에 맞게 문장 끝맺음을 바꿔 주세요.`,
    correction: {
      original: text, corrected,
      explanation: `${detectedLabel} 표현이라 현재 상대에게 요구되는 ${expectedLabel}와 맞지 않습니다.`,
      severity: 'warning' as const, type: 'speech_level',
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
    input_kind: 'speech_level_term', verdict: 'speech_level_term',
    detected_speech_level: speechTerm.label,
    detected_speech_level_code: speechTerm.code,
    summary: `'${text.trim()}'은(는) 말투 이름이라 실제 대화 문장으로 점수를 매기기 어려워요.`,
    natural_alternatives: [{ expression: `${speechTerm.label}로 말해 볼게요.`, explanation: '말투 이름만 말하는 것보다 자연스러운 연습 문장입니다.' }],
  };
};

const applyLocalFeedbackGuard = (text: string, feedback: SpeechAnalysis | null, expectedLevel?: string): SpeechAnalysis | null => {
  const localOverride = getLocalInputOverride(text);
  if (localOverride) {
    return {
      corrected_message: '',
      detected_speech_level: localOverride.detected_speech_level,
      detected_speech_level_code: localOverride.detected_speech_level_code,
      speech_level_correct: true,
      expected_speech_level: feedback?.expected_speech_level || '',
      expected_speech_level_code: feedback?.expected_speech_level_code,
      input_kind: localOverride.input_kind, verdict: localOverride.verdict,
      has_errors: false, accuracy_score: null, scorable: false,
      corrections: [], natural_alternatives: localOverride.natural_alternatives,
      encouragement: '', summary: localOverride.summary,
    };
  }
  const typoCorrections = getLocalTypoCorrections(text);
  const shouldTrustBackendSpeech =
    Boolean(feedback)
    && feedback?.input_kind !== 'speech_level_term'
    && feedback?.verdict !== 'speech_level_term';
  const speechMismatch = shouldTrustBackendSpeech ? null : buildLocalSpeechMismatch(text, expectedLevel);
  if (typoCorrections.length === 0 && !speechMismatch) return feedback;
  if (feedback && shouldTrustBackendSpeech) {
    if (typoCorrections.length === 0) return feedback;
    const existingTypoKeys = new Set(
      (feedback.corrections || [])
        .filter(c => c.type === 'spelling')
        .map(c => `${c.original}=>${c.corrected}`),
    );
    const missingTypos = typoCorrections.filter(
      c => !existingTypoKeys.has(`${c.original}=>${c.corrected}`),
    );
    if (missingTypos.length === 0) return feedback;

    const mergedCorrections = [...feedback.corrections, ...missingTypos];
    const mergedAlternatives = feedback.natural_alternatives?.length > 0
      ? feedback.natural_alternatives
      : [{ expression: applyLocalSpellingFixes(text), explanation: '오타를 고친 자연스러운 문장입니다.' }];

    return {
      ...feedback,
      corrected_message: feedback.corrected_message || applyLocalSpellingFixes(text),
      has_errors: true,
      verdict: feedback.speech_level_correct === false ? (feedback.verdict || 'wrong_speech_level') : 'spelling',
      accuracy_score: Math.min(feedback.accuracy_score ?? 100, 70),
      corrections: mergedCorrections,
      natural_alternatives: mergedAlternatives,
      summary: feedback.summary || '오타를 고치면 더 자연스러워요.',
      encouragement: feedback.encouragement || '오타만 다듬어도 훨씬 자연스럽게 들려요.',
    };
  }
  const spellingFixedText = applyLocalSpellingFixes(text);
  const fallbackExpectedCode = normalizeExpectedLevelCode(expectedLevel);
  const expectedCode = speechMismatch?.expectedCode || feedback?.expected_speech_level_code || fallbackExpectedCode;
  const detectedCode = speechMismatch?.detectedCode || feedback?.detected_speech_level_code || detectLikelySpeechLevel(text) || '';
  const typoSummary = typoCorrections.map(c => `'${c.original}'는 '${c.corrected}'`).join(', ');
  const finalSpeechCorrection: Correction | null = speechMismatch ? {
    original: text, corrected: speechMismatch.corrected,
    explanation: typoCorrections.length > 0
      ? `먼저 ${typoSummary}로 고친 뒤, ${speechMismatch.detectedLabel} 표현을 ${speechMismatch.expectedLabel}에 맞게 바꿔야 합니다.`
      : `${speechMismatch.detectedLabel} 표현이라 현재 상대에게 요구되는 ${speechMismatch.expectedLabel}와 맞지 않습니다.`,
    severity: 'warning',
    type: typoCorrections.length > 0 ? 'spelling_speech_level' : 'speech_level',
    tip: `${speechMismatch.expectedLabel} 예시: ${LEVEL_EXAMPLES[speechMismatch.expectedCode]}`,
  } : null;
  const localCorrections = finalSpeechCorrection ? [finalSpeechCorrection] : typoCorrections;
  const localScore = Math.min(speechMismatch?.score ?? 100, typoCorrections.length > 0 ? 70 : 100);
  const backendScore = feedback?.accuracy_score ?? 100;
  const summary = [speechMismatch?.summary, typoCorrections.length > 0 ? '오타가 보여서 자연스러운 표기로 고쳐 봤어요.' : ''].filter(Boolean).join(' ');
  const localEncouragement = speechMismatch ? '문장 끝맺음만 맞춰도 훨씬 자연스럽게 들려요.' : '오타만 고치면 더 자연스럽게 들려요.';
  return {
    corrected_message: speechMismatch ? speechMismatch.corrected : (spellingFixedText !== text ? spellingFixedText : feedback?.corrected_message || ''),
    detected_speech_level: detectedCode ? LEVEL_LABELS[detectedCode] : feedback?.detected_speech_level || '',
    detected_speech_level_code: detectedCode || feedback?.detected_speech_level_code,
    speech_level_correct: speechMismatch ? false : feedback?.speech_level_correct ?? true,
    expected_speech_level: expectedCode ? LEVEL_LABELS[expectedCode] : feedback?.expected_speech_level || '',
    expected_speech_level_code: expectedCode || feedback?.expected_speech_level_code,
    input_kind: feedback?.input_kind,
    verdict: speechMismatch ? (typoCorrections.length > 0 ? 'speech_and_spelling' : 'wrong_speech_level') : 'spelling',
    has_errors: true, accuracy_score: Math.min(backendScore, localScore), scorable: true,
    corrections: localCorrections,
    natural_alternatives: speechMismatch
      ? [{ expression: speechMismatch.corrected, explanation: `${speechMismatch.expectedLabel}로 더 자연스럽게 바꾼 최종 문장입니다.` }]
      : spellingFixedText !== text ? [{ expression: spellingFixedText, explanation: '오타를 고친 자연스러운 문장입니다.' }]
      : feedback?.natural_alternatives || [],
    encouragement: localEncouragement, summary: summary || feedback?.summary || '',
  };
};

const isScorableFeedback = (fb: SpeechAnalysis) =>
  fb.scorable !== false && fb.accuracy_score !== null && fb.accuracy_score !== undefined
  && fb.verdict !== 'speech_level_term' && fb.input_kind !== 'speech_level_term';

const normalizeSpeechLevelCode = (level: any, explicitCode?: string) => {
  if (explicitCode) return explicitCode;
  if (typeof level === 'object' && level?.code) return String(level.code);
  if (typeof level === 'string') { const n = level.trim().toLowerCase(); return LEVEL_LABELS[n] ? n : ''; }
  return '';
};

const normalizeSpeechLevelLabel = (level: any, explicitLabel?: string) => {
  if (explicitLabel) return explicitLabel;
  if (typeof level === 'object') {
    const label = level?.label_ko || level?.label || level?.name_ko;
    if (label) return String(label);
    if (level?.code) return LEVEL_LABELS[String(level.code).toLowerCase()] || String(level.code);
  }
  if (typeof level === 'string') { const n = level.trim().toLowerCase(); return LEVEL_LABELS[n] || level; }
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

const isValidAlternative = (
  alt: NaturalAlternative | undefined,
  originalText = '',
  correctedText = '',
  expectedLevel = '',
) => {
  const expression = alt?.expression?.trim() || '';
  const explanation = alt?.explanation?.trim() || '';
  if (!expression || expression.length < 2) return false;
  if (BAD_ALT_PATTERNS.some(pattern => pattern.test(expression) || pattern.test(explanation))) return false;
  if (expression === originalText.trim()) return false;
  if (correctedText && expression === correctedText.trim()) return false;
  const expectedCode = normalizeExpectedLevelCode(expectedLevel);
  const detectedCode = detectLikelySpeechLevel(expression) || '';
  if (expectedCode && detectedCode && detectedCode !== expectedCode) return false;
  return true;
};

const getRecommendedExpression = (feedback?: SpeechAnalysis | null, fallback = '') =>
  feedback?.corrected_message || feedback?.natural_alternatives?.[0]?.expression || feedback?.corrections?.[0]?.corrected || fallback;

const buildWholeSentenceCorrection = (originalText: string, feedback?: SpeechAnalysis | null) => {
  if (!feedback?.has_errors) return '';
  if (feedback.corrected_message?.trim()) return feedback.corrected_message.trim();

  const directWholeSentence = feedback.corrections?.find(c => c.original?.trim() === originalText.trim() && c.corrected?.trim());
  if (directWholeSentence?.corrected) return directWholeSentence.corrected.trim();

  let reconstructed = originalText;
  for (const correction of feedback.corrections || []) {
    if (!correction.original || !correction.corrected) continue;
    if (correction.original === originalText) continue;
    reconstructed = reconstructed.replace(correction.original, correction.corrected);
  }
  if (reconstructed.trim() && reconstructed.trim() !== originalText.trim()) return reconstructed.trim();

  return feedback?.natural_alternatives?.[0]?.expression?.trim() || '';
};

const buildRecentMistakeContext = (messages: Message[]) =>
  messages.filter(m => m.sender === 'user' && m.feedback?.has_errors).slice(-4).map(m => ({
    message: m.text, corrected: getRecommendedExpression(m.feedback, m.text),
    verdict: m.feedback?.verdict, summary: m.feedback?.summary,
  }));

const buildCorrectionContext = (sessionId: string, text: string, expectedSpeechLevel: string | undefined, feedback: SpeechAnalysis | null, messages: Message[]): CorrectionContext => {
  const expectedCode = normalizeExpectedLevelCode(expectedSpeechLevel);
  const expectedLabel = expectedCode ? LEVEL_LABELS[expectedCode] : String(expectedSpeechLevel || '');
  const correctedUserMessage = getRecommendedExpression(feedback, applyLocalSpellingFixes(text));
  return {
    session_id: sessionId,
    expected_speech_level_code: expectedCode || String(expectedSpeechLevel || ''),
    expected_speech_level_label: expectedLabel,
    latest_user_message: text, corrected_user_message: correctedUserMessage,
    latest_feedback: feedback ? {
      verdict: feedback.verdict, has_errors: feedback.has_errors,
      accuracy_score: feedback.accuracy_score,
      detected_speech_level: feedback.detected_speech_level,
      detected_speech_level_code: feedback.detected_speech_level_code,
      summary: feedback.summary, corrections: feedback.corrections,
    } : null,
    recent_mistakes: buildRecentMistakeContext(messages),
    response_guidance: [
      '사용자의 원문에 오타나 말투 오류가 있으면 corrected_user_message 기준으로 의도를 이해하세요.',
      '채팅 답변에는 "polite detected", "점수", "감지" 같은 분석 라벨을 직접 쓰지 마세요.',
      '교정이 필요한 경우 자연스러운 수정 문장을 짧게 짚은 뒤, 아바타의 말투로 대화를 이어가세요.',
      '이전 recent_mistakes를 참고해 같은 실수가 반복되면 조금 더 분명하게 안내하세요.',
    ],
  };
};

const buildSituationPromptContext = (situation: any) => {
  if (!situation) return null;
  if (typeof situation === 'string') return situation.trim() || null;
  const name = situation?.name_ko || situation?.title || situation?.name || '';
  const description = situation?.description_ko || situation?.description || '';
  const contexts = Array.isArray(situation?.contexts) ? situation.contexts.filter((item: any) => String(item).trim()) : [];
  const categoryId = String(situation?.category || '').trim();
  const categoryLabel = SITUATION_CATEGORY_LABELS[categoryId] || categoryId;
  const isCustom = Boolean(situation?.isCustom);
  const parts = [
    name ? `상황 이름: ${name}` : '',
    description ? `상황 설명: ${description}` : '',
    categoryLabel ? `상황 카테고리: ${categoryLabel}` : '',
    contexts.length > 0 ? `상황 맥락: ${contexts.join(', ')}` : '',
    isCustom ? '이 상황은 사용자가 직접 만든 맞춤 상황입니다.' : '',
  ].filter(Boolean);
  return parts.join('\n') || null;
};

const sanitizeAiReply = (message: string) =>
  message.replace(DECORATIVE_REPLY_SYMBOLS, '').replace(/[ \t]{2,}/g, ' ').trim();

const isDiagnosticOrGenericReply = (message: string) => {
  const normalized = message.trim();
  if (!normalized) return true;
  return (
    /(polite|formal|informal|speech level|detected|accuracy|score)/i.test(normalized) ||
    /(감지|점수|정확도|분석 결과|말투 분석)/.test(normalized) ||
    /(네,?\s*그렇군요|더 이야기해|계속.*대화|무엇을 도와|도와드릴|말씀해 주세요)/.test(normalized)
  );
};

const buildCorrectionAwareFallbackReply = (originalText: string, feedback?: SpeechAnalysis | null) => {
  if (!feedback?.has_errors) return '';
  const corrected = getRecommendedExpression(feedback, originalText);
  if (feedback.verdict === 'speech_and_spelling') return `"${corrected}"라고 하면 더 자연스러워. 좋아, 그 표현으로 다시 이어가 보자.`;
  if (feedback.verdict === 'spelling') return `"${corrected}"가 맞는 표기야. 무슨 말인지 알겠어. 이어서 말해줘.`;
  if (feedback.verdict === 'wrong_speech_level') return `"${corrected}"처럼 말하면 지금 관계에 더 잘 맞아. 그럼 계속 이야기해 보자.`;
  return `"${corrected}"라고 하면 더 자연스러워. 계속 이어가 볼게.`;
};

const makeContextAwareAiReply = (rawMessage: string, originalText: string, feedback?: SpeechAnalysis | null) => {
  const cleaned = sanitizeAiReply(rawMessage || '');
  if (!feedback?.has_errors) return cleaned || '좋아, 계속 이야기해 보자.';
  if (!isDiagnosticOrGenericReply(cleaned)) return cleaned;
  return buildCorrectionAwareFallbackReply(originalText, feedback) || cleaned;
};

const feedbackTitle = (fb: SpeechAnalysis) => {
  const detected = normalizeSpeechLevelLabel(fb.detected_speech_level);
  const expected = normalizeSpeechLevelLabel(fb.expected_speech_level);
  if (fb.verdict === 'speech_level_term' || fb.input_kind === 'speech_level_term') return '말투 이름만 입력됨';
  if (fb.verdict === 'not_scorable' || fb.scorable === false) return '분석 제외';
  if (fb.verdict === 'speech_and_spelling') return '여러 부분을 함께 다듬어 볼까요?';
  if (fb.verdict === 'practice_expression') return `${detected || expected || '말투'} 연습 표현`;
  if (fb.verdict === 'fragment') return '표현 조각';
  if (fb.verdict === 'spelling' || fb.corrections.some(c => c.type === 'spelling')) return '표기를 조금 다듬으면 더 좋아요';
  if (fb.verdict === 'wrong_speech_level') return detected ? `${detected}보다 조금 더 맞춰 볼게요` : '말투를 조금 맞춰 볼게요';
  if (fb.verdict === 'needs_revision') return '조금만 다듬으면 더 자연스러워요';
  if (fb.verdict === 'unclear') return '말투를 판단하기 어려워요';
  if (fb.input_kind === 'meta_practice') return `${detected || expected || '말투'} 연습 표현`;
  if (fb.input_kind === 'fragment') return '표현 조각';
  if (fb.input_kind === 'non_korean') return '한국어 표현 아님';
  if (!detected) return fb.expected_speech_level || '말투 분석';
  if (detected.includes('연습 표현') || detected.includes('표현 분석')) return detected;
  if (fb.detected_speech_confidence && fb.detected_speech_confidence < 0.75) return `${detected}에 가까워요`;
  return `${detected} 표현이에요`;
};

const correctionCategoryMeta = (correction: Correction) => {
  const original = correction.original || '';
  const corrected = correction.corrected || '';
  const compactOriginal = original.replace(/\s+/g, '');
  const compactCorrected = corrected.replace(/\s+/g, '');

  if (correction.type === 'honorific') {
    if (/주세|주실|드려|부탁/.test(corrected)) {
      return { label: '요청 표현', tint: '#DBEAFE', text: '#1D4ED8' };
    }
    return { label: '호칭/높임', tint: '#DBEAFE', text: '#1D4ED8' };
  }
  if (correction.type === 'speech_level' || correction.type === 'spelling_speech_level') {
    return { label: '말투', tint: '#EDE9FE', text: '#6D28D9' };
  }
  if (correction.type === 'vocabulary') {
    return { label: '어휘', tint: '#FEF3C7', text: '#B45309' };
  }
  if (correction.type === 'grammar') {
    return { label: '문법', tint: '#FCE7F3', text: '#BE185D' };
  }
  if (compactOriginal === compactCorrected && original !== corrected) {
    return { label: '띄어쓰기', tint: '#DCFCE7', text: '#15803D' };
  }
  return { label: '오타', tint: '#FEE2E2', text: '#DC2626' };
};

const feedbackSubtitle = (fb: SpeechAnalysis) => {
  if (!fb.has_errors) return '지금 문장도 충분히 자연스러워요';
  const labels = Array.from(new Set((fb.corrections || []).map(c => correctionCategoryMeta(c).label)));
  if (labels.length === 0) {
    return fb.summary || '조금만 다듬으면 더 자연스러워요';
  }
  if (labels.length === 1) {
    return `${labels[0]}만 다듬으면 훨씬 자연스러워져요`;
  }
  if (labels.length === 2) {
    return `${labels[0]}와 ${labels[1]}을 함께 보면 좋아요`;
  }
  return `${labels.slice(0, 3).join(' · ')}를 함께 다듬어 볼게요`;
};

// ─── API ─────────────────────────────────────────────────────────────────────

const sendMessageToAI = async (
  text: string, history: HistoryItem[], avatar: any, situation: any,
  user_id: string, expectedSpeechLevel?: string, sessionId?: string, correctionContext?: CorrectionContext,
) => {
  const situationContext = buildSituationPromptContext(situation);
  const legacyPayload = {
    user_message: text, conversation_history: history,
    avatar: { id: avatar?.id || 'test', name_ko: avatar?.name_ko || '아바타', role: avatar?.role || 'friend', personality_traits: avatar?.personality_traits || [], interests: avatar?.interests || [], dislikes: avatar?.dislikes || [] },
    situation: situationContext, user_id,
  };
  const contextPayload = { ...legacyPayload, session_id: sessionId, expected_speech_level: expectedSpeechLevel, correction_context: correctionContext, response_instruction: correctionContext?.response_guidance };
  const postChat = (payload: any) => fetch(`${AI_SERVER}/api/v1/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  let res = await postChat(contextPayload);
  if ((res.status === 400 || res.status === 422) && correctionContext) res = await postChat(legacyPayload);
  if (!res.ok) throw new Error(`AI server error: ${res.status}`);
  const data = await res.json();
  const correction = data.correction;
  const detectedRaw = correction?.detected_speech_level || correction?.detected_level;
  const expectedRaw = correction?.expected_speech_level || correction?.expected_level;
  const speech_analysis: SpeechAnalysis | null = correction ? {
    corrected_message: correction.corrected_message || '',
    detected_speech_level: normalizeSpeechLevelLabel(detectedRaw, correction.detected_speech_level_label || correction.detected_level_label),
    detected_speech_level_code: normalizeSpeechLevelCode(detectedRaw, correction.detected_speech_level_code || correction.detected_level_code),
    detected_speech_confidence: normalizeConfidence(detectedRaw, correction.detected_speech_level_confidence || correction.detected_confidence),
    speech_level_correct: correction.speech_level_correct ?? true,
    expected_speech_level: normalizeSpeechLevelLabel(expectedRaw, correction.expected_speech_level_label || correction.expected_level_label),
    expected_speech_level_code: normalizeSpeechLevelCode(expectedRaw, correction.expected_speech_level_code || correction.expected_level_code),
    input_kind: correction.input_kind || correction.inputKind, verdict: correction.verdict,
    has_errors: correction.has_errors ?? false, accuracy_score: normalizeScore(correction.accuracy_score),
    scorable: correction.scorable, corrections: correction.corrections || [],
    natural_alternatives: correction.natural_alternatives || [],
    encouragement: correction.encouragement || '', summary: correction.summary || correction.overall_feedback || '',
  } : null;
  const finalSpeechAnalysis = applyLocalFeedbackGuard(text, speech_analysis, expectedSpeechLevel);
  const correctedText = correction?.corrected_message || finalSpeechAnalysis?.corrections?.[0]?.corrected || '';
  if (finalSpeechAnalysis) {
    finalSpeechAnalysis.natural_alternatives = (finalSpeechAnalysis.natural_alternatives || []).filter(
      alt => isValidAlternative(alt, text, correctedText, expectedSpeechLevel),
    );
  }
  return {
    message: makeContextAwareAiReply(data.message || data.response || data.reply || '', text, finalSpeechAnalysis),
    speech_analysis: finalSpeechAnalysis,
    mood_change: data.mood_change || 0, current_mood: data.current_mood || 70,
    mood_emoji: data.mood_emoji || '😊', correct_streak: data.correct_streak || 0,
  };
};

const analyzeSessionWithAI = async (avatar: any, history: HistoryItem[]) => {
  const res = await fetch(`${AI_SERVER}/api/v1/chat/analyze`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ avatar, conversation_history: history }) });
  if (!res.ok) throw new Error(`Analyze error: ${res.status}`);
  return res.json();
};

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function ChatScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();

  const avatar           = route.params?.avatar;
  const situation        = route.params?.situation;
  const recommendedLevel = route.params?.recommendedLevel || avatar?.formality_from_user || 'polite';
  const profileName      = route.params?.name     || avatar?.name_ko || '아바타';
  const profileBg        = route.params?.avatarBg || avatar?.avatar_bg || '#6C3BFF';

  const flatListRef  = useRef<FlatList>(null);
  const sessionIdRef = useRef(route.params?.sessionId || `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`);

  const [messages,         setMessages]         = useState<Message[]>([]);
  const [input,            setInput]            = useState('');
  const [loading,          setLoading]          = useState(false);
  const [avatarMood,       setAvatarMood]       = useState(70);
  const [startTime]        = useState(Date.now());
  const [userId,           setUserId]           = useState('test-user-1');
  const [correctStreak,    setCorrectStreak]    = useState(0);
  // Default expanded = true so card opens immediately after send
  const [expandedFeedback, setExpandedFeedback] = useState<Record<string, boolean>>({});

  useEffect(() => { AsyncStorage.getItem('user_id').then(id => { if (id) setUserId(id); }); }, []);
  useEffect(() => { if (messages.length > 0) setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100); }, [messages]);
  useEffect(() => {
    if (!avatar || messages.length === 0) return;
    saveConversationPreview(buildLatestPreviewPayload(messages, avatar, situation, sessionIdRef.current)).catch(() => {});
  }, [avatar, messages, situation]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    const userMsg: Message = { id: Date.now().toString(), text, sender: 'user' };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const history: HistoryItem[] = [...buildHistoryFromMessages(messages), { role: 'user', content: text }];
      const localAnalysisHint = applyLocalFeedbackGuard(text, null, recommendedLevel);
      const correctionContext = buildCorrectionContext(sessionIdRef.current, text, recommendedLevel, localAnalysisHint, messages);
      const data = await sendMessageToAI(text, history, avatar, situation, userId, recommendedLevel, sessionIdRef.current, correctionContext);
      const aiMsg: Message = { id: (Date.now() + 1).toString(), text: data.message, sender: 'ai' };
      setAvatarMood(data.current_mood);
      setCorrectStreak(data.correct_streak);
      setMessages(prev => {
        const updated = prev.map(m => m.id === userMsg.id ? { ...m, feedback: data.speech_analysis ?? undefined } : m);
        return [...updated, aiMsg];
      });
      if (data.speech_analysis) setExpandedFeedback(prev => ({ ...prev, [userMsg.id]: true }));
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { id: (Date.now() + 1).toString(), text: '네, 그렇군요! 더 이야기해주세요.', sender: 'ai' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleEndChat = async () => {
    const duration    = Math.floor((Date.now() - startTime) / 1000);
    const durationStr = `${String(Math.floor(duration/60)).padStart(2,'0')}:${String(duration%60).padStart(2,'0')}`;
    const history     = buildHistoryFromMessages(messages);
    const sessionCorrections = messages.filter(m => m.sender === 'user' && m.feedback && isScorableFeedback(m.feedback)).map(m => ({
      message: m.text, accuracy_score: m.feedback!.accuracy_score, has_errors: m.feedback!.has_errors,
      corrections: m.feedback!.corrections, detected_level: m.feedback!.detected_speech_level, encouragement: m.feedback!.encouragement,
    }));
    const avgScore = sessionCorrections.length > 0 ? Math.round(sessionCorrections.reduce((s, c) => s + (c.accuracy_score ?? 0), 0) / sessionCorrections.length) : 100;
    let sessionReport = null;
    try { sessionReport = await analyzeSessionWithAI(avatar, history); } catch {}
    navigation.navigate('ConversationSummary', { avatar, duration: durationStr, situation, conversationHistory: history, finalMood: avatarMood, sessionReport, sessionCorrections, avgScore });
  };

  // ── Pip row ────────────────────────────────────────────────────────────────
  const renderPips = (mood: number) => {
    const col = moodColor(mood);
    const filled = Math.floor(mood / 20);
    const partial = (mood % 20) / 20;
    return (
      <View style={styles.pipsRow}>
        {[0,1,2,3,4].map(i => (
          <View
            key={i}
            style={[
              styles.pip,
              i < filled ? { backgroundColor: col } :
              i === filled && partial > 0.2 ? { backgroundColor: col, opacity: 0.4 } :
              { backgroundColor: '#E5E5EA' },
            ]}
          />
        ))}
      </View>
    );
  };

  // ── Feedback card ──────────────────────────────────────────────────────────
  const renderFeedbackCard = (item: Message) => {
    if (!item.feedback) return null;
    const fb         = item.feedback;
    const expanded   = expandedFeedback[item.id] ?? true;
    const hasError   = fb.has_errors;
    const isScorable = isScorableFeedback(fb);
    const sc         = scoreColor(fb.accuracy_score);
    const scoreLabel = isScorable ? `${fb.accuracy_score}점` : '분석 제외';
    const alternatives    = fb.natural_alternatives || [];
    const hasAlts         = alternatives.length > 0;
    const primaryCorrection = hasError && fb.corrections.length > 0 ? fb.corrections[0] : null;
    const fullSentenceCorrection = hasError ? buildWholeSentenceCorrection(item.text, fb) : '';

    return (
      <View style={styles.feedbackCard}>
        {/* Header — always visible, tap to fold */}
        <TouchableOpacity
          style={styles.feedbackHeader}
          onPress={() => setExpandedFeedback(prev => ({ ...prev, [item.id]: !expanded }))}
          activeOpacity={0.7}
        >
          <View style={styles.feedbackDot}>
            {hasError
              ? <AlertCircle size={12} color="#888" />
              : <CheckCircle size={12} color="#888" />}
          </View>
          <View style={styles.feedbackTitleBlock}>
            <Text style={styles.feedbackTitle}>{feedbackTitle(fb)}</Text>
            <Text style={styles.feedbackSub}>{feedbackSubtitle(fb)}</Text>
          </View>
          {/* Score chip always visible */}
          <Text style={[styles.scoreChip, { color: sc, backgroundColor: `${sc}14` }]}>
            {scoreLabel}
          </Text>
          <ChevronDown
            size={14}
            color="#bbb"
            style={{ transform: [{ rotate: expanded ? '180deg' : '0deg' }] }}
          />
        </TouchableOpacity>

        {/* Body — collapsible */}
        {expanded && (
          <View style={styles.feedbackBody}>
            {/* Score bar */}
            <View style={styles.scoreRow}>
              <Text style={[styles.scoreNum, { color: sc }]}>{isScorable ? fb.accuracy_score : '–'}</Text>
              <View style={styles.scoreBarWrap}>
                <View style={styles.scoreTrack}>
                  <View style={[styles.scoreFill, { width: `${isScorable ? (fb.accuracy_score ?? 0) : 0}%`, backgroundColor: sc }]} />
                </View>
                <Text style={[styles.scoreHint, { color: sc }]}>
                  {!isScorable ? '분석 제외' : (fb.accuracy_score ?? 0) >= 70 ? '완벽해요' : (fb.accuracy_score ?? 0) >= 40 ? '수정 추천' : '말투 오류 있음'}
                </Text>
              </View>
            </View>

            {/* Correction compare boxes */}
            {fullSentenceCorrection ? (
              <View style={styles.fullSentenceBox}>
                <Text style={styles.fullSentenceLabel}>전체 문장 수정</Text>
                <Text style={styles.fullSentenceText}>{fullSentenceCorrection}</Text>
              </View>
            ) : null}

            {primaryCorrection && (
              <View style={styles.cmpRow}>
                <View style={styles.cmpSide}>
                  <Text style={styles.cmpLabel}>입력</Text>
                  <Text style={styles.cmpText}>{primaryCorrection.original}</Text>
                </View>
                <Text style={styles.cmpArrow}>→</Text>
                <View style={[styles.cmpSide, styles.cmpSideFixed]}>
                  <Text style={[styles.cmpLabel, styles.cmpLabelFixed]}>수정</Text>
                  <Text style={[styles.cmpText, styles.cmpTextFixed]}>{primaryCorrection.corrected}</Text>
                </View>
              </View>
            )}

            {/* Note */}
            {fb.summary ? <Text style={styles.fcNote}>{fb.summary}</Text> : null}

            {hasError && fb.corrections.length > 0 && (
              <View style={styles.categoryChipsRow}>
                {Array.from(new Map(fb.corrections.map(c => {
                  const meta = correctionCategoryMeta(c);
                  return [meta.label, meta];
                })).values()).map(meta => (
                  <View key={meta.label} style={[styles.categoryChip, { backgroundColor: meta.tint }]}>
                    <Text style={[styles.categoryChipText, { color: meta.text }]}>{meta.label}</Text>
                  </View>
                ))}
              </View>
            )}

            {/* All corrections detail */}
            {hasError && fb.corrections.length > 0 && (
              <View style={styles.correctionList}>
                {fb.corrections.map((c, i) => {
                  const meta = correctionCategoryMeta(c);
                  return (
                  <View key={i} style={styles.correctionItem}>
                    <View style={styles.correctionItemHeader}>
                      <Text style={[styles.correctionTypeLabel, { backgroundColor: meta.tint, color: meta.text }]}>
                        {meta.label}
                      </Text>
                      <Text style={styles.correctionSeverity}>
                        {c.severity === 'error' ? '꼭 수정' : '수정 추천'}
                      </Text>
                    </View>
                    <View style={styles.correctionCompare}>
                      <Text style={styles.correctionOrig}>{c.original}</Text>
                      <Text style={styles.correctionArrow}>→</Text>
                      <Text style={styles.correctionFixed}>{c.corrected}</Text>
                    </View>
                    <Text style={styles.correctionExplain}>{c.explanation}</Text>
                    {c.tip ? <Text style={styles.correctionTip}>Tip: {c.tip}</Text> : null}
                  </View>
                  );
                })}
              </View>
            )}

            {/* Alternatives */}
            {hasAlts && (
              <View style={styles.altsSection}>
                <View style={styles.altsHeader}>
                  <Lightbulb size={12} color="#6C3BFF" />
                  <Text style={styles.altsLabel}>이렇게도 말할 수 있어요</Text>
                </View>
                {alternatives.map((alt, i) => (
                  <View key={i} style={[styles.altItem, i < alternatives.length - 1 && styles.altItemBorder]}>
                    <Text style={styles.altExpr}>{alt.expression}</Text>
                    {alt.explanation ? <Text style={styles.altExpl}>{alt.explanation}</Text> : null}
                  </View>
                ))}
              </View>
            )}

            {/* Encouragement */}
            {fb.encouragement && !hasAlts ? (
              <Text style={styles.encouragement}>{fb.encouragement}</Text>
            ) : null}
          </View>
        )}
      </View>
    );
  };

  // ── Message row ────────────────────────────────────────────────────────────
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
          item.sender === 'user' && item.feedback?.has_errors && styles.bubbleUserError,
        ]}>
          <Text style={[styles.bubbleText, item.sender === 'user' ? styles.bubbleTextUser : styles.bubbleTextAi,
            item.sender === 'user' && item.feedback?.has_errors && styles.bubbleTextError,
          ]}>
            {item.text}
          </Text>
        </View>
      </View>
      {item.sender === 'user' && item.feedback && renderFeedbackCard(item)}
    </View>
  );

  const moodState = getMoodState(avatarMood);
  const mc        = moodColor(avatarMood);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <ChevronLeft size={22} color="#111" />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <View style={[styles.headerAvatar, { backgroundColor: profileBg }]}>
            <Icon name={avatar?.icon || 'user'} size={16} color="#FFFFFF" />
          </View>
          <View>
            <Text style={styles.headerName}>{profileName}</Text>
            <Text style={styles.headerSub}>{situation?.name_ko || '대화'}</Text>
          </View>
        </View>
        <TouchableOpacity style={styles.headerEndBtn} onPress={handleEndChat}>
          <Text style={styles.headerEndText}>종료</Text>
        </TouchableOpacity>
      </View>

      {/* Mood strip */}
      <View style={styles.moodStrip}>
        <View style={styles.moodFaceWrap}>
          <MoodFace mood={avatarMood} />
          <Text style={[styles.moodFaceLabel, { color: mc }]}>{moodState.label}</Text>
        </View>
        <View style={styles.moodRight}>
          <View style={styles.moodTopRow}>
            <Text style={styles.moodPct}>{avatarMood}%</Text>
            <View style={styles.moodMeta}>
              <Text style={styles.moodHint}>기분</Text>
              {correctStreak >= 3 && (
                <View style={styles.streakBadge}>
                  <StarIcon />
                  <Text style={styles.streakText}>{correctStreak}연속</Text>
                </View>
              )}
            </View>
          </View>
          {renderPips(avatarMood)}
        </View>
      </View>

      {/* Level bar */}
      <View style={styles.levelBar}>
        <Text style={styles.levelHint}>추천 말투</Text>
        <SpeechLevelBadge level={recommendedLevel} size="small" />
      </View>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.messageList}
          renderItem={renderMessage}
          extraData={expandedFeedback}
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
            <Send size={18} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────────────

const BRAND  = '#6C3BFF';
const GREY   = '#F2F2F7';
const BORDER = '#E5E5EA';

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#FFFFFF' },

  // Header
  header:        { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 14, paddingVertical: 12, backgroundColor: '#FFFFFF', borderBottomWidth: 1, borderBottomColor: BORDER },
  headerBtn:     { width: 36, alignItems: 'center' },
  headerCenter:  { flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1, justifyContent: 'center' },
  headerAvatar:  { width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  headerName:    { fontSize: 15, fontWeight: '500', color: '#111' },
  headerSub:     { fontSize: 11, color: '#999', marginTop: 1 },
  headerEndBtn:  { paddingHorizontal: 12, paddingVertical: 5, backgroundColor: 'rgba(255,77,77,0.09)', borderRadius: 20 },
  headerEndText: { fontSize: 12, fontWeight: '500', color: '#FF4D4D' },

  // Mood strip
  moodStrip:     { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 18, paddingVertical: 10, backgroundColor: GREY },
  moodFaceWrap:  { alignItems: 'center', gap: 4 },
  moodFaceLabel: { fontSize: 11, fontWeight: '500' },
  moodRight:     { flex: 1, gap: 6 },
  moodTopRow:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  moodPct:       { fontSize: 13, fontWeight: '500', color: '#111' },
  moodMeta:      { flexDirection: 'row', alignItems: 'center', gap: 6 },
  moodHint:      { fontSize: 11, color: '#999' },
  streakBadge:   { flexDirection: 'row', alignItems: 'center', gap: 3, backgroundColor: 'rgba(108,59,255,0.12)', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 20 },
  streakText:    { fontSize: 11, fontWeight: '500', color: BRAND },
  pipsRow:       { flexDirection: 'row', gap: 4 },
  pip:           { flex: 1, height: 4, borderRadius: 2 },

  // Level bar
  levelBar:  { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, paddingVertical: 7, borderBottomWidth: 1, borderBottomColor: BORDER },
  levelHint: { fontSize: 11, color: '#999' },

  // Messages
  messageList:    { padding: 14, gap: 4 },
  messageWrapper: { marginBottom: 12 },
  bubbleRow:      { flexDirection: 'row', alignItems: 'flex-end' },
  bubbleRowAi:    { justifyContent: 'flex-start' },
  bubbleRowUser:  { justifyContent: 'flex-end' },
  bubbleAvatar:   { width: 28, height: 28, borderRadius: 14, alignItems: 'center', justifyContent: 'center', marginRight: 7 },

  bubble:         { maxWidth: '74%', paddingHorizontal: 13, paddingVertical: 10, borderRadius: 18 },
  bubbleAi:       { backgroundColor: '#FFFFFF', borderRadius: 5, borderTopLeftRadius: 18, borderBottomLeftRadius: 18, borderBottomRightRadius: 18, borderWidth: 1, borderColor: BORDER },
  bubbleUser:     { backgroundColor: BRAND, borderRadius: 18, borderTopRightRadius: 5 },
  bubbleUserError:{ backgroundColor: '#FFFFFF', borderWidth: 1.5, borderColor: 'rgba(108,59,255,0.35)' },
  bubbleText:     { fontSize: 13.5, lineHeight: 21 },
  bubbleTextAi:   { color: '#111' },
  bubbleTextUser: { color: '#FFFFFF' },
  bubbleTextError:{ color: '#111' },

  // Feedback card
  feedbackCard:   { marginTop: 8, marginLeft: 35, borderRadius: 16, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: BORDER, overflow: 'hidden' },
  feedbackHeader: { flexDirection: 'row', alignItems: 'center', gap: 9, padding: 11 },
  feedbackDot:    { width: 22, height: 22, borderRadius: 11, backgroundColor: GREY, borderWidth: 1, borderColor: BORDER, alignItems: 'center', justifyContent: 'center' },
  feedbackTitleBlock: { flex: 1 },
  feedbackTitle:  { fontSize: 12.5, fontWeight: '500', color: '#111' },
  feedbackSub:    { fontSize: 10, color: '#999', marginTop: 1 },
  scoreChip:      { fontSize: 11, fontWeight: '500', paddingHorizontal: 9, paddingVertical: 3, borderRadius: 20, overflow: 'hidden' },

  feedbackBody:   { borderTopWidth: 1, borderTopColor: BORDER },
  scoreRow:       { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 12, paddingBottom: 8 },
  scoreNum:       { fontSize: 22, fontWeight: '500', minWidth: 38, lineHeight: 26 },
  scoreBarWrap:   { flex: 1, gap: 3 },
  scoreTrack:     { height: 5, borderRadius: 3, backgroundColor: BORDER, overflow: 'hidden' },
  scoreFill:      { height: '100%', borderRadius: 3 },
  scoreHint:      { fontSize: 10 },

  fullSentenceBox:{ marginHorizontal: 12, marginBottom: 10, padding: 12, borderRadius: 12, backgroundColor: '#F7F4FF', borderWidth: 1, borderColor: 'rgba(108,59,255,0.18)' },
  fullSentenceLabel:{ fontSize: 10, fontWeight: '600', color: BRAND, marginBottom: 6 },
  fullSentenceText:{ fontSize: 14, lineHeight: 21, fontWeight: '600', color: '#2D1B69' },

  cmpRow:         { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingBottom: 10 },
  cmpSide:        { flex: 1, padding: 9, borderRadius: 10, backgroundColor: GREY, borderWidth: 1, borderColor: BORDER },
  cmpSideFixed:   { backgroundColor: '#FFFFFF', borderColor: 'rgba(108,59,255,0.30)' },
  cmpLabel:       { fontSize: 9, fontWeight: '500', letterSpacing: 0.06, marginBottom: 3, color: '#999' },
  cmpLabelFixed:  { color: BRAND },
  cmpText:        { fontSize: 13, fontWeight: '500', color: '#555' },
  cmpTextFixed:   { color: BRAND },
  cmpArrow:       { fontSize: 12, color: '#bbb' },

  fcNote:         { fontSize: 11, color: '#666', lineHeight: 17, paddingHorizontal: 12, paddingBottom: 10 },
  categoryChipsRow:{ flexDirection: 'row', flexWrap: 'wrap', gap: 6, paddingHorizontal: 12, paddingBottom: 10 },
  categoryChip:   { paddingHorizontal: 9, paddingVertical: 5, borderRadius: 999 },
  categoryChipText:{ fontSize: 11, fontWeight: '600' },

  correctionList:       { paddingHorizontal: 12, paddingBottom: 10, gap: 8 },
  correctionItem:       { gap: 4 },
  correctionItemHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  correctionTypeLabel:  { fontSize: 10, fontWeight: '500', color: BRAND, backgroundColor: 'rgba(108,59,255,0.10)', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 20 },
  correctionSeverity:   { fontSize: 10, color: '#999' },
  correctionCompare:    { flexDirection: 'row', alignItems: 'center', gap: 6 },
  correctionOrig:       { fontSize: 13, fontWeight: '500', color: '#999', textDecorationLine: 'line-through' },
  correctionArrow:      { fontSize: 12, color: '#bbb' },
  correctionFixed:      { fontSize: 13, fontWeight: '500', color: BRAND },
  correctionExplain:    { fontSize: 11, color: '#666', lineHeight: 17 },
  correctionTip:        { fontSize: 11, color: BRAND, fontWeight: '500' },

  altsSection:    { marginHorizontal: 12, marginBottom: 12, backgroundColor: GREY, borderRadius: 12, padding: 10 },
  altsHeader:     { flexDirection: 'row', alignItems: 'center', gap: 5, marginBottom: 8 },
  altsLabel:      { fontSize: 10, fontWeight: '500', color: BRAND },
  altItem:        { paddingVertical: 5 },
  altItemBorder:  { borderBottomWidth: 0.5, borderBottomColor: BORDER, marginBottom: 5 },
  altExpr:        { fontSize: 13, fontWeight: '500', color: '#111' },
  altExpl:        { fontSize: 10.5, color: '#999', marginTop: 2, lineHeight: 15 },
  encouragement:  { fontSize: 12, color: '#22C55E', paddingHorizontal: 12, paddingBottom: 12 },

  // Loading
  loadingRow:    { flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 14, paddingBottom: 8 },
  loadingBubble: { backgroundColor: GREY, borderRadius: 18, paddingHorizontal: 20, paddingVertical: 12 },

  // Input
  inputBar:        { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 14, paddingVertical: 10, borderTopWidth: 1, borderTopColor: BORDER, backgroundColor: '#FFFFFF', gap: 8 },
  input:           { flex: 1, backgroundColor: GREY, borderRadius: 22, paddingHorizontal: 16, paddingVertical: 10, fontSize: 14, color: '#111' },
  sendBtn:         { width: 40, height: 40, borderRadius: 20, backgroundColor: BRAND, alignItems: 'center', justifyContent: 'center' },
  sendBtnDisabled: { opacity: 0.4 },
});
