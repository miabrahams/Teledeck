import { useState, useEffect } from 'react';
import { useAtom } from 'jotai';
import { searchStringAtom } from '@preferences/state';

export const useSearch = (debounceMs = 300) => {
  const [searchString, setSearchString] = useAtom(searchStringAtom);
  const [searchValue, setSearchValue] = useState(searchString);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchValue !== searchString) {
        setSearchString(searchValue);
      }
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [searchValue, searchString, setSearchString, debounceMs]);

  return {
    searchValue,
    setSearchValue,
    searchString,
  };
};