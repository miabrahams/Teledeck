import React, { useState, useEffect } from 'react';
import MediaCard from './MediaCard';
import FullscreenView from './FullScreenView';
import ContextMenu from './ContextMenu';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Preferences, MediaItem } from '@/lib/types';
import { useDeleteItem, useGalleryIds, useToggleFavorite } from '@/lib/api';

type MediaGalleryProps = { currentPage: number, totalPages: number, onPageChange: Function, preferences: Preferences };
const MediaGallery: React.FC<MediaGalleryProps> = ( {currentPage, totalPages, onPageChange, preferences} ) => {
  const [contextMenu, setContextMenu] = useState<ContextMenu | null>(null);
  const [fullscreenItem, setFullscreenItem] = useState(null);


  const {data: idData, isLoading, error} = useGalleryIds(preferences, currentPage);

  const handleContextMenu = (e: React.MouseEvent, item: MediaItem) => {
    e.preventDefault();
    setContextMenu({
      x: e.pageX,
      y: e.pageY,
      item
    });
  };

  // data, error, mutateAsync, isError, context, isPending...
  const tf = useToggleFavorite();
  const {mutate: mutDelete} = useDeleteItem();

  const handleContextAction = async (action: string, id: string) => {
    switch (action) {
      case 'download':
        // TODO: implement
        console.error("Not implemented");
        // window.open(`/media/${item.file_name}`, '_blank');
        break;
      case 'favorite':
        tf.mutate(id);
        break;
      case 'delete':
        // if (window.confirm('Are you sure you want to delete this item?')) {
        mutDelete({itemId: id, page: currentPage, preferences});
        // }
        break;
    }
    setContextMenu(null);
  };

  if (isLoading) {
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
        <button
          className="mt-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div id="media-index">
      <div className="media-gallery" id="gallery">
        {idData.map((item) => (
          <MediaCard
            key={item.id}
            itemId={item.id}
            handleContextMenu={handleContextMenu}
            onFavorite={() => handleContextAction('favorite', item.id)}
            onDelete={() => handleContextAction('delete', item.id)}
            setFullscreenItem={setFullscreenItem}
          />
        ))}
      </div>

      {/* Pagination */}
      <Pagination currentPage={currentPage} totalPages={totalPages} changePage={onPageChange} />

      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          item={contextMenu.item}
          onClose={() => setContextMenu(null)}
          onAction={handleContextAction}
        />
      )}

      {fullscreenItem && (
        <FullscreenView
          item={fullscreenItem}
          onClose={() => setFullscreenItem(null)}
        />
      )}
    </div>
  );
};

type PaginationProps = {currentPage: number, totalPages: number, changePage: (n: number) => void}
const Pagination: React.FC<PaginationProps> = ({currentPage, totalPages, changePage}) => {

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
}

export default MediaGallery;