import { useCallback } from 'react';
import { useAtom, useAtomValue } from 'jotai';
import { useTotalPages } from '../api';
import { currentPageAtom } from '../state';
import { searchPrefsAtom } from '@preferences/state';


export const usePageNavigation = () => {
  const searchPrefs = useAtomValue(searchPrefsAtom);
  const [currentPage, setCurrentPage] = useAtom(currentPageAtom);
  const { data: totalPages = 1 } = useTotalPages(searchPrefs);

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
