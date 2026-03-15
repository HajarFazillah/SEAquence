import { API_BASE_URL } from '../constants';

// Types
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

// API Functions
class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  // Health check
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl.replace('/api/v1', '')}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  // Avatars
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

  // Situations
  async getSituations(): Promise<Situation[]> {
    const response = await fetch(`${this.baseUrl}/situations`);
    if (!response.ok) throw new Error('Failed to fetch situations');
    const data = await response.json();
    return data.situations;
  }

  // Speech Level Recommendation
  async getSpeechRecommendation(
    avatarId: string,
    situationId: string
  ): Promise<SpeechRecommendation> {
    const params = new URLSearchParams({
      avatar_id: avatarId,
      situation_id: situationId,
    });
    const response = await fetch(
      `${this.baseUrl}/recommendation/speech-level?${params}`
    );
    if (!response.ok) throw new Error('Failed to fetch recommendation');
    return response.json();
  }

  // Compatibility
  async analyzeCompatibility(
    userLikes: string[],
    userDislikes: string[],
    avatarId: string
  ): Promise<CompatibilityResult> {
    const response = await fetch(`${this.baseUrl}/compatibility/analyze`, {
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
    const response = await fetch(`${this.baseUrl}/compatibility/batch`, {
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

  // Chat
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
        session_id: sessionId,
        user_id: userId,
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
