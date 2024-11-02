import { atomWithStorage } from 'jotai/utils';

export const currentPageAtom = atomWithStorage<number>('currentPage', 1)