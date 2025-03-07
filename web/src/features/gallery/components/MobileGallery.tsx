import React from 'react';
import { useAtom } from 'jotai';
import { Box, Flex, Text, IconButton } from '@radix-ui/themes';
import { ArrowLeft } from 'lucide-react';
import { useGalleryNavigation } from '@gallery/hooks/useGalleryNavigation';
import { searchPrefsAtom } from '@preferences/state';
import MobileMediaViewer from '../../media/components/MobileMediaViewer';
import { useLocation, useNavigate } from 'react-router-dom';

const MobileGallery: React.FC = () => {
  const [searchPrefs] = useAtom(searchPrefsAtom);
  const location = useLocation();
  const navigate = useNavigate();

  // Extract item ID from the URL if it exists
  const urlParams = new URLSearchParams(location.search);
  const initialItemId = urlParams.get('itemId') || undefined;

  // Track if we're in fullscreen view
  const isFullscreenView = !!initialItemId;

  // Use the gallery navigation hook with the initial item ID
  const {
    currentItemId,
    isLoading,
    error
  } = useGalleryNavigation(initialItemId, searchPrefs);

  // Update URL when the current item changes
  React.useEffect(() => {
    if (currentItemId) {
      navigate(`?itemId=${currentItemId}`, { replace: true });
    }
  }, [currentItemId, navigate]);

  const exitFullscreenView = () => {
    navigate('/', { replace: true });
  };

  if (isLoading) {
    return (
      <Box style={{ height: '100vh', width: '100%' }}>
        <Flex align="center" justify="center" height="100%">
          <Text color="gray">Loading gallery...</Text>
        </Flex>
      </Box>
    );
  }

  if (error) {
    return (
      <Box style={{ height: '100vh', width: '100%' }}>
        <Flex align="center" justify="center" height="100%">
          <Text color="red">Error loading gallery: {error.message}</Text>
        </Flex>
      </Box>
    );
  }

  return (
    <Box style={{ height: '100vh', width: '100%' }}>
      {isFullscreenView && (
        <Box style={{ position: 'absolute', top: 0, left: 0, zIndex: 60, padding: '1rem' }}>
          <IconButton variant="soft" onClick={exitFullscreenView}>
            <ArrowLeft />
          </IconButton>
        </Box>
      )}

      {currentItemId ? (
        <MobileMediaViewer itemId={currentItemId} />
      ) : (
        <Flex align="center" justify="center" height="100%">
          <Text color="gray">No media items found</Text>
        </Flex>
      )}
    </Box>
  );
};

export default MobileGallery;
