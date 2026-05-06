// Nalin's AI server — port 8000
import { AI_SERVER_URL } from '../constants';

const AI_BASE_URL = AI_SERVER_URL;

export type HonorificResult = {
  kind: 'risk' | 'success' | 'neutral';
  message: string;
  suggestion?: string;
};

export async function analyzeHonorific(
  speaker: string,
  text: string,
  sessionId?: string
): Promise<HonorificResult> {
  try {
    const res = await fetch(`${AI_BASE_URL}/analyze/honorific`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ speaker, text, sessionId }),
    });

    if (!res.ok) throw new Error(`AI server error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[Honorific] analyzeHonorific error:', err);
    // Fail silently — don't block transcript on analysis failure
    return { kind: 'neutral', message: '' };
  }
}
