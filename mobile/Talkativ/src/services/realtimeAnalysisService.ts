import axios from 'axios';

const API_BASE_URL = 'http://10.0.2.2:8080'; // Android emulator
// const API_BASE_URL = 'http://10.240.44.208:8080'; // physical device

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