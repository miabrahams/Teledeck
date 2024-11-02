import axios from 'axios';
import { SearchPreferences } from '@shared/types/preferences';
import { API_ENDPOINTS } from './constants';
import { createPreferenceString } from '@shared/api/serialization';
import { MediaID, MediaItem } from '@shared/types/media';
import { User } from '@shared/types/user';


const instance = axios.create()



type ROUTE = typeof API_ENDPOINTS[keyof typeof API_ENDPOINTS];
export const withPreferences = (route: ROUTE, preferences: Parameters<typeof createPreferenceString>[0]) => {
  return `${route}?${createPreferenceString(preferences)}`
}

export const getTotalPages = async (preferences: SearchPreferences): Promise<number> => {
  const res = await instance.get(withPreferences(API_ENDPOINTS.total_pages, preferences));
  return await res.data;
}
export const getGalleryPage = async (preferences: SearchPreferences, page: number): Promise<MediaItem[]> => {
  const res = await instance.get(withPreferences(API_ENDPOINTS.gallery, {...preferences, page}));
  return await res.data;
}


export const getGalleryIds = async (preferences: SearchPreferences): Promise<MediaID[]> => {
  const res = await instance.get(withPreferences(API_ENDPOINTS.gallery_ids, preferences));
  return await res.data;
}

export const getMediaItem = async (itemId: string): Promise<MediaItem> => {
  const res = await instance.get(`/api/media/${itemId}`)
  return await res.data as MediaItem
}

export const getUser = async (): Promise<User> => {
  const res = await instance.get(`/api/me`)
  return await res.data
}

export const postLogout = async (): Promise<boolean> => {
  const res = await instance.post('/api/logout');
  return res.status === 200;
}

export const postFavorite = async (itemId: string): Promise<MediaItem> => {
  const res = await instance.post(`/api/media/${itemId}/favorite`)
  return res.data as MediaItem;
}

export const deleteItem = async (itemId: string): Promise<boolean> => {
  const res = await instance.delete(`/api/media/${itemId}`)
  return res.status === 200;
}


export default instance