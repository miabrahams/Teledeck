import { useQuery, useMutation, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { MediaItem, Preferences } from '@/lib/types';

type PaginatedResponse = {
  items: MediaItem[];
  totalPages: number;
  currentPage: number;
};

type MediaID = {id : string}

type ApiError = {
  message: string;
};

// Convert to string
const createPreferenceString = (preferences: Preferences) => {
  return Object.entries(preferences)
    .map(([key, value]) => `${key}=${value}`)
    .join('&');
}

const createPreferenceQuery = (preferences: Preferences, page: number) => {
  return createPreferenceString(preferences) + '&page=' + page.toString();
};

// Hook to fetch paginated list of IDs
export const useGalleryIds = (preferences: Preferences, page: number) => {
  return useQuery({
    queryKey: ['mediaIds', createPreferenceString(preferences), page],
    queryFn: () =>
      fetch(`/api/gallery/ids?${createPreferenceQuery(preferences, page)}`)
      .then(res => res.json()) as Promise<MediaID[]>,
    staleTime: Infinity,  // Disable automatic refetching
  });
};


// Hook to fetch individual media items
export const useMediaItem = (itemId: string) => {
  return useQuery({
    queryKey: ['mediaItem', itemId],
    queryFn: () => fetch(`/api/media/${itemId}`).then(res => res.json()),
    staleTime: Infinity,
    enabled: !!itemId,
  });
};

// Unused??
export const useGallery = (preferences: Preferences, page: number) => {
  const queryClient = useQueryClient();
  return useQuery<MediaID[], ApiError>({
    queryKey: ['media', page],
    queryFn: async () => {
      const res = await fetch(`/api/gallery?${createPreferenceQuery(preferences, page)}`);
      const gallery = await res.json() as MediaItem[];

      gallery.forEach(mediaItem => {
        queryClient.setQueryData(['mediaItem', mediaItem.id], mediaItem);
      });
      return gallery.map((item) => {return {id: item.id}})
    },
    staleTime: Infinity,
  });
};

// Hook to fetch multiple media items at once
// TODO: Not used. Look into this
/*
export const useMediaItems = (ids: string[]): UseQueryResult<MediaItem[]> => {
  return useQuery({
    queryKey: ['mediaItems', ids],
    queryFn: () =>
      Promise.all(ids.map(id =>
        fetch(`/api/media/${id}`).then(res => res.json())
      )),
    staleTime: Infinity,
    enabled: ids.length > 0
  });
};
*/


// Mutation hook for toggling favorites
export const useToggleFavorite = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (itemId: string) => {

      // Optimistically query containing this item
      const itemKey = ['mediaItem', itemId]
      const mediaItem = queryClient.getQueryData<MediaItem>(itemKey);
      if (mediaItem) {
        queryClient.setQueryData(itemKey, {...mediaItem, favorite: !mediaItem.favorite })
      };

      const response = await fetch(`/api/media/${itemId}/favorite`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error('Failed to toggle favorite');
      }
      console.log("Favorited...")
      return response.json() as Promise<MediaItem>;
    },
    onSuccess: (updatedItem) => {
      // Update the individual item cache
      console.log("Updating fav: ", updatedItem)
      queryClient.setQueryData(
        ['mediaItem', updatedItem.id],
        updatedItem
      );
    }
  });
};

export const useTotalPages = (preferences: Preferences) => {
  return useQuery<number>({
    queryKey: ['totalPages', createPreferenceString(preferences)],
    queryFn: () =>
      fetch(`/api/gallery/totalPages?${createPreferenceString(preferences)}`)
      .then(res => res.json()),
})}


type deleteParams = {itemId: string, page: number, preferences: Preferences}

export const useDeleteItem = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({itemId, page, preferences}: deleteParams) => {

      // Optimistically remove this item from page
      const pageIdKey = ['mediaIds', createPreferenceString(preferences), page]
      const currentPage = queryClient.getQueryData<MediaID[]>(pageIdKey);
      if (currentPage) {
        queryClient.setQueryData(pageIdKey, currentPage.filter(id => id.id !== itemId));
      };

      const response = await fetch(`/api/media/${itemId}`, { method: 'DELETE' });
      if (!response.ok) {
        throw new Error('Failed to delete item: ' + response.statusText);
      }
      return itemId;
    },
    onSuccess: (data, variables, context) => {
      console.log('Deleted item', data);
      console.log('Deleted variables', variables);
      console.log('Deletion context', context);
      queryClient.invalidateQueries({ queryKey: ['mediaIds'] });
    },
    onError: (error, variables, context) => {
      // An error happened!
      console.log('Deletion error:', context)
      console.log('Deletion error:', variables)
      console.log('Deletion error:', error)
    },
  });
};

// Auth hooks remain the same...
export const useUser = () => {
  return useQuery({
    queryKey: ['user'],
    queryFn: () => { return fetch('/api/me').then(res => res.json()); },
    retry: false,
    staleTime: Infinity,
  });
};

export const useLogout = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const response = await fetch('/api/logout', { method: 'POST' });
      if (!response.ok) {
        throw new Error('Logout failed');
      }
    },
    onSuccess: () => {
      queryClient.setQueryData(['user'], null);
      queryClient.invalidateQueries({ queryKey: ['media'] });
    },
  });
};