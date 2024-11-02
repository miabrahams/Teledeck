import React, { useState, useRef } from 'react';
import { Play, Pause, Download, Star, Trash } from 'lucide-react';
import { MediaItem } from '@/lib/types';
import { useMediaItem } from '@/lib/api';

type MediaItemProps = {
  itemId: string;
  onFavorite: Function;
  onDelete: Function;
  setFullscreenItem: Function;
  handleContextMenu: Function;
  className?: string;
};

const VideoItem: React.FC<{ item: MediaItem }> = ({ item }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const vidRef = useRef<HTMLVideoElement>(null);

  const handleVideoToggle = () => {
    if (!vidRef.current) return;
    if (isPlaying) { vidRef.current.pause(); }
    else { vidRef.current.play(); }
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="media-item-content cursor-pointer">
      <video
        className="w-full h-64 object-cover rounded-t-lg"
        src={`/media/${item.file_name}`}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onClick={handleVideoToggle}
        ref={vidRef}
      />
      <button
        className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={(e) => {
          e.stopPropagation();
          handleVideoToggle();
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
};


const MediaInfo: React.FC<{ item: MediaItem }> = ({ item }) => {

      return (
      <div className="media-info">
        <div className="flex justify-between items-start mb-2">
          <h2 className="media-meta media-filename"> {item.file_name} </h2>
          {item.favorite && ( <Star className="w-5 h-5 text-yellow-500 fill-current" />)}
        </div>

        <div className="media-meta media-channel">
          <p>Channel: {item.channelTitle}</p>
        </div>
        <p className="media-meta media-date">Date: {new Date(item.created_at).toLocaleDateString()}</p>
        {item.TelegramText && <p className="media-meta media-text truncate">{item.TelegramText}</p>}
        </div>
    )};

const MediaControls: React.FC<{ item: MediaItem, isHovering: boolean, onFavorite: Function, onDelete: Function }> = ({ item, isHovering, onFavorite, onDelete }) => {

  const controlClass = `controls ${isHovering ? 'opacity-100' : 'opacity-0'} transition-opacity duration-200`
  return (
      <div className={controlClass} >
        <button
          onClick={() => window.open(`/media/${item.file_name}`, '_blank')}
          className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
        >
          <Download className="w-4 h-4" />
        </button>
        <button
          onClick={() => onFavorite(item)}
          className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
        >
          <Star
            className={`w-4 h-4 ${item.favorite ? 'fill-yellow-500' : ''}`}
          />
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
  )};

const MediaCard: React.FC<MediaItemProps> = ({
  itemId,
  handleContextMenu,
  onFavorite,
  onDelete,
  setFullscreenItem,
}) => {
  const [isHovering, setIsHovering] = useState(false);

  const { data: item, status, error } = useMediaItem(itemId);

  if (status === 'pending') {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }
  if (status === 'error') {
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


  const isVideo = ['video'].includes(item.MediaType);
  const isImage = ['image', 'photo'].includes(item.MediaType);
  const cardClass = 'media-item relative group' + (item.favorite ? ' favorite' : '')

  return (
    <div
      className={cardClass}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <div className={'media-item-content cursor-pointer'}>{
          isVideo?
            <VideoItem item={item} />
          : isImage?
            <img
              src={`/media/${item.file_name}`}
              alt={item.file_name}
              onClick={() => setFullscreenItem(item)}
            />
          : null
        }
      </div>
      <MediaInfo item={item} />
      <MediaControls item={item} isHovering={isHovering} onFavorite={onFavorite} onDelete={onDelete} />
    </div>
  );
};

export default MediaCard;
