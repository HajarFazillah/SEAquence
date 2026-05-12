import { SPRING_API_BASE_URL } from '../constants';

const API_BASE_URL = SPRING_API_BASE_URL;

export type RealtimeAnalysisResponse = {
  status?: string;
  transcript?: string;
  speaker?: string;
  sessionId?: string;
  [key: string]: any;
};

export type AnalyzeRealtimeParams = {
  fileUri: string;
  fileName?: string;
  mimeType?: string;
  sessionId?: string;
};

function normalizeFileUri(uri: string) {
  if (uri.startsWith('file://')) return uri;
  return `file://${uri}`;
}

function getDefaultFileName(uri: string) {
  const parts = uri.split('/');
  return parts[parts.length - 1] || `audio_${Date.now()}.m4a`;
}

function getDefaultMimeType(fileName: string) {
  const lower = fileName.toLowerCase();
  if (lower.endsWith('.wav')) return 'audio/wav';
  if (lower.endsWith('.mp3')) return 'audio/mpeg';
  if (lower.endsWith('.aac')) return 'audio/aac';
  if (lower.endsWith('.m4a')) return 'audio/mp4';
  if (lower.endsWith('.mp4')) return 'audio/mp4';
  return 'application/octet-stream';
}

export async function analyzeRealtimeAudio(
  params: AnalyzeRealtimeParams
): Promise<RealtimeAnalysisResponse> {
  const { fileUri, fileName, mimeType, sessionId } = params;

  const resolvedFileName = fileName || getDefaultFileName(fileUri);
  const resolvedMimeType = mimeType || getDefaultMimeType(resolvedFileName);
  const resolvedUri = normalizeFileUri(fileUri);

  const formData = new FormData();

  formData.append('file', {
    uri: resolvedUri,
    name: resolvedFileName,
    type: resolvedMimeType,
  } as any);

  if (sessionId) {
    formData.append('sessionId', sessionId);
  }

  const response = await fetch(`${API_BASE_URL}/realtime/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => '');
    throw new Error(
      `Realtime analysis failed (${response.status}): ${errorText || response.statusText}`
    );
  }

  return response.json();
}
