import axios from 'axios';
import { SPRING_API_BASE_URL } from '../constants';

const API_BASE_URL = SPRING_API_BASE_URL;

export type TranscriptTurnResult = {
  id?: string;
  speaker?: string;
  text?: string;
  type?: 'partial' | 'final' | string;
};

export type InsightResult = {
  id?: string;
  kind?: 'risk' | 'success' | string;
  message?: string;
  suggestion?: string;
  turnId?: string;
  turn_id?: string;
};

export type RealtimeAnalysisResponse = {
  turns?: TranscriptTurnResult[];
  insights?: InsightResult[];
};

export async function analyzeRealtimeAudio(
  formData: FormData
): Promise<RealtimeAnalysisResponse> {
  const response = await axios.post<RealtimeAnalysisResponse>(
    `${API_BASE_URL}/realtime/analyze`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    }
  );

  return {
    turns: Array.isArray(response.data?.turns) ? response.data.turns : [],
    insights: Array.isArray(response.data?.insights) ? response.data.insights : [],
  };
}
