export type TranscriptTurnResult = {
  id: string;
  speaker: string;
  text: string;
  type: 'partial' | 'final';
};

export type InsightResult = {
  id: string;
  kind: 'risk' | 'success';
  message: string;
  suggestion?: string;
  turnId: string;
};

export type RealtimeAnalysisResult = {
  turns: TranscriptTurnResult[];
  insights: InsightResult[];
};

const API_BASE_URL = 'http://10.0.2.2:8080';

export async function uploadRealtimeAudio(filePath: string, sessionId?: string): Promise<RealtimeAnalysisResult> {
  const formData = new FormData();

  formData.append('file', {
    uri: filePath.startsWith('file://') ? filePath : `file://${filePath}`,
    name: `realtime-${Date.now()}.m4a`,
    type: 'audio/mp4',
  } as any);

  if (sessionId) {
    formData.append('sessionId', sessionId);
  }

  const response = await fetch(`${API_BASE_URL}/realtime/analyze`, {
    method: 'POST',
    body: formData,
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.status}`);
  }

  return await response.json();
}