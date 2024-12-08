import { useCallback, useEffect } from 'react';
import { useAtom, useAtomValue } from 'jotai';
import { useTotalPages } from '../api';
import { currentPageAtom } from '../state';
import { searchPrefsAtom } from '@preferences/state';


export const usePageNavigation = () => {
  const searchPrefs = useAtomValue(searchPrefsAtom);
  const [currentPage, setCurrentPage] = useAtom(currentPageAtom);
  let { data: totalPages } = useTotalPages(searchPrefs);

  if (totalPages === undefined) {
    totalPages = 1;
  }

  const changePage = useCallback(
    (n: number) => {
      if (n >= 1 && n <= totalPages) {
        setCurrentPage(n);
      }
    },
    [totalPages, setCurrentPage]
  );

  const nextPage = useCallback(() => {
    changePage(currentPage + 1);
  }, [currentPage, changePage]);

  const previousPage = useCallback(() => {
    changePage(currentPage - 1);
  }, [currentPage, changePage]);

  return {
    currentPage,
    totalPages,
    changePage,
    nextPage,
    previousPage,
    hasNextPage: currentPage < totalPages,
    hasPreviousPage: currentPage > 1,
  };
};

export const useKeyboardNavigation = (nextPage: () => void, previousPage: () => void) => {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') nextPage();
      if (e.key === 'ArrowLeft') previousPage();
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [nextPage, previousPage]);
};