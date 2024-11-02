import { sortOptions, favoriteOptions } from '@navigation/constants';

export type SortOption = keyof typeof sortOptions;
export type FavoriteOption = keyof typeof favoriteOptions;

export type SearchPreferences = {
  sort: SortOption;
  videos: boolean;
  favorites: FavoriteOption;
  search: string;
};

export type ViewPreferences = {
  darkmode: boolean;
  hideinfo: boolean;
}

export type Preferences = {
  search: SearchPreferences,
  view: ViewPreferences,
}
