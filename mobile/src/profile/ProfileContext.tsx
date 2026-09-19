import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { deleteProfile, loadProfile, saveProfile } from './storage';
import { EMPTY_PROFILE, type Profile } from './types';

interface ProfileState {
  profile: Profile;
  /** False until the saved profile has been read from the phone. */
  ready: boolean;
  /** True once the person has finished or skipped setup. */
  hasProfile: boolean;
  setProfile: (profile: Profile) => Promise<void>;
  clearProfile: () => Promise<void>;
}

const ProfileContext = createContext<ProfileState | null>(null);

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const [profile, setState] = useState<Profile>(EMPTY_PROFILE);
  const [ready, setReady] = useState(false);
  const [hasProfile, setHasProfile] = useState(false);

  useEffect(() => {
    loadProfile()
      .then((saved) => {
        if (saved) {
          setState(saved);
          setHasProfile(true);
        }
      })
      .catch(() => undefined)
      .finally(() => setReady(true));
  }, []);

  const setProfile = useCallback(async (next: Profile) => {
    setState(next);
    setHasProfile(true);
    await saveProfile(next);
  }, []);

  const clearProfile = useCallback(async () => {
    setState(EMPTY_PROFILE);
    await deleteProfile();
    await saveProfile(EMPTY_PROFILE); // keep "setup done" so onboarding doesn't reappear
  }, []);

  const value = useMemo(
    () => ({ profile, ready, hasProfile, setProfile, clearProfile }),
    [profile, ready, hasProfile, setProfile, clearProfile],
  );
  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

export function useProfile(): ProfileState {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error('useProfile must be used inside ProfileProvider');
  return ctx;
}
