import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Moon, Sun, Search, Captions, CaptionsOff } from 'lucide-react';
import {User, SavedPreferences, sortOptions, favoriteOptions} from '@/lib/types';


type NavigationProps = {
  user: User;
  preferences: SavedPreferences;
  onPreferenceChange: (key: string, value: any) => any;
  onLogout: React.MouseEventHandler<HTMLButtonElement>;
}

const Navigation: React.FC<NavigationProps> = ({
  user,
  preferences,
  onPreferenceChange,
  onLogout,
}) => {
  const [searchValue, setSearchValue] = useState(preferences.search.search || '');

  // Handle search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchValue !== preferences.search.search) {
        onPreferenceChange('search', searchValue);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchValue]);

  return (
    <nav className="bg-primary-600 p-4 dark:bg-dark-surface text-white sticky top-0 z-40">
      <div className="container mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Left side - Navigation and filters */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-4">
            <Link to="/" className="hover:text-gray-200">Home</Link>
            <Link to="/about" className="hover:text-gray-200">About</Link>
            <button
              onClick={() => {onPreferenceChange('hideInfo', !preferences.view.hideInfo)}}
              className="p-2 bg-primary-700 dark:bg-primary-800 rounded-full hover:bg-primary-800 dark:hover:bg-primary-700"
              aria-label="Show info"
            >
              {preferences.view.hideInfo ? <CaptionsOff className="w-5 h-5" /> : <Captions className="w-5 h-5" />}
            </button>
            <button
              onClick={() => {onPreferenceChange('darkmode', !preferences.view.darkmode)}}
              className="p-2 bg-primary-700 dark:bg-primary-800 rounded-full hover:bg-primary-800 dark:hover:bg-primary-700"
              aria-label="Toggle dark mode"
            >
              {preferences.view.darkmode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>

          <select
            value={preferences.search.sort}
            onChange={(e) => onPreferenceChange('sort', e.target.value)}
            className="bg-primary-700 dark:bg-primary-800 text-gray-200 rounded px-3 py-1.5 text-sm"
          >
            {Object.entries(sortOptions).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          <select
            value={preferences.search.favorites}
            onChange={(e) => onPreferenceChange('favorites', e.target.value)}
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
              checked={preferences.search.videos}
              onChange={(e) => onPreferenceChange('videos', e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            Videos only
          </label>

          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value as keyof typeof sortOptions)}
              placeholder="Search..."
              className="pl-9 pr-4 py-1.5 rounded bg-primary-700 dark:bg-primary-800 text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>

        {/* Right side - User actions */}
        <div className="flex items-center gap-4">
          {user ? (
            <>
              <span className="text-sm">Welcome, {user.email}</span>
              <button
                onClick={onLogout}
                className="px-4 py-1.5 bg-primary-700 dark:bg-primary-800 rounded text-sm hover:bg-primary-800"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/register"
                className="px-4 py-1.5 bg-primary-700 dark:bg-primary-800 rounded text-sm hover:bg-primary-800"
              >
                Register
              </Link>
              <Link
                to="/login"
                className="px-4 py-1.5 bg-primary-700 dark:bg-primary-800 rounded text-sm hover:bg-primary-800"
              >
                Login
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;