import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Moon, Sun, Search } from 'lucide-react';
import {User, Preferences} from '@/lib/types';

const sortOptions = [
  { value: 'date_desc', label: 'Newest posts first' },
  { value: 'date_asc', label: 'Oldest posts first' },
  { value: 'id_desc', label: 'Recent additions first' },
  { value: 'id_asc', label: 'Oldest additions first' },
  { value: 'size_desc', label: 'Largest files first' },
  { value: 'size_asc', label: 'Smallest files first' },
  { value: 'random', label: 'Random' }
];

const favoriteOptions = [
  { value: 'all', label: 'View all posts' },
  { value: 'favorites', label: 'Favorites only' },
  { value: 'non-favorites', label: 'Non-favorites only' }
];

type NavigationProps = {
  user: User;
  preferences: Preferences;
  onPreferenceChange: (key: string, value: any) => any;
  onLogout: React.MouseEventHandler<HTMLButtonElement>;
}

const Navigation: React.FC<NavigationProps> = ({
  user,
  preferences,
  onPreferenceChange,
  onLogout,
}) => {
  const [searchValue, setSearchValue] = useState(preferences.search || '');
  const [isDark, setIsDark] = useState(() =>
    document.documentElement.classList.contains('dark')
  );

  // Handle search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchValue !== preferences.search) {
        onPreferenceChange('search', searchValue);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchValue]);

  const toggleDarkMode = () => {
    document.documentElement.classList.toggle('dark');
    setIsDark(!isDark);
  };

  return (
    <nav className="bg-primary-600 p-4 dark:bg-dark-surface text-white sticky top-0 z-40">
      <div className="container mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Left side - Navigation and filters */}
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-4">
            <Link to="/" className="hover:text-gray-200">Home</Link>
            <Link to="/about" className="hover:text-gray-200">About</Link>
            <button
              onClick={toggleDarkMode}
              className="p-2 bg-primary-700 dark:bg-primary-800 rounded-full hover:bg-primary-800 dark:hover:bg-primary-700"
              aria-label="Toggle dark mode"
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>

          <select
            value={preferences.sort}
            onChange={(e) => onPreferenceChange('sort', e.target.value)}
            className="bg-primary-700 dark:bg-primary-800 text-gray-200 rounded px-3 py-1.5 text-sm"
          >
            {sortOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <select
            value={preferences.favorites}
            onChange={(e) => onPreferenceChange('favorites', e.target.value)}
            className="bg-primary-700 dark:bg-primary-800 text-gray-200 rounded px-3 py-1.5 text-sm"
          >
            {favoriteOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={preferences.videos}
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
              onChange={(e) => setSearchValue(e.target.value)}
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