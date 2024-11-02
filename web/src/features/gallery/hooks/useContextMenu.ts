import React, { useState, useCallback, useEffect } from 'react';
import { MediaItem } from '../types';

// src/features/gallery/hooks/useContextMenu.ts
type ContextMenuState = {
  x: number;
  y: number;
  item: MediaItem | null;
};

export const useContextMenu = () => {
  const [contextMenuState, setContextMenuState] = useState<ContextMenuState>({
    x: 0,
    y: 0,
    item: null,
  });

  const contextMenuRef = React.useRef<HTMLDivElement>(null);

  const openContextMenu = useCallback((e: React.MouseEvent, item: MediaItem) => {
    e.preventDefault();
    setContextMenuState({
      x: e.pageX,
      y: e.pageY,
      item,
    });
  }, []);

  const closeContextMenu = useCallback(() => {
    setContextMenuState((prev) => ({ ...prev, item: null }));
  }, []);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (contextMenuRef.current && !contextMenuRef.current.contains(event.target as Node)) {
        closeContextMenu();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [closeContextMenu]);



  return {
    contextMenuState,
    openContextMenu,
    closeContextMenu,
    contextMenuRef,
  };
};