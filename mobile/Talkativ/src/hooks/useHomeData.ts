import { useState, useEffect, useCallback } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { getMyProfile, getUserStats, UserProfile, UserStats } from '../services/apiUser';
import { getActiveSessions, ActiveSession } from '../services/apiSession';
import { ConversationPreview, getConversationPreviewMapByAvatar } from '../services/conversationPreview';
import { fetchMyVocabulary } from '../services/apiVocabulary';

export const useHomeData = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conversationPreviews, setConversationPreviews] = useState<Record<string, ConversationPreview>>({});

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      const [profileResult, statsResult, sessionsResult, previewResult, vocabResult] =
        await Promise.allSettled([
          getMyProfile(),
          getUserStats(),
          getActiveSessions(),
          getConversationPreviewMapByAvatar(),
          fetchMyVocabulary(),
        ]);

      if (profileResult.status === 'fulfilled') setProfile(profileResult.value);
      if (sessionsResult.status === 'fulfilled') setActiveSessions(sessionsResult.value);
      if (previewResult.status === 'fulfilled') setConversationPreviews(previewResult.value);

      const baseStats: UserStats =
        statsResult.status === 'fulfilled'
          ? statsResult.value
          : { completedSessions: 0, learnedExpressions: 0, practiceMinutes: 0, progressPercent: 0 };

      if (vocabResult.status === 'fulfilled') {
        const words = vocabResult.value.filter(v => v.kind === 'word').length;
        const phrases = vocabResult.value.filter(v => v.kind === 'phrase').length;
        setStats({ ...baseStats, learnedWords: words, learnedPhrases: phrases });
      } else {
        setStats({ ...baseStats, learnedWords: 0, learnedPhrases: 0 });
      }
    } catch (err) {
      setError('Failed to load home data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  // Refetch when the home tab regains focus (e.g. after saving vocab in the
  // post-chat summary or deleting in the saved-vocabulary screen).
  useFocusEffect(useCallback(() => { fetchAll(); }, [fetchAll]));

  return { profile, stats, activeSessions, conversationPreviews, loading, error };
};
