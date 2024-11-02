// core/constants/index.ts
export const API_ENDPOINTS = {
  total_pages: '/api/gallery/totalPages',

  gallery: '/api/gallery',
  gallery_ids: '/api/gallery/ids',
  MEDIA: '/api/media',
  AUTH: '/api/auth',
  USER: '/api/user',
} as const;

export const MEDIA_TYPES = {
  IMAGE: 'image',
  VIDEO: 'video',
  PHOTO: 'photo',
} as const;

export const QUERY_KEYS = {
  MEDIA: 'media',
  USER: 'user',
  AUTH: 'auth',
} as const;