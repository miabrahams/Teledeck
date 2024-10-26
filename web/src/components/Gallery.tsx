import { useState, useEffect } from 'react';
import MediaItem from './MediaItem';
import FullscreenView from './FullScreenView';
import ContextMenu from './ContextMenu';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const MediaGallery = ({ currentPage, totalPages, onPageChange }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [fullscreenItem, setFullscreenItem] = useState(null);

  useEffect(() => {
    fetchItems();
  }, [currentPage]);

  const fetchItems = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get preferences from localStorage for consistent filtering
      const preferences = JSON.parse(localStorage.getItem('userPreferences')) || {};
      const params = new URLSearchParams({
        ...preferences,
        page: currentPage.toString()
      });

      const response = await fetch(`/api/media?${params}`);
      if (!response.ok) throw new Error('Failed to fetch media items');

      const data = await response.json();
      setItems(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleContextMenu = (e, item) => {
    e.preventDefault();
    setContextMenu({
      x: e.pageX,
      y: e.pageY,
      item
    });
  };

  const handleContextAction = async (action, item) => {
    switch (action) {
      case 'download':
        window.open(`/media/${item.fileName}`, '_blank');
        break;
      case 'favorite':
        try {
          const response = await fetch(`/api/media/${item.id}/favorite`, {
            method: 'POST'
          });
          if (!response.ok) throw new Error('Failed to toggle favorite');
          await fetchItems(); // Refresh the list
        } catch (err) {
          console.error('Error toggling favorite:', err);
        }
        break;
      case 'delete':
        if (!item.favorite) {
          try {
            const response = await fetch(`/api/media/${item.id}`, {
              method: 'DELETE'
            });
            if (!response.ok) throw new Error('Failed to delete item');
            await fetchItems(); // Refresh the list
          } catch (err) {
            console.error('Error deleting item:', err);
          }
        }
        break;
    }
    setContextMenu(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-600 p-4">
        <p>Error loading media: {error}</p>
        <button
          onClick={fetchItems}
          className="mt-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {items.map((item) => (
          <MediaItem
            key={item.id}
            item={item}
            onContextMenu={(e) => handleContextMenu(e, item)}
            onFavorite={() => handleContextAction('favorite', item)}
            onDelete={() => handleContextAction('delete', item)}
            onOpenFullscreen={() => setFullscreenItem(item)}
          />
        ))}
      </div>

      {/* Pagination */}
      <div className="flex justify-center items-center gap-4 mt-8">
        {currentPage > 1 && (
          <button
            onClick={() => onPageChange(currentPage - 1)}
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
            onClick={() => onPageChange(currentPage + 1)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        )}
      </div>

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

export default MediaGallery;