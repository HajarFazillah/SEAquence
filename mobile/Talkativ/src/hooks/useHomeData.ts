import { useState, useEffect } from 'react';
import { getMyProfile, getUserStats, UserProfile, UserStats } from '../services/apiUser';
import { getActiveSessions, ActiveSession } from '../services/apiSession';
import { ConversationPreview, getConversationPreviewMapByAvatar } from '../services/conversationPreview';

export const useHomeData = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conversationPreviews, setConversationPreviews] = useState<Record<string, ConversationPreview>>({});

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true);
        const [profileResult, statsResult, sessionsResult, previewResult] = await Promise.allSettled([
          getMyProfile(),
          getUserStats(),
          getActiveSessions(),
          getConversationPreviewMapByAvatar(),
        ]);

        if (profileResult.status === 'fulfilled') setProfile(profileResult.value);
        if (statsResult.status === 'fulfilled') setStats(statsResult.value);
        if (sessionsResult.status === 'fulfilled') setActiveSessions(sessionsResult.value);
        if (previewResult.status === 'fulfilled') setConversationPreviews(previewResult.value);

      } catch (err) {
        setError('Failed to load home data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  return { profile, stats, activeSessions, conversationPreviews, loading, error };
};
