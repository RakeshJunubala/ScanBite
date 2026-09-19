// The health profile is kept in the phone's encrypted store and never sent to the server.
import * as SecureStore from 'expo-secure-store';

import { EMPTY_PROFILE, type Profile } from './types';

const KEY = 'health_profile_v1';

export async function loadProfile(): Promise<Profile | null> {
  const raw = await SecureStore.getItemAsync(KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<Profile>;
    return { ...EMPTY_PROFILE, ...parsed };
  } catch {
    return null;
  }
}

export async function saveProfile(profile: Profile): Promise<void> {
  await SecureStore.setItemAsync(KEY, JSON.stringify(profile));
}

export async function deleteProfile(): Promise<void> {
  await SecureStore.deleteItemAsync(KEY);
}
