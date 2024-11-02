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

export type Preferences = {
  sort: string;
  videos: boolean;
  favorites: string;
  search: string;
  page?: string;
  darkmode: boolean;
};

export type User = {
  email: string;
} | null;
