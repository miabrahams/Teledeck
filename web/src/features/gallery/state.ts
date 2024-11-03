import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';
import { MediaItem } from '@shared/types/media';

type OptionalMediaItem = MediaItem | null;

export type ContextMenuState = { x: number, y: number, item: OptionalMediaItem };

export const currentPageAtom = atomWithStorage<number>('currentPage', 1);

export const contextMenuAtom = atom<ContextMenuState>({ x: 0, y: 0, item: null });

export const fullscreenItemAtom = atom<OptionalMediaItem>(null);