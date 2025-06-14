import { atom, getDefaultStore } from 'jotai'
import { atomWithStorage, createJSONStorage  } from 'jotai/utils';
import { SortOption, FavoriteOption } from '@shared/types/preferences';
import { defaultPreferences } from './constants';

const storage = createJSONStorage<any>(() => localStorage)
const opts = { getOnInit: true }
export const sortModeAtom = atomWithStorage<SortOption>('sortMode', 'date_desc', storage, opts)
export const videosOnlyAtom = atomWithStorage<boolean>('videosOnly', false, storage, opts)
export const favoritesAtom = atomWithStorage<FavoriteOption>('showFavorites', 'all', storage, opts)
export const searchStringAtom = atomWithStorage<string>('searchString', '', storage, opts)
export const darkModeAtom = atomWithStorage<boolean>('darkmode', true, storage, opts)
export const hideInfoAtom = atomWithStorage<boolean>('hideinfo', false, storage, opts)


export const searchPrefsAtom = atom(
  (get) => {return {
    sort: get(sortModeAtom),
    videos: get(videosOnlyAtom),
    favorites: get(favoritesAtom),
    search: get(searchStringAtom),
}},
  (_, set, key: string, value: any) => {
    switch (key) {
      case 'sort':
        return set(sortModeAtom, value);
      case 'videos':
        return set(videosOnlyAtom, value);
      case 'favorites':
        return set(favoritesAtom, value);
      case 'search':
        return set(searchStringAtom, value);
      default:
        console.error(`Invalid search preference key: ${key}`);
    }
})

export const viewPrefsAtom = atom(
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


export const prefsAtom = atom(
  (get) => {return {
      search: get(searchPrefsAtom),
      view: get(viewPrefsAtom),
    }
  },
  (_, set, key: string, value: any) => {
    if (key in defaultPreferences.search) {
      return set(searchPrefsAtom, key, value);
    }
    else if (key in defaultPreferences.view) {
      return set(viewPrefsAtom, key, value);
    }
    else {
      console.error(`Invalid preference key: ${key}`);
    }
})

const defaultStore = getDefaultStore();

defaultStore.sub(darkModeAtom, () => {
    defaultStore.get(darkModeAtom) ?
        document.documentElement.classList.add('dark')
      : document.documentElement.classList.remove('dark');
});

defaultStore.sub(hideInfoAtom, () => {
    defaultStore.get(hideInfoAtom) ?
        document.documentElement.classList.add('hide-info')
      : document.documentElement.classList.remove('hide-info');
});

// See if this works
defaultStore.sub(prefsAtom, () => {
  localStorage.setItem('userPreferences', JSON.stringify(defaultStore.get(prefsAtom)));
});
