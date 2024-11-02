import React, { useState } from 'react';
import MediaGallery from './MediaGallery';
import FullscreenView from './FullScreenView';
import Pagination from './Pagination';
import { useAtomValue } from 'jotai';
import { searchPrefsAtom } from '@preferences/state';
import { ContextMenu } from './ContextMenu';
import { useContextMenu } from '../hooks/useContextMenu'
import { usePageNavigation } from '../hooks/usePageNavigation'

export const PaginatedMediaGallery: React.FC = () => {
  const searchPrefs = useAtomValue(searchPrefsAtom);
  const [fullscreenItem, setFullscreenItem] = useState(null);
  const { currentPage } = usePageNavigation()
  const {contextMenuState, openContextMenu, contextMenuRef } = useContextMenu()

  return (

    <div id="media-index">
      <Pagination />
        <MediaGallery
          currentPage={currentPage}
          searchPrefs={searchPrefs}
          openContextMenu={openContextMenu}
          setFullscreenItem={setFullscreenItem}
        />
      <Pagination />

      {contextMenuState.item && (
        <ContextMenu
          state = {contextMenuState}
          menuRef = {contextMenuRef}
        />
      )}

      {fullscreenItem && (
        <FullscreenView
          item={fullscreenItem}
          onClose={() => {setFullscreenItem(null)}}
        />
      )}
    </div>

  );
};





export default PaginatedMediaGallery;