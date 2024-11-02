import { Preferences } from './types'

export const defaultPreferences: Preferences = {
  search: {
    sort: 'date_desc',
    videos: false,
    favorites: 'all',
    search: '',
  },
  view: {
    darkmode: true,
    hideinfo: false,
  },
};
