// src/features/media/components/MediaCard.tsx
import React from 'react';
import { useSetAtom } from 'jotai';
import { Play, Download, Star, Trash } from 'lucide-react';
import { useVideoPlayer } from '@media/hooks/useVideoPlayer';
import { useMediaControls } from '@media/hooks/useMediaControls';
import { useMediaItem } from '@media/api';
import { contextMenuAtom, fullscreenItemAtom } from '@gallery/state';
import { MediaItem } from '@shared/types/media';
import {
  Box,
  Card,
  Flex,
  Text,
  IconButton,
  AspectRatio
} from '@radix-ui/themes';

type MediaViewProps = { item: MediaItem }

type VideoImageSwitchProps = MediaViewProps
const VideoImageSwitch: React.FC<VideoImageSwitchProps> = ({ item }) => {
  const setFullscreenItem = useSetAtom(fullscreenItemAtom);
  const setFullscreen = React.useCallback(() => {
    setFullscreenItem(item)
  }, [item, setFullscreenItem])

  if (['video'].includes(item.MediaType)) {
    return <VideoItem item={item} setFullscreen={setFullscreen} />;
  }

  if (['image', 'photo', 'jpeg', 'png'].includes(item.MediaType)) {
    return <ImageItem item={item} setFullscreen={setFullscreen} />;
  }

  return <Text>Unsupported Media type: {item.MediaType}</Text>;
};

type MediaProps = MediaViewProps & { setFullscreen: () => void }
const ImageItem: React.FC<MediaProps> = ({ item, setFullscreen }) => {
  return (
    <AspectRatio ratio={1}>
      <img
        src={`/media/${item.file_name}`}
        alt={item.file_name}
        onClick={setFullscreen}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          cursor: 'pointer'
        }}
      />
    </AspectRatio>
  );
}

const VideoItem: React.FC<MediaProps> = ({ item, setFullscreen }) => {
  const { videoRef, isPlaying, togglePlay, handlePlay, handlePause } = useVideoPlayer();

  return (
    <AspectRatio ratio={1}>
      <Box position="relative" style={{ width: '100%', height: '100%' }} onClick={setFullscreen}>
        <video
          onClick={togglePlay}
          onPlay={handlePlay}
          onPause={handlePause}
          ref={videoRef}
          src={`/media/${item.file_name}`}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            cursor: 'pointer'
          }}
        />
        <Flex
          position="absolute"
          width="100%"
          height="100%"
          align="center"
          justify="center"
          style={{
            background: isPlaying ? 'transparent' : 'rgba(0, 0, 0, 0.3)',
            transition: 'background-color 0.2s',
            top: 0,
            left: 0
          }}
        >
          {!isPlaying && (
            <Play className="w-12 h-12 text-white" />
          )}
        </Flex>
      </Box>
    </AspectRatio>
  );
};

const MediaInfo: React.FC<MediaViewProps> = ({ item }) => {
  return (
    <Box p="3">
      <Flex justify="between" align="start" mb="2">
        <Text size="2" weight="medium" style={{ wordBreak: 'break-word' }}>
          {item.file_name}
        </Text>
        {item.favorite && (
          <Star className="w-4 h-4 text-yellow-500 fill-current flex-shrink-0" />
        )}
      </Flex>

      <Text size="1" color="gray">
        Channel: {item.channelTitle}
      </Text>
      <Text size="1" color="gray">
        Date: {new Date(item.created_at).toLocaleDateString()}
      </Text>
      {item.TelegramText && (
        <Text size="1" color="gray" style={{
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {item.TelegramText}
        </Text>
      )}
    </Box>
  );
};

type MediaControlsProps = {
  isHovering: boolean;
  isFavorite: boolean;
  handleFavorite: () => void;
  handleDelete: () => void;
  handleDownload: () => void;
};

const MediaControls: React.FC<MediaControlsProps> = ({
  isHovering,
  isFavorite,
  handleDelete,
  handleDownload,
  handleFavorite
}) => {
  return (
    <Box
      position="absolute"
      top="0"
      right="0"
      p="2"
      style={{
        opacity: isHovering ? 1 : 0,
        transition: 'opacity 0.2s ease-in-out'
      }}
    >
      <Flex gap="2">
        <IconButton
          size="1"
          variant="soft"
          onClick={handleDownload}
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}
        >
          <Download className="w-4 h-4" />
        </IconButton>
        <IconButton
          size="1"
          variant="soft"
          onClick={handleFavorite}
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}
        >
          <Star className={`w-4 h-4 ${isFavorite ? 'fill-yellow-500' : ''}`} />
        </IconButton>
        {!isFavorite && (
          <IconButton
            size="1"
            variant="soft"
            onClick={handleDelete}
            style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}
          >
            <Trash className="w-4 h-4" />
          </IconButton>
        )}
      </Flex>
    </Box>
  );
};

type MediaCardProps = { itemId: string };

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
      <Card size="1" style={{ height: '100%' }}>
        <Flex align="center" justify="center" height="9">
          <Text>Loading...</Text>
        </Flex>
      </Card>
    );
  }

  if (status === 'error' || !item) {
    return (
      <Card size="1">
        <Flex direction="column" align="center" gap="2" p="4">
          <Text color="red" size="2">Error loading media: {error?.message}</Text>
          <IconButton size="1" variant="soft" onClick={() => window.location.reload()}>
            Retry
          </IconButton>
        </Flex>
      </Card>
    );
  }

  return (
    <Card
      size="1"
      style={{
        position: 'relative',
        height: '100%',
        transition: 'transform 0.2s ease-in-out',
        transform: isHovering ? 'translateY(-2px)' : 'none'
      }}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      onClick={(e) => {
        setContextMenuAtom({x: e.pageX, y: e.pageY, item: item})
      }}
    >
      <Box className="media-item-content">
        <VideoImageSwitch item={item} />
      </Box>
      <MediaInfo item={item} />
      <MediaControls
        isHovering={isHovering}
        isFavorite={item.favorite}
        handleFavorite={handleFavorite}
        handleDelete={handleDelete}
        handleDownload={() => handleDownload(item.file_name)}
      />
    </Card>
  );
};

export default MediaCard;