import React, { useState } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import Navigation from '@/components/Navigation';
import MediaGallery from '@/components/Gallery';
import { Login, Register } from '@/components/Auth';
import { Preferences, User, defaultPreferences } from '@/lib/types';
import { useUser, useLogout, useTotalPages } from '@/lib/api';

const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(1);

  // TODO: query totalPages from API
  // TODO: fetch preferences using useQuery
  const [preferences, setPreferences] = useState<Preferences>(() => {
    const stored = localStorage.getItem('userPreferences');
    const prefs = stored ? JSON.parse(stored) : defaultPreferences;
    // Set dark mode to match new setting
    if (prefs.darkmode) {
      document.documentElement.classList.add('dark');
    }
    else {
      document.documentElement.classList.remove('dark');
    }
    return prefs
  });


  const {data: totalPages} = useTotalPages(preferences);

  // Equivalent useQuery for preferences
  /*
  const { data: preferences, isLoading: preferencesLoading } = useQuery({
    queryKey: ['preferences'],
    queryFn: () => {
      const stored = localStorage.getItem('userPreferences');
      const prefs: Preferences = stored ? JSON.parse(stored) : defaultPreferences;
      return prefs;
    },
  });
  */


  const { data: user, isLoading: userLoading } = useUser();
  const logout = useLogout();


  const handlePreferenceChange = (key: string, value: any) => {
    const newPreferences = { ...preferences, [key]: value };
    setPreferences(newPreferences);
    localStorage.setItem('userPreferences', JSON.stringify(newPreferences));
  };


  return (
    <Router>
      <div className="min-h-screen flex flex-col dark:bg-slate-800">
        <Navigation
          user={user}
          preferences={preferences}
          onPreferenceChange={handlePreferenceChange}
          onLogout={() => { logout.mutate }}
        />

        <main className="flex-1 container main-container">
          <Routes>
            <Route
              path="/"
              element={
                <MediaGallery
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={setCurrentPage}
                  preferences={preferences}
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

// Wrap the app with QueryClientProvider
const AppWithProvider = () => (
  <QueryClientProvider client={queryClient}>
      <App />
    {/* <ReactQueryDevtools /> Add this in development */}
  </QueryClientProvider>
);


export default AppWithProvider;
