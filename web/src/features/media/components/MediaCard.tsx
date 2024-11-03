import React from 'react';
import { useSetAtom } from 'jotai';
import { Play, Pause, Download, Star, Trash } from 'lucide-react';
import { useVideoPlayer } from '@media/hooks/useVideoPlayer';
import { useMediaControls } from '@media/hooks/useMediaControls';
import { useMediaItem } from '@media/api';
import { contextMenuAtom, fullscreenItemAtom } from '@gallery/state';
import { MediaItem } from '@shared/types/media';

type MediaViewProps = { item: MediaItem }

type VideoImageSwitchProps = MediaViewProps
const VideoImageSwitch: React.FC<VideoImageSwitchProps> = ({ item }) => {
  const setFullscreenItem = useSetAtom(fullscreenItemAtom);
  const setFullscreen = React.useCallback(() => {
    console.log("Setting fullscreen")
    setFullscreenItem(item)
  }, [item, setFullscreenItem])

  if (['video'].includes(item.MediaType)) {
    return <VideoItem item={item} setFullscreen={setFullscreen} />;
  }

  if (['image', 'photo'].includes(item.MediaType)) {
    return <ImageItem item={item} setFullscreen={setFullscreen} />;
  }

  return <div>Unsupported Media type: {}</div>;
};


type MediaProps = MediaViewProps & { setFullscreen: () => void}
const ImageItem: React.FC<MediaProps> = ({ item, setFullscreen }) => {
    return (
      <img
        src={`/media/${item.file_name}`}
        alt={item.file_name}
        onClick={setFullscreen}
      />
    );
  }


const VideoItem: React.FC<MediaProps> = ({ item, setFullscreen }) => {
  const { videoRef, isPlaying, togglePlay, handlePlay, handlePause } =
    useVideoPlayer();

  return (
    <div
      style={{ contentVisibility: 'auto', objectFit: 'contain', width: '100%' }}
      onClick = {setFullscreen}
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

const MediaInfo: React.FC<MediaViewProps> = ({ item }) => {
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

type HasChildren = { children: React.ReactNode; };
type HasClick = { onClick: () => void; };

const MediaActionButton: React.FC<HasChildren & HasClick> = ({ children, onClick }) => {
  const buttonClass = 'p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90';
  return (
    <button className={buttonClass} onClick={onClick} >
      {children}
    </button>
  );
}

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
      <MediaActionButton onClick={handleDownload} >
        <Download className="w-4 h-4" />
      </MediaActionButton>
      <MediaActionButton onClick={handleFavorite} >
        <Star className={`w-4 h-4 ${isFavorite ? 'fill-yellow-500' : ''}`} />
      </MediaActionButton>
      {!isFavorite && (
        <MediaActionButton onClick={handleDelete}>
          <Trash className="w-4 h-4" />
        </MediaActionButton>
      )}
    </div>
  );
};


type MediaCardProps = { itemId: string; };

const MediaCard: React.FC<MediaCardProps> = ({ itemId }) => {
  const { data: item, error, status } = useMediaItem(itemId);
  const {
    isHovering,
    setIsHovering,
    handleFavorite,
    handleDelete,
    handleDownload,
  } = useMediaControls(itemId);

  const setContextMenuAtom = useSetAtom(contextMenuAtom);

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
      onClick={(e) => {setContextMenuAtom({x: e.pageX, y: e.pageY, item: item})}}
    >
      <div className={'media-item-content flex-grow cursor-pointer'}>
        <VideoImageSwitch item={item} />
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
