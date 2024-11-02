import {
  useQuery,
  useQueryClient,
  QueryClient,
} from '@tanstack/react-query';
import { MediaItem, MediaID } from '@shared/types/media';
import { ApiError } from '@shared/types/api';
import { SearchPreferences } from '@shared/types/preferences';
import queryKeys from '@shared/api/queryKeys'
import { getGalleryIds, getGalleryPage, getTotalPages } from '@shared/api/instance';

export const useTotalPages = (preferences: SearchPreferences) => {
  return useQuery<number>({
    queryKey: queryKeys.gallery.numPages(preferences),
    queryFn: () => getTotalPages(preferences),
  });
};

// Hook to fetch paginated list of IDs (unused)
export const useGalleryIds = (preferences: SearchPreferences, page: number) => {
  return useQuery({
    queryKey: queryKeys.gallery.ids(preferences, page),
    queryFn: () => getGalleryIds(preferences),
    staleTime: Infinity,
  });
};

// Prepopulate media items from full query and return ids only
const fetchGalleryPage = async (
  queryClient: QueryClient,
  preferences: SearchPreferences,
  page: number
) => {
  const gallery = await getGalleryPage(preferences, page);
  gallery.forEach((mediaItem) => {
    queryClient.setQueryData(['mediaItem', mediaItem.id], mediaItem);
  });
  return gallery.map((item) => {
    return { id: item.id };
  });
};

const prefetchGalleryPage = async (
  queryClient: QueryClient,
  preferences: SearchPreferences,
  page: number
) => {
  if (page < 1) return;
  queryClient.prefetchQuery({
    queryKey: queryKeys.gallery.ids(preferences, page),
    queryFn: () => fetchGalleryPage(queryClient, preferences, page),
  });
};

export const useGallery = (preferences: SearchPreferences, page: number) => {
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
