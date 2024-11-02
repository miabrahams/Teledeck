import { SearchPreferences } from '@shared/types/preferences';

// TODO: This is extremely simple for now, but could deal with more complex serialization
export const createPreferenceString = (preferences: SearchPreferences | SearchPreferences & {page: number}) => {
  return Object.entries(preferences)
    .map(([key, value]) => `${key}=${value}`)
    .join('&');
};