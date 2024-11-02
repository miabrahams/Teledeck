import React from 'react';
import { Play, Pause, Download, Star, Trash } from 'lucide-react';
import { MediaItem } from '@shared/types/media';
import { useVideoPlayer } from '@/features/media/hooks/useVideoPlayer';
import { useMediaControls } from '@media/hooks/useMediaControls';
import { useMediaItem } from '@media/api';


type VideoImageSwitchProps = { item: MediaItem; setFullscreenItem: Function; };
const VideoImageSwitch: React.FC<VideoImageSwitchProps> = ({ item, setFullscreenItem }) => {

  if (['video'].includes(item.MediaType)) {
    return <VideoItem item={item} />;
  }

  if (['image', 'photo'].includes(item.MediaType)) {
    return (
      <img
        src={`/media/${item.file_name}`}
        alt={item.file_name}
        onClick={() => setFullscreenItem(item)}
      />
    );
  }

  return <div>Unsupported Media type: {}</div>;
};


const VideoItem: React.FC<{ item: MediaItem }> = ({ item }) => {
  const { videoRef, isPlaying, togglePlay, handlePlay, handlePause } =
    useVideoPlayer();

  return (
    <div
      style={{ contentVisibility: 'auto', objectFit: 'contain', width: '100%' }}
    >
      <video
        className="w-full object-cover rounded-t-lg"
        src={`/media/${item.file_name}`}
        onPlay={handlePlay}
        onPause={handlePause}
        onClick={togglePlay}
        ref={videoRef}
      />
      <button
        className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={togglePlay}
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
        {item.favorite && (
          <Star className="w-5 h-5 text-yellow-500 fill-current" />
        )}
      </div>

      <div className="media-meta media-channel">
        <p>Channel: {item.channelTitle}</p>
      </div>
      <p className="media-meta media-date">
        Date: {new Date(item.created_at).toLocaleDateString()}
      </p>
      {item.TelegramText && (
        <p className="media-meta media-text truncate">{item.TelegramText}</p>
      )}
    </div>
  );
};

const MediaControls: React.FC<{
  isHovering: boolean;
  isFavorite: boolean;
  handleFavorite: () => void;
  handleDelete: () => void;
  handleDownload: () => void;
}> = ({ isHovering, isFavorite, handleDelete, handleDownload, handleFavorite }) => {
  const controlClass = `controls opacity-${ isHovering ? '100' : '0' } transition-opacity duration-200`;
  return (
    <div className={controlClass}>
      <button
        onClick={handleDownload}
        className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
      >
        <Download className="w-4 h-4" />
      </button>
      <button
        onClick={handleFavorite}
        className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
      >
        <Star className={`w-4 h-4 ${isFavorite ? 'fill-yellow-500' : ''}`} />
      </button>
      {!isFavorite && (
        <button
          onClick={handleDelete}
          className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
        >
          <Trash className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};


type MediaCardProps = {
  itemId: string;
  setFullscreenItem: Function;
  openContextMenu: (e: React.MouseEvent, item: MediaItem) => void;
  className?: string;
};

const MediaCard: React.FC<MediaCardProps> = ({
  itemId,
  openContextMenu,
  setFullscreenItem,
}) => {
  const { data: item, error, status } = useMediaItem(itemId);
  const {
    isHovering,
    setIsHovering,
    handleFavorite,
    handleDelete,
    handleDownload,
  } = useMediaControls(itemId);

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
        <button className="mt-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div
      className={
        'media-item flex flex-col justify-center relative group' +
        (item.favorite ? ' favorite' : '')
      }
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      onClick={(e) => {openContextMenu(e, item)}}
    >
      <div className={'media-item-content flex-grow cursor-pointer'}>
        <VideoImageSwitch item={item} setFullscreenItem={setFullscreenItem} />
      </div>
      <MediaInfo item={item} />
      <MediaControls
        isHovering={isHovering}
        isFavorite={item.favorite}
        handleFavorite={handleFavorite}
        handleDelete={handleDelete}
        handleDownload={() => {handleDownload(item.file_name)}}
      />
    </div>
  );
};

export default MediaCard;
