import React, { useState } from 'react';
import { Play, Pause, Download, Star, Trash } from 'lucide-react';
import { item } from '@/types/types';

type MediaItemProps = {
  item: item,
  onFavorite: Function,
  onDelete: Function,
  onOpenFullscreen: Function,
  className?: string
};

const MediaItem: React.FC<MediaItemProps> =
    ({ item, onFavorite, onDelete, onOpenFullscreen, className = "" }) => {
  const [isHovering, setIsHovering] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const isVideo = item.mediaType.includes('video');
  const isImage = item.mediaType.includes('image') || item.mediaType.includes('photo');

  const handleVideoToggle = (videoEl: HTMLVideoElement) => {
    if (isPlaying) {
      videoEl.pause();
    } else {
      videoEl.play();
    }
    setIsPlaying(!isPlaying);
  };

  const renderMedia = () => {
    if (isVideo) {
      return (
        <div className="relative group">
          <video
            className="w-full h-64 object-cover rounded-t-lg"
            src={`/media/${item.fileName}`}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
            onClick={(e) => handleVideoToggle(e.target)}
          />
          <button
            className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => {
              e.stopPropagation();
              const video = e.target.parentElement.querySelector('video');
              handleVideoToggle(video);
            }}
          >
            {isPlaying ? (
              <Pause className="w-12 h-12 text-white" />
            ) : (
              <Play className="w-12 h-12 text-white" />
            )}
          </button>
        </div>
      );
    } else if (isImage) {
      return (
        <img
          src={`/media/${item.fileName}`}
          alt={item.fileName}
          className="w-full h-64 object-cover rounded-t-lg"
          onClick={() => onOpenFullscreen(item)}
        />
      );
    }
    return null;
  };

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden transition-transform hover:scale-[1.02] ${
        item.favorite ? 'ring-2 ring-blue-500' : ''
      } ${className}`}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      {renderMedia()}

      <div className="p-4">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-lg font-medium dark:text-white truncate">
            {item.fileName}
          </h3>
          {item.favorite && (
            <Star className="w-5 h-5 text-yellow-500 fill-current" />
          )}
        </div>

        <div className="space-y-1 text-sm text-gray-500 dark:text-gray-400">
          <p>Channel: {item.channelTitle}</p>
          <p>Date: {new Date(item.createdAt).toLocaleDateString()}</p>
          {item.telegramText && (
            <p className="truncate">{item.telegramText}</p>
          )}
        </div>
      </div>

      <div className={`
        absolute top-2 right-2 flex gap-2
        ${isHovering ? 'opacity-100' : 'opacity-0'}
        transition-opacity duration-200
      `}>
        <button
          onClick={() => window.open(`/media/${item.fileName}`, '_blank')}
          className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
        >
          <Download className="w-4 h-4" />
        </button>
        <button
          onClick={() => onFavorite(item)}
          className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
        >
          <Star className={`w-4 h-4 ${item.favorite ? 'fill-yellow-500' : ''}`} />
        </button>
        {!item.favorite && (
          <button
            onClick={() => onDelete(item)}
            className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
          >
            <Trash className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default MediaItem;