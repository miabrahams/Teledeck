import React from 'react';
import { Link } from 'react-router-dom';
import { User } from '@auth/types';

import ViewOptions from './ViewOptions';
import SearchOptions from './SearchOptions';
import SearchBox from './SearchBox';

type NavigationProps = { user: User; onLogout: React.MouseEventHandler<HTMLButtonElement> };

const Navigation: React.FC<NavigationProps> = ({ user, onLogout }) => {
  return (
    <nav className="bg-primary-600 p-4 dark:bg-dark-surface text-white sticky top-0 z-40">
      <div className="container mx-auto flex flex-wrap items-center justify-between gap-4">
        {/* Left side - Navigation and filters */}
        <div className="flex flex-wrap items-center gap-4">
          <ViewOptions />
          <SearchOptions />
          <SearchBox />
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
