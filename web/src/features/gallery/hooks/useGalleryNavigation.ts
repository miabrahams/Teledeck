import { useState, useEffect, useCallback } from 'react';
import { useGallery } from '@gallery/api';
import { SearchPreferences } from '@shared/types/preferences';

interface GalleryNavigationResult {
  currentIndex: number;
  totalItems: number;
  isLoading: boolean;
  error: any;
  goToNext: () => void;
  goToPrevious: () => void;
  goToItem: (itemId: string) => void;
  goToIndex: (index: number) => void;
  currentItemId: string | undefined;
}

export const useGalleryNavigation = (
  initialItemId: string | undefined,
  searchPrefs: SearchPreferences,
  initialPage = 1
): GalleryNavigationResult => {
  const [currentIndex, setCurrentIndex] = useState<number>(0);

  // Fetch gallery data based on search preferences
  const {
    data: galleryItems,
    isLoading,
    error
  } = useGallery(searchPrefs, initialPage);

  // Find the index of the initial item in the gallery
  useEffect(() => {
    if (galleryItems && initialItemId) {
      const index = galleryItems.findIndex(item => item.id === initialItemId);
      if (index !== -1) {
        setCurrentIndex(index);
      } else {
        // If item not found, reset to first item
        setCurrentIndex(0);
      }
    }
  }, [initialItemId, galleryItems]);

  const goToNext = useCallback(() => {
    if (galleryItems && currentIndex < galleryItems.length - 1) {
      setCurrentIndex(prev => prev + 1);
    }
  }, [currentIndex, galleryItems]);

  const goToPrevious = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex(prev => prev - 1);
    }
  }, [currentIndex]);

  const goToItem = useCallback((itemId: string) => {
    if (galleryItems) {
      const index = galleryItems.findIndex(item => item.id === itemId);
      if (index !== -1) {
        setCurrentIndex(index);
      }
    }
  }, [galleryItems]);

  const goToIndex = useCallback((index: number) => {
    if (galleryItems && index >= 0 && index < galleryItems.length) {
      setCurrentIndex(index);
    }
  }, [galleryItems]);

  // Get the current item ID based on the index
  const currentItemId = galleryItems?.[currentIndex]?.id;

  return {
    currentIndex,
    totalItems: galleryItems?.length || 0,
    isLoading,
    error,
    goToNext,
    goToPrevious,
    goToItem,
    goToIndex,
    currentItemId
  };
};
