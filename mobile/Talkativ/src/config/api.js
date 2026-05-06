// src/services/api.js
import AsyncStorage from '@react-native-async-storage/async-storage'
import { AI_SERVER_URL } from '../constants';

const AI_SERVER = AI_SERVER_URL;

export const apiService = {

  sendMessage: async (sessionId, userId, text, avatar, situation, history) => {
    const user_id = await AsyncStorage.getItem('user_id') || userId

    const res = await fetch(`${AI_SERVER}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_message:         text,
        conversation_history: history,
        avatar: {
          id:                 avatar?.id         || 'sujin_friend',
          name_ko:            avatar?.name_ko    || '수진',
          role:               avatar?.role       || 'friend',
          personality_traits: avatar?.personality_traits || [],
          interests:          avatar?.interests  || [],
          dislikes:           avatar?.dislikes   || [],
        },
        situation: situation ? {
          title:       situation?.name_ko || situation?.title,
          description: situation?.description,
          location:    situation?.location,
        } : null,
        user_id: user_id,
      })
    })

    const data = await res.json()

    return {
      response:        data.message,
      speech_analysis: data.correction ? {
        detected_level:  data.correction.detected_speech_level_label || data.correction.detected_speech_level || data.correction.detected_level || 'unknown',
        detected_level_code: data.correction.detected_speech_level_code || data.correction.detected_level_code,
        input_kind:      data.correction.input_kind || data.correction.inputKind,
        verdict:         data.correction.verdict,
        is_appropriate:  !data.correction.has_errors,
        feedback_ko:     data.correction.summary || data.correction.corrections?.[0]?.explanation || null,
        accuracy_score:  data.correction.accuracy_score,
        corrections:     data.correction.corrections || [],
      } : null,
      mood_change:     data.mood_change,
      current_mood:    data.current_mood,
      mood_emoji:      data.mood_emoji,
      correct_streak:  data.correct_streak,
    }
  },

}
