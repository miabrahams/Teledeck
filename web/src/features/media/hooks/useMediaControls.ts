import { useState, useCallback } from 'react';
import { useGalleryMutations } from '@media/api';
import { useAtomValue } from 'jotai';
import { currentPageAtom } from '@gallery/state';
import { searchPrefsAtom } from '@preferences/state';

export const useMediaControls = ( itemId: string ) => {
  const [isHovering, setIsHovering] = useState(false);
  const { toggleFavorite, deleteItem } = useGalleryMutations();
  const page = useAtomValue(currentPageAtom);
  const searchPrefs = useAtomValue(searchPrefsAtom);

  const handleFavorite = useCallback(() => {
    toggleFavorite.mutate({ itemId, page, searchPrefs });
  }, [itemId, page, searchPrefs, toggleFavorite]);

  const handleDelete = useCallback(() => {
    deleteItem.mutate({ itemId, page, searchPrefs });
  }, [itemId, page, searchPrefs, deleteItem]);

  const handleDownload = useCallback((fileName: string) => {
    window.open(`/media/${fileName}`, '_blank');
  }, []);

  return {
    isHovering,
    setIsHovering,
    handleFavorite,
    handleDelete,
    handleDownload,
    isFavoriting: toggleFavorite.isPending,
    isDeleting: deleteItem.isPending,
  };
};
