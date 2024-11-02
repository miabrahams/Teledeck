// Types to match your Go models
export type MediaItem = {
  id: string;
  file_name: string;
  MediaType: string;
  favorite: boolean;
  channelTitle: string;
  created_at: string;
  TelegramDate: string;
  TelegramText: string;
};

export type MediaGalleryProps = {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
};

export const sortOptions = {
  'date_desc': 'Newest posts first',
  'date_asc': 'Oldest posts first',
  'id_desc': 'Recent additions first',
  'id_asc': 'Oldest additions first',
  'size_desc': 'Largest files first',
  'size_asc': 'Smallest files first',
  'random': 'Random'
};

export const favoriteOptions = {
  'all': 'View all posts',
  'favorites': 'Favorites only',
  'non-favorites': 'Non-favorites only',
};

export type SearchPreferences = {
  sort: keyof typeof sortOptions;
  videos: boolean;
  favorites: keyof typeof favoriteOptions;
  search: string;
};

export type ViewPreferences = {
  darkmode: boolean;
  hideInfo: boolean;
}

export type SavedPreferences = {
  search: SearchPreferences,
  view: ViewPreferences,
}


export type User = {
  email: string;
} | null;

