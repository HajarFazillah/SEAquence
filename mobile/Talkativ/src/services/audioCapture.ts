import Sound, { RecordBackType } from 'react-native-nitro-sound';
import { PermissionsAndroid, Platform } from 'react-native';

let isCapturing = false;

export type RecordingProgress = {
  currentPosition: number;
  currentMetering?: number;
};

export function isAudioCapturing() {
  return isCapturing;
}

async function requestMicPermission(): Promise<boolean> {
  if (Platform.OS !== 'android') return true;

  const granted = await PermissionsAndroid.request(
    PermissionsAndroid.PERMISSIONS.RECORD_AUDIO,
    {
      title: '마이크 권한 필요',
      message: '대화 분석을 위해 마이크 접근이 필요합니다.',
      buttonPositive: '허용',
      buttonNegative: '거부',
    }
  );
  return granted === PermissionsAndroid.RESULTS.GRANTED;
}

export async function startAudioCapture(
  onProgress?: (progress: RecordingProgress) => void
): Promise<string> {
  if (isCapturing) return '';

  const hasPermission = await requestMicPermission();
  if (!hasPermission) {
    throw new Error('마이크 권한이 거부되었습니다.');
  }

  try {
    isCapturing = true;
    Sound.removeRecordBackListener();
    Sound.addRecordBackListener((e: RecordBackType) => {
      onProgress?.({
        currentPosition: e.currentPosition,
        currentMetering: e.currentMetering,
      });
    });

    const path = await Sound.startRecorder();
    return path;
  } catch (error) {
    isCapturing = false;
    Sound.removeRecordBackListener();
    throw error;
  }
}

export async function stopAudioCapture(): Promise<string> {
  if (!isCapturing) return '';

  try {
    const result = await Sound.stopRecorder();
    return result;
  } finally {
    isCapturing = false;
    Sound.removeRecordBackListener();
  }
}