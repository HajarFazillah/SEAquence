import { useState, useEffect } from 'react';
import { getMyProfile, getUserStats, UserProfile, UserStats } from '../services/apiUser';
import { getActiveSessions, ActiveSession } from '../services/apiSession';

export const useHomeData = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [activeSessions, setActiveSessions] = useState<ActiveSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true);
        const [profileResult, statsResult, sessionsResult] = await Promise.allSettled([
          getMyProfile(),
          getUserStats(),
          getActiveSessions(),
        ]);

        if (profileResult.status === 'fulfilled') setProfile(profileResult.value);
        if (statsResult.status === 'fulfilled') setStats(statsResult.value);
        if (sessionsResult.status === 'fulfilled') setActiveSessions(sessionsResult.value);

      } catch (err) {
        setError('Failed to load home data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  return { profile, stats, activeSessions, loading, error };
};
