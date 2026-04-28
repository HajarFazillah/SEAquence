import { API_BASE_URL } from '../constants';

// ── 서버 주소 ────────────────────────────────────────────────────────────────
const SPRING_BASE_URL = API_BASE_URL;                    // Spring Boot :8080
const AI_BASE_URL     = 'http://10.0.2.2:8000/api/v1';  // AI 서버 :8000

// ============================================================================
// Types
// ============================================================================

export interface Avatar {
  id: string;
  name_ko: string;
  name_en: string;
  role: string;
  difficulty: string;
  formality: string;
  description_ko?: string;
  greeting?: string;
}

export interface Situation {
  id: string;
  name_ko: string;
  name_en: string;
  description_ko: string;
  context?: string;
  category?: string;
  contexts?: string[];
  isCustom?: boolean;
}

export interface SpeechRecommendation {
  recommended_level: 'formal' | 'polite' | 'informal';
  recommended_level_info: {
    name_ko: string;
    description: string;
    endings: string[];
  };
  reason_ko: string;
  example_expressions: {
    greetings: string[];
    questions: string[];
    responses: string[];
  };
  avoid_expressions: Array<{
    wrong: string;
    reason: string;
  }>;
  tips: string[];
}

export interface CompatibilityResult {
  avatar_id: string;
  score: number;
  chemistry_level: string;
  common_interests: string[];
  suggested_topics: string[];
  avoid_topics: string[];
  recommendation?: string;
}

export interface CompatibilityAvatarInput {
  id: string;
  name_ko: string;
  role: string;
  difficulty?: string;
  interests?: string[];
  dislikes?: string[];
  personality_traits?: string[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  response: string;
  speech_analysis?: {
    detected_level: string;
    is_appropriate: boolean;
    feedback_ko?: string;
  };
}

type SpeechLevelCode = 'formal' | 'polite' | 'informal';
type RecommendationContext =
  | 'very_formal'
  | 'formal'
  | 'professional'
  | 'neutral'
  | 'casual'
  | 'intimate';
type RecommendationCloseness =
  | 'just_met'
  | 'stranger'
  | 'acquaintance'
  | 'friendly'
  | 'close'
  | 'very_close'
  | 'intimate';
type RecommendationSocialStatus =
  | 'much_lower'
  | 'lower'
  | 'equal'
  | 'higher'
  | 'much_higher';

const LEVEL_META: Record<SpeechLevelCode, { name_ko: string; description: string; endings: string[]; examples: string[] }> = {
  formal: {
    name_ko: '합쇼체',
    description: "가장 격식있는 말투입니다. '-습니다', '-습니까' 등의 어미를 사용합니다.",
    endings: ['-습니다', '-습니까'],
    examples: ['안녕하십니까', '감사합니다', '괜찮으시면 도와주십시오'],
  },
  polite: {
    name_ko: '해요체',
    description: "공손하지만 부드러운 말투입니다. '-어요', '-아요' 등의 어미를 사용합니다.",
    endings: ['-어요', '-아요'],
    examples: ['안녕하세요', '감사해요', '도와주실 수 있나요?'],
  },
  informal: {
    name_ko: '반말',
    description: "친한 사이에서 쓰는 편한 말투입니다. '-어', '-아', '-야' 등의 어미를 사용합니다.",
    endings: ['-어', '-아', '-야'],
    examples: ['안녕', '고마워', '같이 가자'],
  },
};

const ROLE_LABELS: Record<string, string> = {
  friend: '친구',
  close_friend: '절친',
  classmate: '반 친구',
  roommate: '룸메이트',
  club_member: '동아리 멤버',
  junior: '후배',
  senior: '선배',
  professor: '교수님',
  teacher: '선생님',
  tutor: '과외 선생님',
  younger_sibling: '동생',
  older_brother: '형/오빠',
  older_sister: '누나/언니',
  cousin: '사촌',
  parent: '부모님',
  grandparent: '조부모님',
  uncle_aunt: '삼촌/이모',
  in_law: '시댁/처가 어른',
  intern: '인턴',
  colleague: '동료',
  teammate: '팀원',
  team_leader: '팀장',
  manager: '매니저',
  boss: '사장님',
  ceo: '대표님',
  client: '고객',
  mentor: '멘토',
  staff: '직원',
  customer: '손님',
  stranger: '모르는 사람',
  neighbor: '이웃',
  doctor: '의사 선생님',
  delivery: '배달원',
  taxi_driver: '택시 기사님',
};

const parseAge = (value: unknown, fallback: number): number => {
  const parsed = Number.parseInt(String(value ?? ''), 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

const deriveContext = (situation?: Situation): RecommendationContext => {
  const haystack = `${situation?.id || ''} ${situation?.name_ko || ''} ${situation?.description_ko || ''} ${situation?.category || ''}`.toLowerCase();

  if (/면접|interview/.test(haystack)) return 'very_formal';
  if (/교수|연구실|doctor|의사|상담|formal/.test(haystack)) return 'formal';
  if (/회의|meeting|project|업무|work/.test(haystack)) return 'professional';
  if (/주문|order|shopping|쇼핑|service|delivery|taxi/.test(haystack)) return 'neutral';
  if (/파티|모임|카페|campus|casual|friend/.test(haystack)) return 'casual';
  return 'neutral';
};

const deriveCloseness = (role: string, situation?: Situation): RecommendationCloseness => {
  const haystack = `${situation?.id || ''} ${situation?.name_ko || ''} ${situation?.description_ko || ''}`.toLowerCase();

  if (/처음|first/.test(haystack)) return 'just_met';
  if (['close_friend', 'roommate'].includes(role)) return 'very_close';
  if (['friend', 'classmate', 'younger_sibling'].includes(role)) return 'close';
  if (['club_member', 'colleague', 'teammate', 'mentor', 'cousin'].includes(role)) return 'friendly';
  if (['stranger', 'doctor', 'delivery', 'taxi_driver', 'staff', 'customer', 'client'].includes(role)) return 'stranger';
  return 'acquaintance';
};

const deriveSocialStatus = (role: string): RecommendationSocialStatus => {
  if (['professor', 'teacher', 'boss', 'ceo', 'doctor', 'parent', 'grandparent'].includes(role)) return 'much_higher';
  if (['senior', 'manager', 'team_leader', 'client', 'older_brother', 'older_sister', 'uncle_aunt', 'in_law'].includes(role)) return 'higher';
  if (['junior', 'intern', 'younger_sibling', 'staff', 'delivery'].includes(role)) return 'lower';
  return 'equal';
};

const buildRecommendationFallback = (level: SpeechLevelCode, roleLabel: string, situation?: Situation): SpeechRecommendation => {
  const meta = LEVEL_META[level];
  const situationLabel = situation?.name_ko ? ` ${situation.name_ko} 상황에서는` : ' 대화에서는';

  return {
    recommended_level: level,
    recommended_level_info: {
      name_ko: meta.name_ko,
      description: meta.description,
      endings: meta.endings,
    },
    reason_ko: `${roleLabel}과${situationLabel} ${meta.name_ko}를 쓰는 편이 자연스러워요.`,
    example_expressions: {
      greetings: meta.examples.slice(0, 2),
      questions: meta.examples.slice(0, 2).map((example) => `${example}?`),
      responses: meta.examples.slice(1, 3),
    },
    avoid_expressions: [],
    tips: [
      `${roleLabel}에게는 ${meta.name_ko}를 기본으로 사용해 보세요.`,
      `주요 어미: ${meta.endings.join(', ')}`,
      `상황이 바뀌면 말투도 조금 달라질 수 있어요.`,
    ],
  };
};

const normalizeRecommendation = (
  raw: Partial<SpeechRecommendation> | null | undefined,
  fallback: SpeechRecommendation
): SpeechRecommendation => {
  const level = raw?.recommended_level && LEVEL_META[raw.recommended_level]
    ? raw.recommended_level
    : fallback.recommended_level;

  return {
    recommended_level: level,
    recommended_level_info: {
      name_ko: raw?.recommended_level_info?.name_ko || fallback.recommended_level_info.name_ko,
      description: raw?.recommended_level_info?.description || fallback.recommended_level_info.description,
      endings: Array.isArray(raw?.recommended_level_info?.endings) && raw!.recommended_level_info!.endings.length > 0
        ? raw!.recommended_level_info!.endings
        : fallback.recommended_level_info.endings,
    },
    reason_ko: raw?.reason_ko || fallback.reason_ko,
    example_expressions: {
      greetings: Array.isArray(raw?.example_expressions?.greetings) && raw!.example_expressions!.greetings.length > 0
        ? raw!.example_expressions!.greetings
        : fallback.example_expressions.greetings,
      questions: Array.isArray(raw?.example_expressions?.questions) && raw!.example_expressions!.questions.length > 0
        ? raw!.example_expressions!.questions
        : fallback.example_expressions.questions,
      responses: Array.isArray(raw?.example_expressions?.responses) && raw!.example_expressions!.responses.length > 0
        ? raw!.example_expressions!.responses
        : fallback.example_expressions.responses,
    },
    avoid_expressions: Array.isArray(raw?.avoid_expressions) && raw!.avoid_expressions!.length > 0
      ? raw!.avoid_expressions!.filter((item) => item?.wrong || item?.reason)
      : fallback.avoid_expressions,
    tips: Array.isArray(raw?.tips) && raw!.tips!.length > 0
      ? raw!.tips!.filter(Boolean)
      : fallback.tips,
  };
};

// ============================================================================
// API Service
// ============================================================================

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = SPRING_BASE_URL;
  }

  // ── Health check ───────────────────────────────────────────────────────────
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl.replace('/api/v1', '')}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // ── Avatars (Spring Boot) ──────────────────────────────────────────────────
  async getAvatars(): Promise<Avatar[]> {
    const response = await fetch(`${this.baseUrl}/avatars`);
    if (!response.ok) throw new Error('Failed to fetch avatars');
    const data = await response.json();
    return data.avatars;
  }

  async getAvatar(avatarId: string): Promise<Avatar> {
    const response = await fetch(`${this.baseUrl}/avatars/${avatarId}`);
    if (!response.ok) throw new Error('Failed to fetch avatar');
    return response.json();
  }

  // ── Situations (Spring Boot) ───────────────────────────────────────────────
  async getSituations(): Promise<Situation[]> {
    const response = await fetch(`${this.baseUrl}/situations`);
    if (!response.ok) throw new Error('Failed to fetch situations');
    const data = await response.json();
    return data.situations;
  }

  // ── Speech Level Recommendation (AI 서버) ──────────────────────────────────
  async getSpeechRecommendation(
    avatar: Partial<Avatar> & { age?: string | number; formality_from_user?: string; custom_role?: string },
    situation?: Situation
  ): Promise<SpeechRecommendation> {
    const avatarRole = avatar?.role || 'friend';
    const roleLabel = ROLE_LABELS[avatarRole] || avatar?.custom_role || avatarRole;
    const defaultLevel = (avatar?.formality_from_user as SpeechLevelCode) || 'polite';
    const fallbackRecommendation = buildRecommendationFallback(defaultLevel, roleLabel, situation);

    try {
      const userAge = 24;
      const avatarAge = parseAge(avatar?.age, userAge);
      const context = deriveContext(situation);
      const closeness = deriveCloseness(avatarRole, situation);
      const socialStatus = deriveSocialStatus(avatarRole);
      const isFirstMeeting = /처음|first/i.test(`${situation?.id || ''} ${situation?.name_ko || ''}`);
      const yearsKnown = closeness === 'very_close' ? 3 : closeness === 'close' ? 2 : closeness === 'friendly' ? 1 : 0;
      const isPublicSetting = ['very_formal', 'formal', 'professional', 'neutral'].includes(context);

      const response = await fetch(`${AI_BASE_URL}/recommendation/speech-level/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: avatarRole,
          user_age: userAge,
          avatar_age: avatarAge,
          closeness,
          social_status: socialStatus,
          context,
          years_known: yearsKnown,
          is_first_meeting: isFirstMeeting,
          is_public_setting: isPublicSetting,
          is_being_observed: isPublicSetting,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch calculated recommendation');
      }

      const data = await response.json();
      const recommendedLevel = data.user_to_avatar as SpeechLevelCode;
      const meta = LEVEL_META[recommendedLevel] || LEVEL_META.polite;

      return normalizeRecommendation({
        recommended_level: recommendedLevel,
        recommended_level_info: {
          name_ko: data.user_to_avatar_ko || meta.name_ko,
          description: meta.description,
          endings: meta.endings,
        },
        reason_ko: data.explanation || `${roleLabel}과의 상황에 맞춰 ${meta.name_ko}를 추천해요.`,
        example_expressions: {
          greetings: [data.user_example, ...meta.examples].filter(Boolean).slice(0, 3),
          questions: [data.user_example, ...meta.examples].filter(Boolean).map((example: string) => `${example}?`).slice(0, 3),
          responses: [data.avatar_example, ...meta.examples].filter(Boolean).slice(0, 3),
        },
        avoid_expressions: (data.common_mistakes || []).slice(0, 3).map((mistake: string) => ({
          wrong: mistake,
          reason: '이 상황에서는 더 자연스러운 높임 표현으로 바꾸는 편이 좋아요.',
        })),
        tips: [...(data.tips || []), ...(data.factors_applied || []).map((factor: string) => `${factor}도 함께 반영했어요.`)].slice(0, 5),
      }, fallbackRecommendation);
    } catch {
      try {
        const response = await fetch(
          `${AI_BASE_URL}/recommendation/speech-level?role=${avatarRole}`
        );
        if (!response.ok) throw new Error('Failed to fetch recommendation');

        const data = await response.json();
        const fromUser = data.from_user;
        const toUser = data.to_user;

        return normalizeRecommendation({
          recommended_level: fromUser.level as SpeechLevelCode,
          recommended_level_info: {
            name_ko: fromUser.name_ko,
            description: fromUser.description,
            endings: fromUser.endings.split(', '),
          },
          reason_ko: `${data.role_label}과의 대화에서는 ${fromUser.name_ko}를 사용하는 것이 적절합니다.`,
          example_expressions: {
            greetings: fromUser.examples.slice(0, 2),
            questions: fromUser.examples.map((e: string) => `${e}?`).slice(0, 2),
            responses: toUser.examples.slice(0, 2),
          },
          avoid_expressions: [
            {
              wrong: toUser.examples[0] || '',
              reason: `${data.role_label}에게 ${toUser.name_ko}는 부적절합니다.`,
            },
          ],
          tips: [
            `${data.role_label}과 대화할 때는 ${fromUser.name_ko}를 사용하세요.`,
            `어미 ${fromUser.endings}를 사용하면 자연스러워요.`,
            `예시: ${fromUser.examples.join(', ')}`,
            `${data.role_label}은(는) 당신에게 ${toUser.name_ko}로 말할 거예요.`,
          ],
        }, fallbackRecommendation);
      } catch {
        return fallbackRecommendation;
      }
    }
  }

  // ── Compatibility (AI 서버) ────────────────────────────────────────────────
  async analyzeCompatibility(
    userLikes: string[],
    userDislikes: string[],
    avatarId: string
  ): Promise<CompatibilityResult> {
    const response = await fetch(`${AI_BASE_URL}/compatibility/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user: { likes: userLikes, dislikes: userDislikes },
        avatar_id: avatarId,
      }),
    });
    if (!response.ok) throw new Error('Failed to analyze compatibility');
    return response.json();
  }

  async batchCompatibility(
    userLikes: string[],
    userDislikes: string[],
    avatars: CompatibilityAvatarInput[]
  ): Promise<CompatibilityResult[]> {
    const response = await fetch(`${AI_BASE_URL}/compatibility/batch-simple`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_profile: {
          name: '나',
          age: 23,
          korean_level: 'intermediate',
          interests: userLikes,
          dislikes: userDislikes,
        },
        avatars: avatars.map((avatar) => ({
          id: avatar.id,
          name_ko: avatar.name_ko,
          role: avatar.role || 'friend',
          difficulty: avatar.difficulty || 'medium',
          interests: avatar.interests || [],
          dislikes: avatar.dislikes || [],
          personality_traits: avatar.personality_traits || [],
        })),
      }),
    });
    if (!response.ok) throw new Error('Failed to batch analyze compatibility');
    const data = await response.json();
    return (data.results || []).map((item: any) => ({
      avatar_id: String(item.avatar_id || ''),
      score: Math.round(item.overall_score || 0),
      chemistry_level: item.overall_score >= 85
        ? 'excellent'
        : item.overall_score >= 70
          ? 'good'
          : item.overall_score >= 50
            ? 'okay'
            : 'low',
      common_interests: Array.isArray(item.shared_interests) ? item.shared_interests : [],
      suggested_topics: Array.isArray(item.shared_interests) ? item.shared_interests.slice(0, 3) : [],
      avoid_topics: [],
      recommendation: item.recommendation || '',
    }));
  }

  // ── Chat (Spring Boot) ─────────────────────────────────────────────────────
  async sendMessage(
    sessionId: string,
    userId: string,
    message: string,
    avatar: Avatar,
    situation: Situation,
    conversationHistory: ChatMessage[]
  ): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/session/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id:           sessionId,
        user_id:              userId,
        message,
        avatar,
        situation,
        conversation_history: conversationHistory,
      }),
    });
    if (!response.ok) throw new Error('Failed to send message');
    return response.json();
  }
}

export const apiService = new ApiService();
