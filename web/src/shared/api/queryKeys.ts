import { createPreferenceString } from '@shared/api/serialization';
import { SearchPreferences } from '@shared/types/preferences';

const queryKeys = {
  gallery: {
    ids: (preferences: SearchPreferences, page: number) =>
      ['gallery', 'ids', createPreferenceString(preferences), page.toString()] as const,
    numPages: (preferences: SearchPreferences) =>
      ['gallery', 'pages', createPreferenceString(preferences)] as const
  },
  media: {
    item: (id: string) =>
      ['gallery', 'item', id] as const,
  },
  user: {
    me: ['user'] as const
  }
};


export default queryKeys;