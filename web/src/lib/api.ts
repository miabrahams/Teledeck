import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MediaItemType, Preferences } from '@/lib/types';

type PaginatedResponse = {
  items: MediaItemType[];
  totalPages: number;
  currentPage: number;
};

type MediaPage = PaginatedResponse | undefined;

type ApiError = {
  message: string;
};

// Convert to string
const createPreferenceQuery = (preferences: Preferences, page: number) => {
  const preferenceQueryPlus = { ...preferences, page: page };
  return Object.entries(preferenceQueryPlus)
    .map(([key, value]) => `${key}=${value}`)
    .join('&');
};



export const useMedia = (preferences: Preferences, page: number) => {
  return useQuery<PaginatedResponse, ApiError>({
    queryKey: ['media', preferences, page],
    queryFn: () => {
      return fetch(`/api/media?${createPreferenceQuery(preferences, page)}`).then((res) => res.json())
    },
    staleTime: Infinity, // Disable automatic refetching
  });
};

export const useToggleFavorite = () => {
  const queryClient = useQueryClient();
  return useMutation<MediaItemType, ApiError, string> ({
    mutationFn: async (itemId: string) => {
        const response = await fetch(`/api/media/${itemId}/favorite`, { method: 'POST' });
        if (!response.ok) {
          throw new Error('Failed to toggle favorite: ' + response.statusText);
        }
        return response.json();
    },
    onSuccess: (updatedItem) => {
      queryClient.setQueriesData({queryKey: ['media']}, (oldData: MediaPage) => {
        if (!oldData) return oldData;
          return {
          ...oldData,
          items: oldData.items.map(
            (item) => (item.id === updatedItem.id ? updatedItem : item)
          )}
      })
  }})
}

export const useDeleteItem = () => {
  const queryClient = useQueryClient();
  return useMutation<void, ApiError, string>({
    mutationFn: async (itemId: string) => {
      const res = await fetch(`/api/media/${itemId}`, { method: 'DELETE' });
      return await res.json();
    },
    onSuccess: (_, deletedItemId) => {
      queryClient.setQueriesData({queryKey: ['media']}, (oldData: MediaPage) => {
        if (!oldData) return oldData;
        return {
          ...oldData,
          items: oldData.items.filter((item) => item.id !== deletedItemId)
        }
      })
    }
  })
}


// Auth Hooks
export const useUser = () => {
  return useQuery({
    queryKey: ['user'],
    queryFn: () => { return fetch('/api/me').then(res => res.json()); },
    retry: false,
    staleTime: Infinity, // User data doesn't need frequent refreshing
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