import React, { useState, useEffect } from 'react';
import { useAtom } from 'jotai';
import { Box, Flex, Text, IconButton } from '@radix-ui/themes';
import { Download, Star, Trash, Info, ChevronLeft, ChevronRight } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';

import { useSwipeControls } from '../hooks/useSwipeControls';
import { useMediaControls } from '../hooks/useMediaControls';
import { useMediaItem } from '@media/api';
import { useGalleryNavigation } from '@gallery/hooks/useGalleryNavigation';
import { MediaItem } from '@shared/types/media';
import { searchPrefsAtom } from '@preferences/state';
import styles from './MobileViewerStyles.module.css';
import { useVideoPlayer } from '@media/hooks/useVideoPlayer';

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  zIndex: 50,
  backgroundColor: 'rgba(0, 0, 0, 0.85)',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
};

const infoOverlayStyle: React.CSSProperties = {
  position: 'absolute',
  bottom: 0,
  left: 0,
  right: 0,
  padding: '1rem',
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  color: 'white',
  zIndex: 51,
};

const controlsOverlayStyle: React.CSSProperties = {
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  padding: '1rem',
  zIndex: 52,
  display: 'flex',
  justifyContent: 'space-between',
};

const fullscreenMediaStyle: React.CSSProperties = {
  maxWidth: '100%',
  maxHeight: '100%',
  objectFit: 'contain',
};

interface MediaDisplayProps {
  item: MediaItem;
  showControls: boolean;
}

const MediaDisplay: React.FC<MediaDisplayProps> = ({ item, showControls }) => {
  const { videoRef, togglePlay } = useVideoPlayer();

  if (['video'].includes(item.MediaType)) {
    return (
      <video
        ref={videoRef}
        src={`/media/${item.file_name}`}
        style={fullscreenMediaStyle}
        controls={showControls}
        onClick={togglePlay}
        autoPlay
        playsInline
      />
    );
  }

  if (['image', 'photo', 'jpeg', 'png', 'gif'].includes(item.MediaType)) {
    return (
      <img
        src={`/media/${item.file_name}`}
        alt={item.file_name}
        style={fullscreenMediaStyle}
      />
    );
  }

  return <Text>Unsupported Media type: {item.MediaType}</Text>;
};

interface MobileMediaViewerProps {
  itemId: string;
}

const MobileMediaViewer: React.FC<MobileMediaViewerProps> = ({ itemId }) => {
  const [searchPrefs] = useAtom(searchPrefsAtom);
  const [showControls, setShowControls] = useState(false);
  const [showInfo, setShowInfo] = useState(false);
  const [showTutorial, setShowTutorial] = useState(true);

  // Fetch current item using the same hook as MediaCard
  const { data: currentItem, error, status } = useMediaItem(itemId);

  // Use gallery navigation to handle moving between items
  const {
    currentIndex,
    totalItems,
    goToNext,
    goToPrevious,
  } = useGalleryNavigation(itemId, searchPrefs);

  // Media controls for the current item
  const {
    handleFavorite,
    handleDelete,
    handleDownload
  } = useMediaControls(itemId);

  const toggleControls = () => {
    setShowControls(!showControls);
    if (!showControls) {
      setShowInfo(false);
    }
  };

  const toggleInfo = () => {
    setShowInfo(!showInfo);
  };

  const handleFavoriteSwipe = () => {
    if (currentItem) {
      handleFavorite();
      // Add haptic feedback if supported
      if (navigator.vibrate) {
        navigator.vibrate(100);
      }
    }
  };

  const handleDeleteSwipe = () => {
    if (currentItem) {
      handleDelete();
      // Add haptic feedback if supported
      if (navigator.vibrate) {
        navigator.vibrate([100, 50, 100]); // Stronger pattern for delete
      }
    }
  };

  const swipeControls = useSwipeControls({
    onSwipeLeft: handleDeleteSwipe,
    onSwipeRight: handleFavoriteSwipe,
    onSwipeUp: goToPrevious,
    onSwipeDown: goToNext,
    onTap: toggleControls,
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowTutorial(false);
    }, 5000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    setShowControls(false);
    setShowInfo(false);
  }, [itemId]);

  if (status === 'pending') {
    return (
      <Box style={overlayStyle}>
        <Flex align="center" justify="center" height="9">
          <Text color="gray">Loading...</Text>
        </Flex>
      </Box>
    );
  }

  if (status === 'error' || !currentItem) {
    return (
      <Box style={overlayStyle}>
        <Flex direction="column" align="center" gap="2" p="4">
          <Text color="red" size="2">Error loading media: {error?.message}</Text>
          <IconButton size="1" variant="soft" onClick={() => window.location.reload()}>
            Retry
          </IconButton>
        </Flex>
      </Box>
    );
  }

  return (
    <Box
      width="100%"
      height="100%"
      {...swipeControls}
      style={overlayStyle}
    >
      <AnimatePresence mode="wait">
        {showTutorial && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            style={{ width: '100%', height: '100%' }}
            className={styles.tutorial}
          >
            <Text weight="bold" color="gray">Swipe Controls</Text>
            <Text size="1" color="gray">← Swipe left to delete</Text>
            <Text size="1" color="gray">→ Swipe right to favorite</Text>
            <Text size="1" color="gray">↑ Swipe up for previous</Text>
            <Text size="1" color="gray">↓ Swipe down for next</Text>
            <Text size="1" color="gray">Tap screen to show controls</Text>
          </motion.div>
        )}
      </AnimatePresence>

      <MediaDisplay item={currentItem} showControls={showControls} />

      {/* Main Controls */}
      <AnimatePresence mode="wait">
        {showControls && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={controlsOverlayStyle}
          >
            <IconButton
              variant="ghost"
              size="3"
              onClick={goToPrevious}
              disabled={currentIndex === 0}
            >
              <ChevronLeft />
            </IconButton>

            <Flex gap="2">
              <IconButton
                size="2"
                variant="soft"
                onClick={() => handleDownload(currentItem.file_name)}
              >
                <Download />
              </IconButton>
              <IconButton size="2" variant="soft" onClick={handleDelete}>
                <Trash />
              </IconButton>
              <IconButton
                size="2"
                variant="soft"
                onClick={handleFavorite}
              >
                <Star className={currentItem.favorite ? "fill-yellow-500" : ""} />
              </IconButton>
              <IconButton size="2" variant="soft" onClick={toggleInfo}>
                <Info />
              </IconButton>
            </Flex>

            <IconButton
              variant="ghost"
              size="3"
              onClick={goToNext}
              disabled={currentIndex >= totalItems - 1}
            >
              <ChevronRight />
            </IconButton>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Info Overlay */}
      <AnimatePresence mode="wait">
        {showInfo && showControls && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={infoOverlayStyle}
          >
            <Text size="1" weight="bold" color="gray">
              {currentItem.file_name}
            </Text>
            <Text size="1" color="gray">
              {currentIndex + 1} / {totalItems}
            </Text>
            {currentItem.TelegramText && (
              <Text size="1" color="gray">
                {currentItem.TelegramText}
              </Text>
            )}
            <Text size="1" color="gray">
              Channel: {currentItem.channelTitle}
            </Text>
            <Text size="1" color="gray">
              Date: {new Date(currentItem.created_at).toLocaleDateString()}
            </Text>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
};

export default MobileMediaViewer;