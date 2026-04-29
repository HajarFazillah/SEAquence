// Nalin's AI server — port 8000
const AI_BASE_URL = 'http://10.0.2.2:8000'; // 10.0.2.2 = host machine from Android emulator
// On physical device, replace with your actual LAN IP e.g. 'http://192.168.x.x:8000'

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