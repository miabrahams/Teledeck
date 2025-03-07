import { useState, useCallback, useEffect } from 'react';
import { useGallery } from '@gallery/api';
import { useMediaItem } from '../api';
import { MediaItem } from '@shared/types/media';
import { SearchPreferences } from '@shared/types/preferences';
import { ApiError } from '@shared/types/api';

interface MediaNavigationResult {
  currentItem: MediaItem | undefined;
  currentIndex: number;
  totalItems: number;
  isLoading: boolean;
  error: ApiError | null;
  goToNext: () => void;
  goToPrevious: () => void;
  goToIndex: (index: number) => void;
}

export const useMediaNavigation = (
  searchPrefs: SearchPreferences,
  initialPage = 1,
  initialIndex = 0
): MediaNavigationResult => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const {
    data: galleryIds,
    isLoading: isLoadingGallery,
    error: galleryError
  } = useGallery(searchPrefs, initialPage);

  // Get current item ID
  const currentItemId = galleryIds?.[currentIndex]?.id;

  // Fetch current media item details
  const {
    data: currentItem,
    isLoading: isLoadingItem,
    error: itemError
  } = useMediaItem(currentItemId || '');

  // Navigation methods
  const goToNext = useCallback(() => {
    if (galleryIds && currentIndex < galleryIds.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  }, [galleryIds, currentIndex]);

  const goToPrevious = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  }, [currentIndex]);

  const goToIndex = useCallback((index: number) => {
    if (galleryIds && index >= 0 && index < galleryIds.length) {
      setCurrentIndex(index);
    }
  }, [galleryIds]);

  // Reset index if gallery changes (e.g. search preferences change)
  useEffect(() => {
    setCurrentIndex(0);
  }, [searchPrefs]);

  return {
    currentItem,
    currentIndex,
    totalItems: galleryIds?.length || 0,
    isLoading: isLoadingGallery || isLoadingItem,
    error: galleryError || itemError || null,
    goToNext,
    goToPrevious,
    goToIndex
  };
};
