// src/services/api.js
import AsyncStorage from '@react-native-async-storage/async-storage'
const AI_SERVER = 'http://10.240.46.93:8000'; // EC2 배포 시 IP로 교체

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
        detected_level:  data.correction.detected_level || 'unknown',
        is_appropriate:  !data.correction.has_errors,
        feedback_ko:     data.correction.corrections?.[0]?.explanation || null,
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