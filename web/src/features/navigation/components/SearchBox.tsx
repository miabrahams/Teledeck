import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { searchStringAtom } from '@preferences/state';
import { useAtom } from 'jotai';

const DebouncedSearchBox: React.FC = () => {
  const [searchString, setSearchString] = useAtom(searchStringAtom);
  const [searchValue, setSearchValue] = useState(searchString);

  // Handle search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchValue !== searchString) {
        setSearchString(searchValue);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchValue]);

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
      <input
        type="text"
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
        placeholder="Search..."
        className="pl-9 pr-4 py-1.5 rounded bg-primary-700 dark:bg-primary-800 text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
      />
    </div>
  );
};

export default DebouncedSearchBox