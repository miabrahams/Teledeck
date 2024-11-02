import React, { useEffect, useState } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Navigation from '@/components/Navigation';
import { PaginatedMediaGallery } from '@/components/Gallery';
import { Login, Register } from '@/components/Auth';
import { SavedPreferences } from '@/lib/types';
import { useUser, useLogout } from '@/lib/api';



const defaultPreferences: SavedPreferences = {
  search: {
    sort: 'date_desc',
    videos: true,
    favorites: 'all',
    search: 'date_desc',
  },
  view: {
    darkmode: true,
    showInfo: true,
  },
};

const App: React.FC = () => {
  const [prefs, setPrefs] = useState<SavedPreferences>(() => {
    const stored = localStorage.getItem('userPreferences');
    return stored ?
              JSON.parse(stored)
            : defaultPreferences
  });

  const handlePreferenceChange = (key: string, value: any) => {
    let { search: newSearch, view: newView } = prefs;
    if (key in prefs.search) {
        newSearch = { ...newSearch, [key]: value }
    }
    else if (key in prefs.view) {
        newView = { ...newView, [key]: value }
    }
    else {
      throw new Error(`Invalid preference key: ${key}`);
    }
    const newPrefs = { search: newSearch, view: newView };
    setPrefs(newPrefs);
    localStorage.setItem('userPreferences', JSON.stringify(newPrefs));
  };

  useEffect(() => {
    if (prefs.view.darkmode) {
      document.documentElement.classList.add('dark');
    }
    else {
      document.documentElement.classList.remove('dark');
    }

    if (prefs.view.showInfo) {
      document.documentElement.classList.remove('hide-info');
    }
    else {
      document.documentElement.classList.add('hide-info');
    }
  }, [prefs.view]);

  const { data: user } = useUser();
  const logout = useLogout();

  return (
    <Router>
      <div className="min-h-screen flex flex-col dark:bg-slate-800">
        <Navigation
          user={user}
          preferences={prefs}
          onPreferenceChange={handlePreferenceChange}
          onLogout={() => { logout.mutate }}
        />

        <main className="flex-1 container main-container">
          <Routes>
            <Route
              path="/"
              element={
                <PaginatedMediaGallery
                  preferences={prefs.search}
                />
              }
            />
            <Route
              path="/login"
              element={user ? <Navigate to="/" /> : <Login />}
            />
            <Route
              path="/register"
              element={user ? <Navigate to="/" /> : <Register />}
            />
          </Routes>
        </main>

        <footer className="bg-neutral-200 dark:bg-dark-surface text-neutral-600 dark:text-neutral-400 p-4 mt-8">
          <div className="container mx-auto text-center">© 2024 Teledeck</div>
        </footer>
      </div>
    </Router>
  );
};

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
// Wrap the app with QueryClientProvider
const AppWithProvider = () => (
  <QueryClientProvider client={queryClient}>
      <App />
{/*     <ReactQueryDevtools initialIsOpen={false} /> */}
  </QueryClientProvider>
);


export default AppWithProvider;
