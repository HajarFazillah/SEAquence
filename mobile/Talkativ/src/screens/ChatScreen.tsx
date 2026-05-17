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
import { appendPracticePatternEvent } from '../services/personalizationHistory';


import { AI_SERVER_URL } from '../constants';
const AI_SERVER = AI_SERVER_URL;

import { saveMistakesToBackend } from '../services/apiMistakes';

const saveMistakes = async (
  sessionId: string,
  turnNumber: number,
  corrections: Correction[],
) => {
  if (!corrections || corrections.length === 0) return;

  const mistakes = corrections
    .filter(c => c.severity === 'error' || c.severity === 'warning')
    .map(c => ({
      originalText: c.original,
      correctedText: c.corrected,
      correctionType: c.type || 'grammar',
      severity: c.severity,
      explanation: c.explanation,
      tip: c.tip || null,
    }));

  if (mistakes.length === 0) return;

  try {
    await saveMistakesToBackend(sessionId, turnNumber, mistakes);
  } catch (err) {
    console.log('Failed to save mistakes:', err);
  }
};

// ─── Types ────────────────────────────────────────────────────────────────────

type HistoryRole = 'user' | 'assistant';
interface HistoryItem { role: HistoryRole; content: string; }

interface Correction {
  original:     string;
  corrected:    string;
  explanation:  string;
  severity:     'error' | 'warning' | 'info';
  tip?:         string;
  type?:        string;
  alternatives?: string[];
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
  key: 'angry' | 'sad' | 'soso' | 'happy';
  label: string;
  subLabel: string;
  color: string;
  bg: string;
  lbrow: string; rbrow: string;
  leye:  string; reye:  string;
  mouth: string;
}

const MOOD_STATES: MoodState[] = [
  { key: 'angry', label: 'angry', subLabel: '불편함', color: '#EF4444', bg: 'rgba(239,68,68,0.10)', lbrow: 'M18 29 Q24 27 28 29', rbrow: 'M44 29 Q48 27 54 29', leye: 'M19 35 Q23 39 27 35', reye: 'M45 35 Q49 39 53 35', mouth: 'M23 50 Q36 44 49 50' },
  { key: 'sad',   label: 'sad',   subLabel: '속상함', color: '#F59E0B', bg: 'rgba(245,158,11,0.12)', lbrow: 'M18 26 Q24 23 28 26', rbrow: 'M44 26 Q48 23 54 26', leye: 'M19 32 Q23 29 27 32', reye: 'M45 32 Q49 29 53 32', mouth: 'M23 48 Q36 44 49 48' },
  { key: 'soso',  label: 'soso',  subLabel: '보통',   color: '#64748B', bg: 'rgba(100,116,139,0.12)', lbrow: 'M18 24 Q24 22 28 24', rbrow: 'M44 24 Q48 22 54 24', leye: 'M19 30 Q23 27 27 30', reye: 'M45 30 Q49 27 53 30', mouth: 'M23 46 Q36 46 49 46' },
  { key: 'happy', label: 'happy', subLabel: '좋음',   color: '#22C55E', bg: 'rgba(34,197,94,0.12)', lbrow: 'M18 22 Q24 17 28 22', rbrow: 'M44 22 Q48 17 54 22', leye: 'M19 29 Q23 24 27 29', reye: 'M45 29 Q49 24 53 29', mouth: 'M21 43 Q36 58 51 43' },
];

const getMoodState = (mood: number): MoodState => {
  if (mood >= 75) return MOOD_STATES[3];
  if (mood >= 50) return MOOD_STATES[2];
  if (mood >= 25) return MOOD_STATES[1];
  return MOOD_STATES[0];
};

const moodColor = (mood: number): string => {
  return getMoodState(mood).color;
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
  const col = s.color;
  return (
    <Svg width={52} height={52} viewBox="0 0 72 72">
      <Circle cx={36} cy={36} r={34} fill={s.bg} />
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

const normalizeExpectedLevelCode = (level?: string) => {
  if (!level) return '';
  const normalized = String(level).trim().toLowerCase();
  if (LEVEL_LABELS[normalized]) return normalized;
  const compact = normalized.replace(/\s+/g, '');
  return SPEECH_LEVEL_TERMS[normalized]?.code || SPEECH_LEVEL_TERMS[compact]?.code || '';
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
) => {
  const expression = alt?.expression?.trim() || '';
  const explanation = alt?.explanation?.trim() || '';
  if (!expression || expression.length < 2) return false;
  if (BAD_ALT_PATTERNS.some(pattern => pattern.test(expression) || pattern.test(explanation))) return false;
  if (expression === originalText.trim()) return false;
  if (correctedText && expression === correctedText.trim()) return false;
  return true;
};

const applyCorrectionOnce = (text: string, original: string, corrected: string) => {
  if (!text || !original || !corrected || original === corrected) return text;

  let searchFrom = 0;
  while (true) {
    const index = text.indexOf(original, searchFrom);
    if (index < 0) return text;
    if (text.startsWith(corrected, index)) {
      searchFrom = index + original.length;
      continue;
    }
    // If corrected ends with original (e.g., "세 시에" ends with "시에"), skip when
    // the added prefix is already present immediately before this match position.
    if (corrected.endsWith(original) && corrected.length > original.length) {
      const addedPrefix = corrected.slice(0, corrected.length - original.length);
      if (index >= addedPrefix.length && text.slice(index - addedPrefix.length, index) === addedPrefix) {
        searchFrom = index + original.length;
        continue;
      }
    }
    return `${text.slice(0, index)}${corrected}${text.slice(index + original.length)}`;
  }
};

const buildWholeSentenceCorrection = (originalText: string, feedback?: SpeechAnalysis | null) => {
  if (!feedback?.has_errors) return '';

  const directWholeSentence = feedback.corrections?.find(c => c.original?.trim() === originalText.trim() && c.corrected?.trim());
  const baseText = feedback.corrected_message?.trim() || directWholeSentence?.corrected?.trim() || originalText;

  let reconstructed = baseText;
  for (const correction of feedback.corrections || []) {
    if (!correction.original || !correction.corrected) continue;
    if (correction.original === originalText) continue;
    if (!originalText.includes(correction.original)) continue;
    if (!reconstructed.includes(correction.original)) continue;
    reconstructed = applyCorrectionOnce(reconstructed, correction.original, correction.corrected);
  }
  if (reconstructed.trim() && reconstructed.trim() !== originalText.trim()) return reconstructed.trim();

  return feedback?.natural_alternatives?.[0]?.expression?.trim() || '';
};

const getRecommendedExpression = (feedback?: SpeechAnalysis | null, fallback = '') =>
  (feedback ? buildWholeSentenceCorrection(fallback, feedback) : '')
  || feedback?.natural_alternatives?.[0]?.expression
  || feedback?.corrections?.[0]?.corrected
  || fallback;

const buildRecentMistakeContext = (messages: Message[]) =>
  messages.filter(m => m.sender === 'user' && m.feedback?.has_errors).slice(-4).map(m => ({
    message: m.text, corrected: getRecommendedExpression(m.feedback, m.text),
    verdict: m.feedback?.verdict, summary: m.feedback?.summary,
  }));

const buildCorrectionContext = (sessionId: string, text: string, expectedSpeechLevel: string | undefined, feedback: SpeechAnalysis | null, messages: Message[]): CorrectionContext => {
  const expectedCode = normalizeExpectedLevelCode(expectedSpeechLevel);
  const expectedLabel = expectedCode ? LEVEL_LABELS[expectedCode] : String(expectedSpeechLevel || '');
  const correctedUserMessage = getRecommendedExpression(feedback, text);
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
  const scenePlace = situation?.scene_place || situation?.scenePlace || '';
  const conversationGoal = situation?.conversation_goal || situation?.conversationGoal || '';
  const avatarRoleInScene = situation?.avatar_role_in_scene || situation?.avatarRoleInScene || '';
  const userRoleInScene = situation?.user_role_in_scene || situation?.userRoleInScene || '';
  const contexts = Array.isArray(situation?.contexts) ? situation.contexts.filter((item: any) => String(item).trim()) : [];
  const categoryId = String(situation?.category || '').trim();
  const categoryLabel = SITUATION_CATEGORY_LABELS[categoryId] || categoryId;
  const isCustom = Boolean(situation?.isCustom);
  const parts = [
    '상황은 대화가 벌어지는 장면/목표일 뿐이며, 아바타의 직업이나 관계를 바꾸지 않습니다.',
    '예: 카페 상황이어도 아바타가 원래 친구/교수/상사라면 카페 직원이나 점원이 아닙니다.',
    name ? `상황 이름: ${name}` : '',
    scenePlace ? `장소/장면: ${scenePlace}` : '',
    conversationGoal ? `연습 목표: ${conversationGoal}` : '',
    avatarRoleInScene ? `아바타의 장면 속 역할: ${avatarRoleInScene}` : '',
    userRoleInScene ? `사용자의 장면 속 역할: ${userRoleInScene}` : '',
    description ? `상황 설명: ${description}` : '',
    categoryLabel ? `상황 카테고리: ${categoryLabel}` : '',
    contexts.length > 0 ? `상황 맥락: ${contexts.join(', ')}` : '',
    '금지: 상황의 장소나 활동 때문에 아바타를 직원/점원/면접관/선생님 등 새 역할로 바꾸지 마세요.',
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

const avatarAllowsServiceRole = (avatar: any) => {
  const roleText = `${avatar?.role || ''} ${avatar?.custom_role || ''} ${avatar?.relationship || ''} ${avatar?.description_ko || ''} ${avatar?.description || ''}`.toLowerCase();
  return /(staff|employee|clerk|server|cashier|barista|waiter|customer|client|직원|점원|알바|아르바이트|종업원|바리스타|손님|고객|사장)/.test(roleText);
};

const avatarAllowsInterviewRole = (avatar: any) => {
  const roleText = `${avatar?.role || ''} ${avatar?.custom_role || ''} ${avatar?.relationship || ''} ${avatar?.description_ko || ''} ${avatar?.description || ''}`.toLowerCase();
  return /(interviewer|recruiter|hr|면접관|채용|인사담당)/.test(roleText);
};

const isRoleConsistencyBrokenReply = (message: string, avatar: any) => {
  const text = String(message || '');
  if (!avatarAllowsServiceRole(avatar)) {
    if (/(손님|고객님|주문\s*도와|주문하시|메뉴|저희\s*(카페|매장|식당|가게)|계산해\s*드릴|포장해\s*드릴)/.test(text)) {
      return true;
    }
  }
  if (!avatarAllowsInterviewRole(avatar)) {
    if (/(면접을\s*시작|지원자|채용\s*절차|면접관|자기소개\s*해\s*보세요)/.test(text)) {
      return true;
    }
  }
  return false;
};

const buildRoleSafeFallbackReply = (avatar: any, situation: any) => {
  const situationName = situation?.name_ko || situation?.name || situation?.title;
  const roleLabel = avatar?.relationship || avatar?.custom_role || avatar?.role;
  if (situationName) {
    return `응, ${situationName} 상황으로 계속 이야기해 보자. 나는 ${roleLabel || '네 대화 상대'}로서 여기에 있는 거야.`;
  }
  return `응, 계속 이야기해 보자. 나는 ${roleLabel || '네 대화 상대'}로서 여기에 있는 거야.`;
};

const makeContextAwareAiReply = (rawMessage: string, originalText: string, feedback?: SpeechAnalysis | null) => {
  const cleaned = sanitizeAiReply(rawMessage || '');
  if (!feedback?.has_errors) return cleaned || '좋아, 계속 이야기해 보자.';
  if (!isDiagnosticOrGenericReply(cleaned)) return cleaned;
  return buildCorrectionAwareFallbackReply(originalText, feedback) || cleaned;
};

const makeRoleSafeAiReply = (rawMessage: string, originalText: string, avatar: any, situation: any, feedback?: SpeechAnalysis | null) => {
  const reply = makeContextAwareAiReply(rawMessage, originalText, feedback);
  if (isRoleConsistencyBrokenReply(reply, avatar)) {
    return buildRoleSafeFallbackReply(avatar, situation);
  }
  return reply;
};

const feedbackTitle = (fb: SpeechAnalysis) => {
  const detected = normalizeSpeechLevelLabel(fb.detected_speech_level);
  const expected = normalizeSpeechLevelLabel(fb.expected_speech_level);
  const correctionTypes = new Set((fb.corrections || []).map(c => c.type));
  const actionableTypes = new Set(
    Array.from(correctionTypes).filter(type => type && type !== 'info'),
  );
  if (fb.verdict === 'speech_level_term' || fb.input_kind === 'speech_level_term') return '말투 이름만 입력됨';
  if (fb.verdict === 'not_scorable' || fb.scorable === false) return '분석 제외';
  if (fb.verdict === 'speech_and_spelling') return '여러 부분을 함께 다듬어 볼까요?';
  if (fb.verdict === 'practice_expression') return `${detected || expected || '말투'} 연습 표현`;
  if (fb.verdict === 'fragment') return '표현 조각';
  if (actionableTypes.size >= 2) return '여러 부분을 함께 다듬어 볼까요?';
  if (fb.verdict === 'wrong_speech_level') return detected ? `${detected}보다 조금 더 맞춰 볼게요` : '말투를 조금 맞춰 볼게요';
  if (correctionTypes.has('grammar')) return '문장 구조를 조금 다듬으면 더 좋아요';
  if (correctionTypes.has('honorific')) return '높임 표현을 조금 더 자연스럽게 해볼게요';
  if (correctionTypes.has('vocabulary')) return '어휘를 조금 더 상황에 맞춰 볼게요';
  if (correctionTypes.has('expression')) return '표현을 조금 더 자연스럽게 다듬어 볼게요';
  if (fb.verdict === 'spelling' || correctionTypes.has('spelling')) return '표기를 조금 다듬으면 더 좋아요';
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
  if (correction.type === 'expression') {
    return { label: '표현', tint: '#E0F2FE', text: '#0369A1' };
  }
  if (compactOriginal === compactCorrected && original !== corrected) {
    return { label: '띄어쓰기', tint: '#DCFCE7', text: '#15803D' };
  }
  if (correction.type === 'spelling') {
    return { label: '맞춤법', tint: '#FEE2E2', text: '#DC2626' };
  }
  return { label: '오타', tint: '#FFE4E4', text: '#DC2626' };
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
  const finalSpeechAnalysis = speech_analysis;
  const correctedText = correction?.corrected_message || finalSpeechAnalysis?.corrections?.[0]?.corrected || '';
  if (finalSpeechAnalysis) {
    finalSpeechAnalysis.natural_alternatives = (finalSpeechAnalysis.natural_alternatives || []).filter(
      alt => isValidAlternative(alt, text, correctedText),
    );
  }
  return {
    message: makeRoleSafeAiReply(data.message || data.response || data.reply || '', text, avatar, situation, finalSpeechAnalysis),
    speech_analysis: finalSpeechAnalysis,
    mood_change: data.mood_change || 0, current_mood: data.current_mood || 70,
    mood_emoji: data.mood_emoji || '😊', correct_streak: data.correct_streak || 0,
    hint: data.hint || '',
    suggestions: data.suggestions || [],
  };
};

const analyzeSessionWithAI = async (avatar: any, history: HistoryItem[], sessionId?: string) => {
  const res = await fetch(`${AI_SERVER}/api/v1/chat/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ avatar, conversation_history: history, session_id: sessionId }),
  });
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
  const [avatarMoodChange, setAvatarMoodChange] = useState(0);
  const [startTime]        = useState(Date.now());
  const [userId,           setUserId]           = useState('test-user-1');
  const [correctStreak,    setCorrectStreak]    = useState(0);
  // Default expanded = true so card opens immediately after send
  const [expandedFeedback, setExpandedFeedback] = useState<Record<string, boolean>>({});
  const [expandedAlternatives, setExpandedAlternatives] = useState<Record<string, boolean>>({});

  useEffect(() => {
    // Read both keys for backward compatibility ('userId' is the canonical key set on login).
    (async () => {
      const id = (await AsyncStorage.getItem('userId')) || (await AsyncStorage.getItem('user_id'));
      if (id) setUserId(id);
    })();
  }, []);

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
      const correctionContext = buildCorrectionContext(sessionIdRef.current, text, recommendedLevel, null, messages);
      const data = await sendMessageToAI(text, history, avatar, situation, userId, recommendedLevel, sessionIdRef.current, correctionContext);
      const aiMsg: Message = { id: (Date.now() + 1).toString(), text: data.message, sender: 'ai' };
      setAvatarMood(data.current_mood);
      setAvatarMoodChange(data.mood_change || 0);
      setCorrectStreak(data.correct_streak);
      setMessages(prev => {
        const updated = prev.map(m => m.id === userMsg.id ? { ...m, feedback: data.speech_analysis ?? undefined } : m);
        return [...updated, aiMsg];
      });
      if (data.speech_analysis) setExpandedFeedback(prev => ({ ...prev, [userMsg.id]: true }));
      const previousUserHadErrors = messages
        .filter(m => m.sender === 'user')
        .slice(-1)[0]?.feedback?.has_errors;
      appendPracticePatternEvent({
        sessionId: sessionIdRef.current,
        avatarId: avatar?.id,
        avatarName: avatar?.name_ko || avatar?.name,
        relationshipType: avatar?.role || avatar?.custom_role,
        situationId: situation?.id || situation?.situation_id,
        situationName: situation?.name_ko || situation?.name,
        situationCategory: situation?.category,
        speechLevel: recommendedLevel,
        correctionTypes: (data.speech_analysis?.corrections || [])
          .map((c: Correction) => c.type || 'unknown')
          .filter(Boolean),
        hadErrors: Boolean(data.speech_analysis?.has_errors),
        accuracyScore: data.speech_analysis?.accuracy_score,
        hintShown: Boolean(data.speech_analysis?.has_errors || data.hint || data.suggestions?.length),
        retrySuccess: Boolean(previousUserHadErrors && data.speech_analysis && !data.speech_analysis.has_errors),
      }).catch(() => {});
      // Save mistakes to backend
      if (data.speech_analysis?.has_errors && data.speech_analysis.corrections.length > 0) {
      const turnNumber = messages.filter(m => m.sender === 'user').length + 1;
      saveMistakes(sessionIdRef.current, turnNumber, data.speech_analysis.corrections);
      }

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
    try { sessionReport = await analyzeSessionWithAI(avatar, history, sessionIdRef.current); } catch {}

    // Fire-and-forget: extract durable per-avatar memories so the next chat with
    // this avatar starts already knowing the user.
    if (avatar?.id && history.length > 0) {
      fetch(`${AI_SERVER}/api/v1/chat/end-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          avatar_id: avatar.id,
          avatar_name: avatar.name_ko,
          session_id: sessionIdRef.current,
          conversation_history: history,
        }),
      }).catch(err => console.log('end-session failed:', err));
    }

    navigation.navigate('ConversationSummary', { avatar, duration: durationStr, situation, conversationHistory: history, finalMood: avatarMood, sessionReport, sessionCorrections, avgScore, sessionId: sessionIdRef.current });
  };

  // ── Pip row ────────────────────────────────────────────────────────────────
  const renderPips = (mood: number) => {
    const state = getMoodState(mood);
    const filled = Math.floor(mood / 25);
    const partial = (mood % 25) / 25;
    return (
      <View style={styles.pipsRow}>
        {[0,1,2,3].map(i => (
          <View
            key={i}
            style={[
              styles.pip,
              i < filled ? { backgroundColor: state.color } :
              i === filled && partial > 0.2 ? [styles.pipPartial, { backgroundColor: state.color }] :
              styles.pipEmpty,
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
    const altsExpanded = expandedAlternatives[item.id] ?? true;
    const hasError   = fb.has_errors;
    const isScorable = isScorableFeedback(fb);
    const sc         = scoreColor(fb.accuracy_score);
    const scoreLabel = isScorable ? `${fb.accuracy_score}점` : '분석 제외';
    const alternatives = fb.natural_alternatives || [];
    const fullSentenceCorrection = hasError ? buildWholeSentenceCorrection(item.text, fb) : '';
    const hasAlts = alternatives.length > 0;
    const nonDuplicateCorrections = fb.corrections.filter(c => {
      if (!fullSentenceCorrection) return true;
      const isWholeSentenceCorrection =
        c.corrected.trim() === fullSentenceCorrection.trim() ||
        c.original.trim() === item.text.trim();
      return !isWholeSentenceCorrection || fb.corrections.length === 1;
    });
    const visibleCorrections = nonDuplicateCorrections.length > 0
      ? nonDuplicateCorrections
      : fb.corrections;
    const categoryMetas = Array.from(new Map(fb.corrections.map(c => {
      const meta = correctionCategoryMeta(c);
      return [meta.label, meta];
    })).values());

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
            <Text style={styles.feedbackTitle}>{feedbackTitle({ ...fb, corrections: visibleCorrections })}</Text>
          </View>
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
            {/* Correction compare boxes */}
            {fullSentenceCorrection ? (
              <View style={styles.fullSentenceBox}>
                <Text style={styles.fullSentenceLabel}>전체 문장 수정</Text>
                <Text style={styles.fullSentenceText}>{fullSentenceCorrection}</Text>
              </View>
            ) : null}

            {/* Note */}

            {/* All corrections detail */}
            {hasError && visibleCorrections.length > 0 && (
              <View style={styles.correctionList}>
                {visibleCorrections.map((c, i) => {
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
                    {c.alternatives && c.alternatives.length > 0 && (
                      <View style={styles.correctionAltWrap}>
                        <Text style={styles.correctionAltLabel}>동등 표현</Text>
                        <View style={styles.correctionAltRow}>
                          {c.alternatives.map((alt, ai) => (
                            <View key={ai} style={styles.correctionAltChip}>
                              <Text style={styles.correctionAltText}>{alt}</Text>
                            </View>
                          ))}
                        </View>
                      </View>
                    )}
                  </View>
                  );
                })}
              </View>
            )}

            {/* Alternatives */}
            {hasAlts && (
              <View style={styles.altsSection}>
                <TouchableOpacity
                  style={[styles.altsHeader, !altsExpanded && styles.altsHeaderCollapsed]}
                  onPress={() => setExpandedAlternatives(prev => ({ ...prev, [item.id]: !altsExpanded }))}
                  activeOpacity={0.7}
                >
                  <View style={styles.altsHeaderLeft}>
                    <Lightbulb size={12} color="#6C3BFF" />
                    <Text style={styles.altsLabel}>이렇게도 말할 수 있어요</Text>
                  </View>
                  <View style={styles.altsHeaderRight}>
                    <Text style={styles.altsCount}>{alternatives.length}</Text>
                    <ChevronDown
                      size={14}
                      color="#6C3BFF"
                      style={{ transform: [{ rotate: altsExpanded ? '180deg' : '0deg' }] }}
                    />
                  </View>
                </TouchableOpacity>
                {altsExpanded && alternatives.map((alt, i) => (
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
        {/* Left: face + score */}
        <View style={styles.moodFaceWrap}>
          <MoodFace mood={avatarMood} />
          <View style={styles.moodScoreRow}>
            <Text style={styles.moodPct}>{avatarMood}%</Text>
            {avatarMoodChange !== 0 && (
              <View style={[
                styles.moodDeltaBadge,
                avatarMoodChange > 0 ? styles.moodDeltaBadgePositive : styles.moodDeltaBadgeNegative,
              ]}>
                <Text style={[
                  styles.moodDeltaText,
                  avatarMoodChange > 0 ? styles.moodDeltaTextPositive : styles.moodDeltaTextNegative,
                ]}>
                  {avatarMoodChange > 0 ? `+${avatarMoodChange}` : avatarMoodChange}
                </Text>
              </View>
            )}
            {correctStreak >= 3 && (
              <View style={styles.streakBadge}>
                <StarIcon />
                <Text style={styles.streakText}>{correctStreak}연속</Text>
              </View>
            )}
          </View>
        </View>

        {/* Right: speech level */}
        <View style={styles.moodRight}>
          <Text style={styles.levelHint}>추천 말투</Text>
          <SpeechLevelBadge level={recommendedLevel} size="small" />
        </View>
      </View>

      <KeyboardAvoidingView style={styles.keyboardView} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.messageList}
          renderItem={renderMessage}
          extraData={{ expandedFeedback, expandedAlternatives }}
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
  headerSub:     { fontSize: 12, color: '#999', marginTop: 1 },
  headerEndBtn:  { paddingHorizontal: 12, paddingVertical: 5, backgroundColor: 'rgba(255,77,77,0.09)', borderRadius: 20 },
  headerEndText: { fontSize: 12, fontWeight: '500', color: '#FF4D4D' },

  // Mood strip
  moodStrip:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 10, backgroundColor: '#FFFFFF', borderBottomWidth: 1, borderBottomColor: BORDER },
  moodFaceWrap:  { alignItems: 'center', gap: 5 },
  moodScoreRow:  { flexDirection: 'row', alignItems: 'center', gap: 5 },
  moodRight:     { alignItems: 'flex-end', gap: 4 },
  moodPct:       { fontSize: 14, fontWeight: '700', color: '#111' },
  moodMeta:      { flexDirection: 'row', alignItems: 'center', gap: 6 },
  moodHint:      { fontSize: 12, color: '#aaa', letterSpacing: 0.3 },
  moodDeltaBadge:{ paddingHorizontal: 7, paddingVertical: 2, borderRadius: 20 },
  moodDeltaText: { fontSize: 12, fontWeight: '700' },
  streakBadge:   { flexDirection: 'row', alignItems: 'center', gap: 3, backgroundColor: 'rgba(108,59,255,0.12)', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 20 },
  streakText:    { fontSize: 12, fontWeight: '500', color: BRAND },
  pipsRow:       { flexDirection: 'row', gap: 4 },
  pip:           { flex: 1, height: 4, borderRadius: 2 },
  pipPartial:    { opacity: 0.4 },
  pipEmpty:      { backgroundColor: '#E5E5EA' },
  moodDeltaBadgePositive: { backgroundColor: 'rgba(34,197,94,0.12)' },
  moodDeltaBadgeNegative: { backgroundColor: 'rgba(239,68,68,0.10)' },
  moodDeltaTextPositive:  { color: '#16A34A' },
  moodDeltaTextNegative:  { color: '#EF4444' },

  // Level bar
  levelHint: { fontSize: 12, color: '#999' },
  keyboardView: { flex: 1 },

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
  feedbackTitle:  { fontSize: 13, fontWeight: '500', color: '#111' },
  feedbackSub:    { fontSize: 12, color: '#999', marginTop: 1 },
  scoreChip:      { fontSize: 11, fontWeight: '500', paddingHorizontal: 9, paddingVertical: 3, borderRadius: 20, overflow: 'hidden' },

  feedbackBody:   { borderTopWidth: 1, borderTopColor: BORDER },
  scoreRow:       { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 12, paddingBottom: 8 },
  scoreNum:       { fontSize: 22, fontWeight: '500', minWidth: 38, lineHeight: 26 },
  scoreBarWrap:   { flex: 1, gap: 3 },
  scoreTrack:     { height: 5, borderRadius: 3, backgroundColor: BORDER, overflow: 'hidden' },
  scoreFill:      { height: '100%', borderRadius: 3 },
  scoreHint:      { fontSize: 10 },

  fullSentenceBox:{ marginHorizontal: 12, marginTop: 12, marginBottom: 10, padding: 12, borderRadius: 12, backgroundColor: '#F7F4FF', borderWidth: 1, borderColor: 'rgba(108,59,255,0.18)' },
  fullSentenceLabel:{ fontSize: 12, fontWeight: '600', color: BRAND, marginBottom: 6 },
  fullSentenceText:{ fontSize: 14, lineHeight: 21, fontWeight: '600', color: '#2D1B69' },

  cmpRow:         { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingBottom: 10 },
  cmpSide:        { flex: 1, padding: 9, borderRadius: 10, backgroundColor: GREY, borderWidth: 1, borderColor: BORDER },
  cmpSideFixed:   { backgroundColor: '#FFFFFF', borderColor: 'rgba(108,59,255,0.30)' },
  cmpLabel:       { fontSize: 11, fontWeight: '500', letterSpacing: 0.06, marginBottom: 3, color: '#999' },
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
  correctionSeverity:   { fontSize: 12, color: '#999' },
  correctionCompare:    { flexDirection: 'column', gap: 2 },
  correctionOrig:       { fontSize: 13, fontWeight: '500', color: '#999', textDecorationLine: 'line-through', flexShrink: 1 },
  correctionArrow:      { fontSize: 11, color: '#bbb' },
  correctionFixed:      { fontSize: 13, fontWeight: '500', color: BRAND, flexShrink: 1 },
  correctionExplain:    { fontSize: 13, color: '#374151', lineHeight: 19 },
  correctionAltWrap:    { marginTop: 8, gap: 5 },
  correctionAltLabel:   { fontSize: 11, fontWeight: '600', color: '#9CA3AF', letterSpacing: 0.3 },
  correctionAltRow:     { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  correctionAltChip:    { backgroundColor: '#EEF2FF', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4 },
  correctionAltText:    { fontSize: 13, color: BRAND, fontWeight: '500' },
  correctionTip:        { fontSize: 12, color: BRAND, fontWeight: '500', marginTop: 4 },

  altsSection:    { marginHorizontal: 12, marginBottom: 12, backgroundColor: GREY, borderRadius: 12, padding: 10 },
  altsHeader:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 },
  altsHeaderCollapsed: { marginBottom: 0 },
  altsHeaderLeft: { flexDirection: 'row', alignItems: 'center', gap: 5, flexShrink: 1 },
  altsHeaderRight:{ flexDirection: 'row', alignItems: 'center', gap: 4 },
  altsLabel:      { fontSize: 12, fontWeight: '500', color: BRAND },
  altsCount:      { fontSize: 11, fontWeight: '600', color: BRAND },
  altItem:        { paddingVertical: 5 },
  altItemBorder:  { borderBottomWidth: 0.5, borderBottomColor: BORDER, marginBottom: 5 },
  altExpr:        { fontSize: 13, fontWeight: '500', color: '#111' },
  altExpl:        { fontSize: 12, color: '#999', marginTop: 2, lineHeight: 17 },
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
