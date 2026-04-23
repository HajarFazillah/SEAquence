// src/hooks/useChat.js
import { useState, useCallback } from 'react'
import AsyncStorage from '@react-native-async-storage/async-storage'
import { ai } from '../config/api'

export const useChat = (avatar, situation = null) => {
  const [messages, setMessages]         = useState([])
  const [correction, setCorrection]     = useState(null)
  const [mood, setMood]                 = useState({ score: 80, emoji: "😊" })
  const [isLoading, setIsLoading]       = useState(false)
  const [sessionReport, setSessionReport] = useState(null)

  // 대화 기록 → AI 서버 포맷으로 변환
  const toHistory = (msgs) => msgs.map(m => ({
    role:    m.role,     // "user" | "assistant"
    content: m.content,
  }))

  // ── 메시지 전송 ──────────────────────────────────────────
  const sendMessage = useCallback(async (text) => {
    const user_id = await AsyncStorage.getItem('user_id')

    // 1. 사용자 메시지 즉시 화면에 추가
    const userMsg = { role: 'user', content: text, id: Date.now() }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setIsLoading(true)
    setCorrection(null)

    try {
      const res = await fetch(ai.chat, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_message:         text,
          conversation_history: toHistory(messages), // 이전 기록
          avatar:               avatar,
          user_id:              user_id,
          situation:            situation,
        })
      })

      const data = await res.json()

      // 2. 아바타 응답 추가
      const avatarMsg = {
        role:    'assistant',
        content: data.message,
        id:      Date.now() + 1,
      }
      setMessages(prev => [...prev, avatarMsg])

      // 3. 교정 피드백
      if (data.correction?.has_errors) {
        setCorrection(data.correction)
      }

      // 4. 기분 업데이트
      setMood({
        score: data.current_mood,
        emoji: data.mood_emoji,
      })

    } catch (e) {
      console.error('Chat error:', e)
    } finally {
      setIsLoading(false)
    }
  }, [messages, avatar, situation])

  // ── 세션 종료 & 분석 리포트 ──────────────────────────────
  const endSession = useCallback(async () => {
    setIsLoading(true)
    try {
      const res = await fetch(ai.analyze, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          avatar:               avatar,
          conversation_history: toHistory(messages),
        })
      })
      const report = await res.json()
      setSessionReport(report)
      return report
    } catch (e) {
      console.error('Analyze error:', e)
    } finally {
      setIsLoading(false)
    }
  }, [messages, avatar])

  return {
    messages,
    correction,
    mood,
    isLoading,
    sessionReport,
    sendMessage,
    endSession,
  }
}
