// src/features/media/components/MediaCard.tsx
import React from 'react';
import { useAtom, useSetAtom } from 'jotai';
import { Play, Download, Star, Trash } from 'lucide-react';
import { useVideoPlayer } from '@media/hooks/useVideoPlayer';
import { useIsMobile } from '@media/hooks/useIsMobile';
import { useMediaControls } from '@media/hooks/useMediaControls';
import { useMediaItem, useVideoThumbnail } from '@media/api';
import { contextMenuAtom, fullscreenItemAtom } from '@gallery/state';
import { MediaItem } from '@shared/types/media';
import { viewPrefsAtom } from '@preferences/state';
import {
  Box,
  Card,
  Flex,
  Text,
  IconButton,
  AspectRatio
} from '@radix-ui/themes';
import classes from './MediaCard.module.css';

type MediaViewProps = { item: MediaItem }

type VideoImageSwitchProps = MediaViewProps
const VideoImageSwitch: React.FC<VideoImageSwitchProps> = ({ item }) => {
  const setFullscreenItem = useSetAtom(fullscreenItemAtom);
  const isMobile = useIsMobile();
  const setFullscreen = React.useCallback(() => {
    if (isMobile) return;
    setFullscreenItem(item)
  }, [item, isMobile, setFullscreenItem])

  if (['video'].includes(item.MediaType)) {
    return <VideoItem item={item} setFullscreen={setFullscreen} />;
  }

  if (['image', 'photo', 'jpeg', 'png', 'gif'].includes(item.MediaType)) {
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
        className={classes.imageFit}
        onClick={setFullscreen}
      />
    </AspectRatio>
  );
}

const VideoItem: React.FC<MediaProps> = ({ item, setFullscreen }) => {
  // # TODO: Merge with top level isHovering
  const { videoRef, isPlaying, togglePlay, handlePlay, handlePause, onHover, onLeave } = useVideoPlayer();
  // const isMobile = useIsMobile();

  const { data, isSuccess } = useVideoThumbnail(item.id);

  return (
    <AspectRatio ratio={1}>
      <Box position="relative"
           style={{ width: '100%', height: '100%' }}
           onClick={setFullscreen}
           onMouseEnter = {onHover}
           onMouseLeave = {onLeave}
          >

        <video
          onClick={togglePlay}
          onPlay={handlePlay}
          onPause={handlePause}
          ref={videoRef}
          poster={isSuccess ? `/thumbnails/${data.fileName}` : undefined}
          className={classes.videoFit}
          src={`/media/${item.file_name}`}
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

type MediaIconsProps = {
  isHovering: boolean;
  isFavorite: boolean;
  handleFavorite: () => void;
  handleDelete: () => void;
  handleDownload: () => void;
};

const MediaIconBox: React.FC<MediaIconsProps> = ({
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
        transition: 'opacity 0.2s ease-in-out',
        width: '100%',
      }}
    >
      <Flex gap="2" width="100%" justify="between">
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
        <IconButton
          size="1"
          variant="soft"
          onClick={handleFavorite}
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}
        >
          <Star className={`w-4 h-4 ${isFavorite ? 'fill-yellow-500' : ''}`} />
        </IconButton>
        <IconButton
          size="1"
          variant="soft"
          onClick={handleDownload}
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.7)' }}
        >
          <Download className="w-4 h-4" />
        </IconButton>
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

  const [viewPrefs, _] = useAtom(viewPrefsAtom);

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
      className = {classes.mediaCard}
      style={ {transform: isHovering ? 'translateY(-2px)' : 'none'} }
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      onClick={(e) => {
        setContextMenuAtom({x: e.pageX, y: e.pageY, item: item})
      }}
    >
      <Box className="media-item-content">
        <VideoImageSwitch item={item} />
      </Box>
      {!viewPrefs.hideinfo &&
        <MediaInfo item={item} /> }
      <MediaIconBox
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