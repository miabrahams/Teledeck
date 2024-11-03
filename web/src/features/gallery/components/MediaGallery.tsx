// src/features/gallery/components/MediaGallery.tsx
import React from 'react';
import MediaCard from '../../media/components/MediaCard';
import { useGallery } from '../api';
import { useAtomValue } from 'jotai';
import { searchPrefsAtom } from '@preferences/state';
import {
  Box,
  Container,
  Flex,
  Text,
  AlertDialog,
  Button,
  Spinner
} from '@radix-ui/themes';

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

type MediaGalleryProps = { currentPage: number };

const MediaGallery: React.FC<MediaGalleryProps> = ({ currentPage }) => {
  const searchPrefs = useAtomValue(searchPrefsAtom);
  const { data, isLoading, error } = useGallery(searchPrefs, currentPage);

  if (isLoading) return <LoadSpinner />;
  if (error) return <ErrorStatus message={error.message} />;
  if (!data || data.length === 0) return <EmptyMessage />;

  return (
    <Container maxWidth={"100%"}>
      <Box
        className="media-gallery"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: 'var(--space-4)',
          padding: 'var(--space-4)'
        }}
      >
        {data.map((mediaItem) => (
          <MediaCard itemId={mediaItem.id} key={mediaItem.id} />
        ))}
      </Box>
    </Container>
  );
};

export default MediaGallery;