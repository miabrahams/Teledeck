import React from 'react';
import { Link } from 'react-router-dom';
import { Moon, Sun, Captions, CaptionsOff } from 'lucide-react';
import { useAtom } from 'jotai';
import { viewPrefsAtom } from '@preferences/state';


const ViewOptions: React.FC = () => {
  const [viewPrefs, setViewPrefs] = useAtom(viewPrefsAtom);

  return (
    <div className="flex items-center gap-4">
      <Link to="/" className="hover:text-gray-200">
        Home
      </Link>
      <Link to="/about" className="hover:text-gray-200">
        About
      </Link>
      <button
        onClick={() => {
          setViewPrefs('hideinfo', !viewPrefs.hideinfo);
        }}
        className="p-2 bg-primary-700 dark:bg-primary-800 rounded-full hover:bg-primary-800 dark:hover:bg-primary-700"
        aria-label="Show info"
      >
        {viewPrefs.hideinfo ? (
          <CaptionsOff className="w-5 h-5" />
        ) : (
          <Captions className="w-5 h-5" />
        )}
      </button>
      <button
        onClick={() => {
          setViewPrefs('darkmode', !viewPrefs.darkmode);
        }}
        className="p-2 bg-primary-700 dark:bg-primary-800 rounded-full hover:bg-primary-800 dark:hover:bg-primary-700"
        aria-label="Toggle dark mode"
      >
        {viewPrefs.hideinfo ? (
          <Sun className="w-5 h-5" />
        ) : (
          <Moon className="w-5 h-5" />
        )}
      </button>
    </div>
  );
};

export default ViewOptions