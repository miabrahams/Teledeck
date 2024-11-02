import {
  useQuery,
  useMutation,
  useQueryClient,
  QueryClient,
} from '@tanstack/react-query';
import { MediaItem, Preferences } from '@/lib/types';

type MediaID = { id: string };

type ApiError = {
  message: string;
};

type mutationParams = { itemId: string; page: number; preferences: Preferences };

// TODO: Axios?

const createPreferenceString = (preferences: Preferences) => {
  return Object.entries(preferences)
    .map(([key, value]) => `${key}=${value}`)
    .join('&');
};

const createPreferenceQuery = (preferences: Preferences, page: number) => {
  return createPreferenceString(preferences) + '&page=' + page.toString();
};

const queryKeys = {
  gallery: {
    ids: (preferences: Preferences, page: number) =>
      ['gallery', 'ids', createPreferenceString(preferences), page.toString()] as const,
    item: (id: string) =>
      ['gallery', 'item', id] as const,
    numPages: (preferences: Preferences) =>
      ['gallery', 'pages', createPreferenceString(preferences)] as const
  },
  user: {
    me: ['user'] as const
  }
};

export const useTotalPages = (preferences: Preferences) => {
  return useQuery<number>({
    queryKey: queryKeys.gallery.numPages(preferences),
    queryFn: () =>
      fetch(
        `/api/gallery/totalPages?${createPreferenceString(preferences)}`
      ).then((res) => res.json()),
  });
};


// Hook to fetch paginated list of IDs
/*
export const useGalleryIds = (preferences: Preferences, page: number) => {
  return useQuery({
    queryKey: queryKeys.gallery.ids(preferences, page),
    queryFn: () =>
      fetch(
        `/api/gallery/ids?${createPreferenceQuery(preferences, page)}`
      ).then((res) => res.json()) as Promise<MediaID[]>,
    staleTime: Infinity,
  });
};
*/

// Hook to fetch individual media items
export const useMediaItem = (itemId: string) => {
  return useQuery({
    queryKey: queryKeys.gallery.item(itemId),
    queryFn: () => fetch(`/api/media/${itemId}`).then((res) => res.json()),
    staleTime: Infinity,
    enabled: !!itemId,
  });
};

// Prepopulate media items from full query and return ids only
const fetchGalleryPage = async (
  queryClient: QueryClient,
  preferences: Preferences,
  page: number
) => {
  const res = await fetch(
    `/api/gallery?${createPreferenceQuery(preferences, page)}`
  );
  const gallery = (await res.json()) as MediaItem[];

  gallery.forEach((mediaItem) => {
    queryClient.setQueryData(['mediaItem', mediaItem.id], mediaItem);
  });
  return gallery.map((item) => {
    return { id: item.id };
  });
};

const prefetchGalleryPage = async (
  queryClient: QueryClient,
  preferences: Preferences,
  page: number
) => {
  queryClient.prefetchQuery({
    queryKey: queryKeys.gallery.ids(preferences, page),
    queryFn: () => fetchGalleryPage(queryClient, preferences, page),
  });
};

export const useGallery = (preferences: Preferences, page: number) => {
  const queryClient = useQueryClient();
  return useQuery<MediaID[], ApiError>({
    queryKey: queryKeys.gallery.ids(preferences, page),
    queryFn: async () => {
      prefetchGalleryPage(queryClient, preferences, page - 1);
      prefetchGalleryPage(queryClient, preferences, page + 1);
      return fetchGalleryPage(queryClient, preferences, page);
    },
    staleTime: Infinity,
  });
};


// Fetch paginated list of IDs only (unused)
/*
export const useGalleryIds = (preferences: Preferences, page: number) => {
  return useQuery({
    queryKey: queryKeys.gallery.ids(preferences, page),
    queryFn: () =>
      fetch(
        `/api/gallery/ids?${createPreferenceQuery(preferences, page)}`
      ).then((res) => res.json()) as Promise<MediaID[]>,
    staleTime: Infinity,
  });
};
*/

export const optimisticRemove = (queryClient: QueryClient, {itemId, preferences, page}: mutationParams) => {
  const pageIdKey = queryKeys.gallery.ids(preferences, page);
  const currentPage = queryClient.getQueryData<MediaID[]>(pageIdKey);
  if (currentPage) {
    queryClient.setQueryData(
      pageIdKey,
      currentPage.filter((id) => id.id !== itemId)
    );
  }
}

const invalidatePageIds = (queryClient: QueryClient) => {
  queryClient.invalidateQueries({ queryKey: ['mediaIds'] });
}

// Mutation hook for toggling favorites
export const useGalleryMutations = () => {
  const queryClient = useQueryClient();

  return {
  toggleFavorite: useMutation({
    mutationFn: async (params: mutationParams) => {
      // Optimistically update query containing this item
      const itemKey = queryKeys.gallery.item(params.itemId);
      const mediaItem = queryClient.getQueryData<MediaItem>(itemKey);
      if (mediaItem) {
        queryClient.setQueryData(itemKey, {
          ...mediaItem,
          favorite: !mediaItem.favorite,
        });
      }

      // If we're filtering by favorite status, toggling favorite on something visible will make it disappear
      if (params.preferences.favorites !== 'all') {
        console.log("Optimistic remove")
        optimisticRemove(queryClient, params);
      }

      const response = await fetch(`/api/media/${params.itemId}/favorite`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to toggle favorite');
      }
      return response.json() as Promise<MediaItem>;
    },
    onSuccess: (updatedItem, variables) => {
      // Update the individual item cache
      queryClient.setQueryData(['mediaItem', updatedItem.id], updatedItem);

      if (variables['preferences'].favorites !== 'all') {
        invalidatePageIds(queryClient)
      }
    },
  }),
  deleteItem: useMutation({
    mutationFn: async (params: mutationParams) => {
      // Optimistically remove this item from page
      optimisticRemove(queryClient, params);

      const response = await fetch(`/api/media/${params.itemId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete item: ' + response.statusText);
      }
      return Promise.resolve(true);
    },
    onSuccess: () => {invalidatePageIds(queryClient)},
    onError: (error, variables, context) => {
      // An error happened!
      console.log('Deletion error:', context);
      console.log('Deletion error:', variables);
      console.log('Deletion error:', error);
    }})
  }
}

// Auth hooks remain the same...
export const useUser = () => {
  return useQuery({
    queryKey: queryKeys.user.me,
    queryFn: () => {
      return fetch('/api/me').then((res) => res.json());
    },
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
      queryClient.invalidateQueries();
    },
  });
};
