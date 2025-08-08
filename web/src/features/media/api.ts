import {
  useQuery,
  useMutation,
  useQueryClient,
  QueryClient,
} from '@tanstack/react-query';
import { SearchPreferences } from '@shared/types/preferences';
import { deleteItem, getMediaItem, getThumbnail, postFavorite, undoDelete } from '@shared/api/requests';
import { MediaItem, MediaID } from '@shared/types/media';
import queryKeys from '@shared/api/queryKeys'


// Hook to fetch individual media items
export const useMediaItem = (itemId: string) => {
  return useQuery({
    queryKey: queryKeys.media.item(itemId),
    queryFn: () => getMediaItem(itemId),
    staleTime: Infinity,
    enabled: !!itemId,
  });
};

// Fetch video thumbnail
export const useVideoThumbnail = (itemId: string) => {
  return useQuery({
    queryKey: queryKeys.media.thumbnail(itemId),
    queryFn: () => getThumbnail(itemId),
    staleTime: Infinity,
  });
};


export const optimisticRemove = (queryClient: QueryClient, {itemId, searchPrefs, page}: mutationParams) => {
  const pageIdKey = queryKeys.gallery.ids(searchPrefs, page);
  const currentPage = queryClient.getQueryData<MediaID[]>(pageIdKey);
  if (currentPage) {
    queryClient.setQueryData(
      pageIdKey,
      currentPage.filter((id) => id.id !== itemId)
    );
    console.log("removed item", itemId)
  }
}

export const optimisticAdd = (queryClient: QueryClient, mediaItem: MediaItem, {searchPrefs, page}: mutationParams) => {
  const pageIdKey = queryKeys.gallery.ids(searchPrefs, page);
  const currentPage = queryClient.getQueryData<MediaID[]>(pageIdKey);
  if (currentPage) {


    console.log("Setting query data", mediaItem)
    queryClient.setQueryData(
      queryKeys.media.item(mediaItem.id),
      mediaItem
    );

    queryClient.setQueryData(
      pageIdKey,
      [...currentPage, {id: mediaItem.id}]
    );
  }
}

const invalidatePageIds = (queryClient: QueryClient) => {
  queryClient.invalidateQueries({ queryKey: ['mediaIds'] });
}

// Mutation hooks (favorite, delete)

type mutationParams = { itemId: string; page: number; searchPrefs: SearchPreferences };
export const useGalleryMutations = () => {
  const queryClient = useQueryClient();

  return {
  toggleFavorite: useMutation({
    mutationFn: async (params: mutationParams) => {
      // Optimistically update query containing this item
      const itemKey = queryKeys.media.item(params.itemId);
      const mediaItem = queryClient.getQueryData<MediaItem>(itemKey);
      if (mediaItem) {
        queryClient.setQueryData(itemKey, {
          ...mediaItem,
          favorite: !mediaItem.favorite,
        });
      }

      // If we're filtering by favorite status, toggling favorite on something visible will make it disappear
      if (params.searchPrefs.favorites !== 'all') {
        console.log("Optimistic remove")
        optimisticRemove(queryClient, params);
      }

      return postFavorite(params.itemId)
    },
    onSuccess: (updatedItem, variables) => {
      // Update the individual item cache
      queryClient.setQueryData(['mediaItem', updatedItem.id], updatedItem);

      if (variables['searchPrefs'].favorites !== 'all') {
        invalidatePageIds(queryClient)
      }
    },
  }),
  deleteItem: useMutation({
    mutationFn: async (params: mutationParams) => {
      console.log("deleting", params)
      optimisticRemove(queryClient, params);
      return deleteItem(params.itemId, params.searchPrefs, params.page);
    },
    onSuccess: (mediaItem, params) => {
      if (mediaItem) {
        optimisticAdd(queryClient, mediaItem, params);
      }
      invalidatePageIds(queryClient);
    },
    onError: (error, variables, context) => {
      console.log('Deletion error:', context, variables, error);
    }}),
  undoDelete: useMutation({
    mutationFn: undoDelete,
    onSuccess: (restoredItem) => {
      if (restoredItem) {
        queryClient.setQueryData(['mediaItem', restoredItem.id], restoredItem);
        invalidatePageIds(queryClient);
      }
    },
    onError: (error) => {
      console.log('Undo error:', error);
    }
  })
  }
}