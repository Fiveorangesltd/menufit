import { useState, useEffect } from 'react';
import type { UserProfile } from '../types';

const PROFILE_KEY = 'menufit_profile';
const USER_ID_KEY = 'menufit_user_id';

export function useLocalProfile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem(PROFILE_KEY);
    const savedId = localStorage.getItem(USER_ID_KEY);
    if (saved) setProfile(JSON.parse(saved));
    if (savedId) setUserId(savedId);
  }, []);

  const saveProfile = (p: UserProfile, id: string) => {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(p));
    localStorage.setItem(USER_ID_KEY, id);
    setProfile(p);
    setUserId(id);
  };

  const clearProfile = () => {
    localStorage.removeItem(PROFILE_KEY);
    localStorage.removeItem(USER_ID_KEY);
    setProfile(null);
    setUserId(null);
  };

  return { profile, userId, saveProfile, clearProfile };
}
