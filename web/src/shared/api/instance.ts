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

export const getTotalPages = async (preferences: SearchPreferences) => {
  const res = await instance.get(withPreferences(API_ENDPOINTS.total_pages, preferences));
  return await res.data as number;
}
export const getGalleryPage = async (preferences: SearchPreferences, page: number) => {
  const res = await instance.get(withPreferences(API_ENDPOINTS.gallery, {...preferences, page}));
  return await res.data as MediaItem[];
}


export const getGalleryIds = async (preferences: SearchPreferences) => {
  const res = await instance.get(withPreferences(API_ENDPOINTS.gallery_ids, preferences));
  return await res.data as MediaID[];
}

export const getMediaItem = async (itemId: string) => {
  const res = await instance.get(`/api/media/${itemId}`)
  return await res.data as MediaItem
}

export const getUser = async () => {
  const res = await instance.get(`/api/me`)
  return await res.data as User
}

export const postLogout = async () => {
  const res = await instance.post('/api/logout');
  return res.data;
}

export const postFavorite = async (itemId: string) => {
  const res = await instance.post(`/api/media/${itemId}/favorite`)
  return res.data as MediaItem;
}

export const deleteItem = async (itemId: string) => {
  const res = await instance.delete(`/api/media/${itemId}`)
  return res
}


export default instance