import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { MediaItem } from '../../../shared/types/media';
import { Dialog, Flex, IconButton } from '@radix-ui/themes';

type FullscreenViewProps = {
  item: MediaItem;
  onClose: () => void;
  closeFullScreen: () => void;
};

const FullscreenView: React.FC<FullscreenViewProps> = ({ item, onClose, closeFullScreen }) => {
  // Install keyboard listener; remove on cleanup
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const isVideo = item.MediaType === 'video';
  const closeOnMe = React.useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeFullScreen();
    }}, [closeFullScreen]);

  return (
    <Dialog.Root
      open={true}
      onOpenChange={() => onClose()}
    >
      <Dialog.Title style={{ display: 'none' }}>
        Fullscreen View
      </Dialog.Title>
      <Dialog.Content
        size="4"
        style={{
          maxWidth: '90vw',
          maxHeight: '90vh',
          width: 'auto',
          padding: 0,
          backgroundColor: 'transparent',
          border: 'none',
          boxShadow: 'none',
        }}
        onClick={closeOnMe}
      >
        <Flex
          direction="column"
          align="center"
          style={{ position: 'relative' }}
          onClick={closeOnMe}
        >
          <IconButton
            size="2"
            variant="soft"
            color="gray"
            onClick={onClose}
            style={{
              position: 'absolute',
              top: '1rem',
              right: '1rem',
              zIndex: 60,
            }}
          >
            <X width={24} height={24} />
          </IconButton>

          {isVideo ? (
            <video
              className="max-w-full max-h-[90vh] rounded-lg"
              controls
              autoPlay
              src={`/media/${item.file_name}`}
            />
          ) : (
            <img
              src={`/media/${item.file_name}`}
              alt={item.file_name}
              className="max-w-full max-h-[90vh] rounded-lg object-contain"
            />
          )}
        </Flex>
      </Dialog.Content>
    </Dialog.Root>
  );
};

export default FullscreenView;
