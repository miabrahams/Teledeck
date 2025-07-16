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

// Helper function for actual file download
const downloadFile = (fileName: string) => {
  const link = document.createElement('a');
  link.href = `/media/${fileName}`;
  link.download = fileName;
  link.className = classes.downloadLink;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

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
  const { videoRef, isPlaying, togglePlay, handlePlay, handlePause, onHover, onLeave } = useVideoPlayer();
  const { data, isSuccess } = useVideoThumbnail(item.id);

  const handleVideoClick = React.useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    togglePlay();
  }, [togglePlay]);

  return (
    <AspectRatio ratio={1}>
      <Box
        position="relative"
        className={classes.videoContainer}
        onClick={setFullscreen}
        onMouseEnter={onHover}
        onMouseLeave={onLeave}
      >
        <video
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
          className={isPlaying ? classes.videoOverlayTransparent : classes.videoOverlay}
        >
          {!isPlaying && (
            <Play className="w-12 h-12 text-white" />
          )}
        </Flex>
        {/* Transparent overlay for play/pause in center */}
        <Box
          position="absolute"
          top="50%"
          left="50%"
          width="80px"
          height="80px"
          style={{
            transform: 'translate(-50%, -50%)',
            borderRadius: '50%',
          }}
          onClick={handleVideoClick}
        />
      </Box>
    </AspectRatio>
  );
};

const MediaInfo: React.FC<MediaViewProps> = ({ item }) => {
  return (
    <Box p="3">
      <Flex justify="between" align="start" mb="2">
        <Text size="2" weight="medium" className={classes.fileNameText}>
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
        <Text size="1" color="gray" className={classes.telegramText}>
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
  const handleIconClick = React.useCallback((e: React.MouseEvent, action: () => void) => {
    e.stopPropagation();
    action();
  }, []);

  return (
    <Box
      position="absolute"
      top="0"
      right="0"
      p="2"
      className={isHovering ? classes.iconBoxVisible : classes.iconBox}
    >
      <Flex gap="2" width="100%" justify="between">
        {!isFavorite && (
          <IconButton
            size="1"
            variant="soft"
            onClick={(e) => handleIconClick(e, handleDelete)}
            className={classes.iconButton}
          >
            <Trash className="w-4 h-4" />
          </IconButton>
        )}
        <IconButton
          size="1"
          variant="soft"
          onClick={(e) => handleIconClick(e, handleFavorite)}
          className={classes.iconButton}
        >
          <Star className={`w-4 h-4 ${isFavorite ? 'fill-yellow-500' : ''}`} />
        </IconButton>
        <IconButton
          size="1"
          variant="soft"
          onClick={(e) => handleIconClick(e, handleDownload)}
          className={classes.iconButton}
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
  } = useMediaControls(itemId);

  const setContextMenuAtom = useSetAtom(contextMenuAtom);
  const [viewPrefs] = useAtom(viewPrefsAtom);

  const handleDownload = React.useCallback(() => {
    if (item) {
      downloadFile(item.file_name);
    }
  }, [item]);

  const handleContextMenu = React.useCallback((e: React.MouseEvent) => {
    if (item) {
      setContextMenuAtom({ x: e.pageX, y: e.pageY, item });
    }
  }, [item, setContextMenuAtom]);

  if (status === 'pending') {
    return (
      <Card size="1" className={classes.loadingCard}>
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
      className={isHovering ? classes.mediaCardHovered : classes.mediaCard}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      onClick={handleContextMenu}
    >
      <Box className="media-item-content">
        <VideoImageSwitch item={item} />
      </Box>
      {!viewPrefs.hideinfo && <MediaInfo item={item} />}
      <MediaIconBox
        isHovering={isHovering}
        isFavorite={item.favorite}
        handleFavorite={handleFavorite}
        handleDelete={handleDelete}
        handleDownload={handleDownload}
      />
    </Card>
  );
};

export default MediaCard;