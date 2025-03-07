import React from 'react';
import { useMobileDetection } from '@media/hooks/useMobileDetection';
import PaginatedMediaGallery from './PaginatedGallery';
import MobileGallery from './MobileGallery';

const GalleryWrapper: React.FC = () => {
  const isMobile = useMobileDetection();

  return (
    <>
      {isMobile ? <MobileGallery /> : <PaginatedMediaGallery />}
    </>
  );
};

export default GalleryWrapper;
