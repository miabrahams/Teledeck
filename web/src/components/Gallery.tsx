import React, { useState, useCallback } from 'react';
import MediaCard from './MediaCard';
import FullscreenView from './FullScreenView';
import { ContextMenu, ContextMenuState } from './ContextMenu';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { SearchPreferences, MediaItem } from '@/lib/types';
import { useGallery, useTotalPages, useGalleryMutations } from '@/lib/api';
import { currentPageAtom, searchPrefsAtom } from '@/lib/prefs';
import { useAtomValue, useAtom } from 'jotai';

export const PaginatedMediaGallery: React.FC = () => {
  const [currentPage, setCurrentPage] = useAtom(currentPageAtom);
  const searchPrefs = useAtomValue(searchPrefsAtom);

  const [contextMenu, setContextMenu] = useState<ContextMenuState>({ x: 0, y: 0, item: null });
  const [fullscreenItem, setFullscreenItem] = useState(null);

  const {toggleFavorite, deleteItem} = useGalleryMutations();
  let {data: totalPages} = useTotalPages(searchPrefs);
  if (!totalPages) {
    totalPages = 1;
  }

  const handleContextAction = async (action: string, id: string) => {
    switch (action) {
      case 'download':
        // TODO: implement
        console.error("Not implemented");
        break;
      case 'favorite':
        toggleFavorite.mutate({ itemId: id, searchPrefs, page: currentPage });
        break;
      case 'delete':
        // TODO: Implement "Undo" function on the server. May be a challenge!
        deleteItem.mutate({itemId: id, page: currentPage, searchPrefs});
        break;
    }
    setContextMenu({...contextMenu, item: null});
  };

  const changePage = useCallback((n: number) => {
    if (n < 1 || n > totalPages) {
      return;
    }
    setCurrentPage(n);
  }, [totalPages, setCurrentPage]);

  const openContextMenu = useCallback((e: React.MouseEvent, item: MediaItem) => {
    e.preventDefault();
    setContextMenu({
      x: e.pageX,
      y: e.pageY,
      item
    });
  }, [])


  return (

    <div id="media-index">
      <Pagination currentPage={currentPage} totalPages={totalPages} changePage={changePage} />
        <MediaGallery
          currentPage={currentPage}
          searchPrefs={searchPrefs}
          openContextMenu={openContextMenu}
          handleContextAction={handleContextAction}
          setFullscreenItem={setFullscreenItem}
        />
      <Pagination currentPage={currentPage} totalPages={totalPages} changePage={changePage} />

      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          item={contextMenu.item}
          onClose={() => setContextMenu({...contextMenu, item: null})}
          onAction={handleContextAction}
        />
      )}

      {fullscreenItem && (
        <FullscreenView
          item={fullscreenItem}
          onClose={() => {setFullscreenItem(null)}}
        />
      )}
    </div>

  );
};





type MediaGalleryProps = {
  searchPrefs: SearchPreferences;
  currentPage: number;
  openContextMenu: (e: React.MouseEvent, item: MediaItem) => void;
  handleContextAction: (action: string, id: string) => void;
  setFullscreenItem: Function;
};

const MediaGallery: React.FC<MediaGalleryProps> = ({
  searchPrefs,
  currentPage,
  openContextMenu,
  handleContextAction,
  setFullscreenItem,
}) => {
  const { data: idData, isLoading, error } = useGallery(searchPrefs, currentPage);

  if (isLoading || !idData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 p-4">
        <p>Error loading media: {error.message}</p>
        <button className="mt-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="media-gallery" id="gallery">
      {idData.map((item) => (
        <MediaCard
          key={item.id}
          itemId={item.id}
          handleContextMenu={openContextMenu}
          onFavorite={() => handleContextAction('favorite', item.id)}
          onDelete={() => handleContextAction('delete', item.id)}
          setFullscreenItem={setFullscreenItem}
        />
      ))}
    </div>
  );
};

type PaginationProps = {
  currentPage: number;
  totalPages: number;
  changePage: (n: number) => void;
};

const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  changePage,
}) => {
  return (
    <div className="flex justify-center items-center gap-4 mt-8">
      {currentPage > 1 && (
        <button
          onClick={() => changePage(currentPage - 1)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          <ChevronLeft className="w-4 h-4" />
          Previous
        </button>
      )}

      <span className="text-sm text-gray-600 dark:text-gray-400">
        Page {currentPage} of {totalPages}
      </span>

      {currentPage < totalPages && (
        <button
          onClick={() => changePage(currentPage + 1)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Next
          <ChevronRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default PaginatedMediaGallery;