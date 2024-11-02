import { atom } from 'jotai'
import { atomWithStorage } from 'jotai/utils';
import { FavoriteOption, SavedPreferences, SortOption } from '@/lib/types';

// Ideas: Zod validation so we don't wreck things? Object.apply?

const defaultPreferences: SavedPreferences = {
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

export const sortModeAtom = atomWithStorage<SortOption>('sortMode', 'date_desc')
export const showVideosAtom = atomWithStorage<boolean>('darkmode', true)
export const favoritesAtom = atomWithStorage<FavoriteOption>('showFavorites', 'all')
export const searchStringAtom = atomWithStorage<FavoriteOption>('searchString', 'all')
export const darkModeAtom = atomWithStorage<boolean>('darkmode', true)
export const hideInfoAtom = atomWithStorage<boolean>('hideinfo', false)


export const searchPrefs = atom(
  (get) => {return {
    sort: get(sortModeAtom),
    videos: get(showVideosAtom),
    favorites: get(favoritesAtom),
    search: get(searchStringAtom),
}},
  (_, set, key: string, value: any) => {
    switch (key) {
      case 'sort':
        return set(sortModeAtom, value);
      case 'videos':
        return set(showVideosAtom, value);
      case 'favorites':
        return set(favoritesAtom, value);
      case 'search':
        return set(searchStringAtom, value);
      default:
        console.error(`Invalid search preference key: ${key}`);
    }
})

export const viewPrefs = atom(
  (get) => {return {
    darkmode: get(darkModeAtom),
    hideinfo: get(hideInfoAtom),
}},
  (_, set, key: string, value: any) => {
    switch (key) {
      case 'darkmode':
        return set(darkModeAtom, value);
      case 'hideinfo':
        return set(hideInfoAtom, value);
      default:
        console.error(`Invalid view preference key: ${key}`);
    }
})


export const prefs = atom(
  (get) => {return {
      search: get(searchPrefs),
      view: get(viewPrefs),
    }
  },
  (_, set, key: string, value: any) => {
    if (key in defaultPreferences.search) {
      return set(searchPrefs, key, value);
    }
    else if (key in defaultPreferences.view) {
      return set(viewPrefs, key, value);
    }
    else {
      console.error(`Invalid preference key: ${key}`);
    }
})
