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
    avatarRole: string,
    situationId: string
  ): Promise<SpeechRecommendation> {
    const response = await fetch(
      `${AI_BASE_URL}/recommendation/speech-level?role=${avatarRole}`
    );
    if (!response.ok) throw new Error('Failed to fetch recommendation');

    const data = await response.json();
    const fromUser = data.from_user;
    const toUser   = data.to_user;

    // AI 서버 응답 → 프론트 형식으로 변환
    return {
      recommended_level: fromUser.level as 'formal' | 'polite' | 'informal',
      recommended_level_info: {
        name_ko:     fromUser.name_ko,
        description: fromUser.description,
        endings:     fromUser.endings.split(', '),
      },
      reason_ko: `${data.role_label}과의 대화에서는 ${fromUser.name_ko}를 사용하는 것이 적절합니다.`,
      example_expressions: {
        greetings: fromUser.examples.slice(0, 2),
        questions: fromUser.examples.map((e: string) => `${e}?`).slice(0, 2),
        responses: toUser.examples.slice(0, 2),
      },
      avoid_expressions: [
        {
          wrong:  toUser.examples[0] || '',
          reason: `${data.role_label}에게 ${toUser.name_ko}는 부적절합니다.`,
        },
      ],
      tips: [
        `${data.role_label}과 대화할 때는 ${fromUser.name_ko}를 사용하세요.`,
        `어미 ${fromUser.endings}를 사용하면 자연스러워요.`,
        `예시: ${fromUser.examples.join(', ')}`,
        `${data.role_label}은(는) 당신에게 ${toUser.name_ko}로 말할 거예요.`,
      ],
    };
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
    userDislikes: string[]
  ): Promise<CompatibilityResult[]> {
    const response = await fetch(`${AI_BASE_URL}/compatibility/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user: { likes: userLikes, dislikes: userDislikes },
      }),
    });
    if (!response.ok) throw new Error('Failed to batch analyze compatibility');
    const data = await response.json();
    return data.results;
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