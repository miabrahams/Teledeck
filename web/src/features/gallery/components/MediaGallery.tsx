import React from 'react';
import { useAtom, useAtomValue } from 'jotai';
import {
  Box,
  Container,
  Flex,
  Grid,
  Text,
  AlertDialog,
  Button,
  Spinner
} from '@radix-ui/themes';
import { useGallery } from '../api';
import { searchPrefsAtom } from '@preferences/state';
import MediaCard from '../../media/components/MediaCard';
import FullscreenView from './FullScreenView';
import Pagination from './Pagination';
import { ContextMenu } from './ContextMenu';
import { useContextMenu } from '../hooks/useContextMenu'
import { usePageNavigation, useKeyboardNavigation } from '@gallery/hooks/usePageNavigation';
import { fullscreenItemAtom } from '@gallery/state';
import UndoButton from './UndoButton';


const PaginatedMediaGallery: React.FC = () => {
  const [ fullscreenItem, setFullscreenItem ] = useAtom(fullscreenItemAtom);
  const { contextMenuState, contextMenuRef } = useContextMenu()
  const { currentPage, nextPage, previousPage } = usePageNavigation()
  useKeyboardNavigation(nextPage, previousPage);

  const P = React.useMemo(() => <Pagination />, [ currentPage ])
  const closeFullScreen = React.useCallback(() => { setFullscreenItem(null); } , [ setFullscreenItem ]);

  return (
    <div id="media-index">
        { P }
        <MediaGallery currentPage={currentPage} />
        { P }
      {contextMenuState.item && (
        <ContextMenu
          state = {contextMenuState}
          menuRef = {contextMenuRef}
        />
      )}
      {fullscreenItem && (
        <FullscreenView
          item={fullscreenItem}
          closeFullScreen={closeFullScreen}
          onClose={closeFullScreen}
        />
      )}
    </div>
  );
};

type MediaGalleryProps = { currentPage: number };

const MediaGallery: React.FC<MediaGalleryProps> = ({ currentPage }) => {
  const searchPrefs = useAtomValue(searchPrefsAtom);
  const { data, isLoading, error } = useGallery(searchPrefs, currentPage);

  if (isLoading) return <LoadSpinner />;
  if (error) return <ErrorStatus message={error.message} />;
  if (!data || data.length === 0) return <EmptyMessage />;

  return (
    <Container maxWidth={"100%"} style={{ position: 'relative' }}>
      <Grid
        className="media-gallery"
        columns='repeat(auto-fill, minmax(440px, 1fr))'
        gap="4"
      >
        {data.map((mediaItem) => (
          <MediaCard itemId={mediaItem.id} key={mediaItem.id} />
        ))}
      </Grid>
      {data && data.length > 0 && <UndoButton />}
    </Container>
  );
};

const LoadSpinner: React.FC = () => {
  return (
    <Flex align="center" justify="center" height="9">
      <Spinner size="2" />
    </Flex>
  );
}

const EmptyMessage: React.FC = () => {
  return (
    <Box p="6" style={{ textAlign: 'center' }}>
      <Text size="3" color="gray">
        No media found
      </Text>
    </Box>
  );
}

const ErrorStatus: React.FC<{message: string}> = ({message}) => {
  return (
    <AlertDialog.Root defaultOpen>
      <AlertDialog.Content>
        <AlertDialog.Title>Error Loading Media</AlertDialog.Title>
        <AlertDialog.Description>
          {message}
        </AlertDialog.Description>
        <Flex gap="3" mt="4" justify="end">
          <AlertDialog.Action>
            <Button onClick={() => window.location.reload()}>
              Retry
            </Button>
          </AlertDialog.Action>
        </Flex>
      </AlertDialog.Content>
    </AlertDialog.Root>
  );
}

export default PaginatedMediaGallery;