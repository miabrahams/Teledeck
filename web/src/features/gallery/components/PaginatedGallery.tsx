import React from 'react';
import { useAtom } from 'jotai';
import MediaGallery from './MediaGallery';
import FullscreenView from './FullScreenView';
import Pagination from './Pagination';
import { ContextMenu } from './ContextMenu';
import { useContextMenu } from '../hooks/useContextMenu'
import { usePageNavigation, useKeyboardNavigation } from '@gallery/hooks/usePageNavigation';
import { fullscreenItemAtom } from '@gallery/state';

export const PaginatedMediaGallery: React.FC = () => {
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





export default PaginatedMediaGallery;