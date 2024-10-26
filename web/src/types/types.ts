
// Types to match your Go models
export type MediaItem = {
  id: string;
  fileName: string;
  mediaType: string;
  favorite: boolean;
  channelTitle: string;
  createdAt: string;
  telegramText: string;
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
  page?: number;
  darkmode: boolean;
};

export type User = {
  email: string;
} | null;
