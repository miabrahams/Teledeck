import axios from 'axios';
import { withPreferences, apiHandler, apiHandlerOK } from '@shared/api/utils';
import { MediaID, MediaItem } from '@shared/types/media';
import { User } from '@shared/types/user';
import { SearchPreferences } from '@shared/types/preferences';
import { API_ENDPOINTS } from './constants';


const instance = axios.create()



export const getTotalPages = async (preferences: SearchPreferences): Promise<number> => {
  const res = instance.get(withPreferences(API_ENDPOINTS.total_pages, preferences));
  return apiHandler(res);
}
export const getGalleryPage = async (preferences: SearchPreferences, page: number): Promise<MediaItem[]> => {
  const res = instance.get(withPreferences(API_ENDPOINTS.gallery, {...preferences, page}));
  return apiHandler(res);
}


export const getGalleryIds = async (preferences: SearchPreferences): Promise<MediaID[]> => {
  const res = instance.get(withPreferences(API_ENDPOINTS.gallery_ids, preferences));
  return apiHandler(res);
}

export const getMediaItem = async (itemId: string): Promise<MediaItem> => {
  const res = instance.get(`/api/media/${itemId}`)
  return apiHandler(res);
}

export const getUser = async (): Promise<User> => {
  const res = instance.get(`/api/me`)
  return apiHandler(res);
}

export const postLogout = async (): Promise<boolean> => {
  const res = instance.post('/api/logout');
  return apiHandlerOK(res);
}

export const postFavorite = async (itemId: string): Promise<MediaItem> => {
  const res = instance.post(`/api/media/${itemId}/favorite`)
  return apiHandler(res);
}

export const deleteItem = async (itemId: string): Promise<boolean> => {
  const res = instance.delete(`/api/media/${itemId}`)
  return apiHandlerOK(res);
}

