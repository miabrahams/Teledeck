// core/types/media.ts
export type MediaType = 'image' | 'video' | 'photo';

export type MediaID = { id: string };

export type BaseMedia = {
  id: string;
  fileName: string;
  MediaType: MediaType;
  created_at: string;
  favorite: boolean;
};

export type MediaMetadata = {
  width?: number;
  height?: number;
  duration?: number;
  size: number;
  mimeType: string;
};

export type TelegramMediaItem = BaseMedia & {
  channelTitle: string;
  TelegramDate: string;
  TelegramText: string;
};

// TODO: Support different sources
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
