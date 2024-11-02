import React from 'react';
import { useAtom } from 'jotai';
import { searchPrefsAtom } from '@preferences/state';
import { favoriteOptions, sortOptions } from '../constants';

const SearchOptions: React.FC = () => {
  const [searchPrefs, setSearchPrefs] = useAtom(searchPrefsAtom);

  return (
    <>
      <select
        value={searchPrefs.sort}
        onChange={(e) => setSearchPrefs('sort', e.target.value)}
        className="bg-primary-700 dark:bg-primary-800 text-gray-200 rounded px-3 py-1.5 text-sm"
      >
        {Object.entries(sortOptions).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>

      <select
        value={searchPrefs.favorites}
        onChange={(e) => setSearchPrefs('favorites', e.target.value)}
        className="bg-primary-700 dark:bg-primary-800 text-gray-200 rounded px-3 py-1.5 text-sm"
      >
        {Object.entries(favoriteOptions).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={searchPrefs.videos}
          onChange={(e) => setSearchPrefs('videos', e.target.checked)}
          className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
        />
        Videos only
      </label>
    </>
  );
};

export default SearchOptions