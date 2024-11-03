import React from 'react';
import MediaCard from '../../media/components/MediaCard';
import { useGallery } from '../api';
import { useAtomValue } from 'jotai';
import { searchPrefsAtom } from '@preferences/state';

const LoadSpinner: React.FC = () => {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  );
}

const EmptyMessage: React.FC = () => {
  return (
    <div className="text-center text-gray-600 p-4">
      <p>No media found</p>
    </div>
  );
}

const ErrorStatus: React.FC<{message: string}> = ({message}) => {
  return (
    <div className="text-center text-red-600 p-4">
      <p>Error loading media: {message}</p>
      <button className="mt-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">
        Retry
      </button>
    </div>
  );
}


type MediaGalleryProps = { currentPage: number; };

const MediaGallery: React.FC<MediaGalleryProps> = ({ currentPage }) => {
  const searchPrefs = useAtomValue(searchPrefsAtom);
  const { data, isLoading, error } = useGallery(searchPrefs, currentPage);
  if (isLoading) return <LoadSpinner />;
  if (error) return <ErrorStatus message={error.message} />;
  if (!data) return <EmptyMessage />;

  return (
    <div className="media-gallery" id="gallery">
      {data.map((mediaItem) => (
        <MediaCard
          key={mediaItem.id}
          itemId={mediaItem.id}
        />
      ))}
    </div>
  );
};

export default MediaGallery