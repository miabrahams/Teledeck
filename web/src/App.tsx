import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navigation from '@/components/Navigation';
import MediaGallery from '@/components/Gallery';
import { Login, Register } from '@/components/Auth';
import { Preferences, User } from '@/types/types';


const App = () => {
  const [user, setUser] = useState<User>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [preferences, setPreferences] = useState<Preferences>(() => {
    const stored = localStorage.getItem('userPreferences');
    return stored ? JSON.parse(stored) : {
      sort: 'date_desc',
      videos: false,
      favorites: 'all',
      search: '',
    };
  });

  const [isDark, setIsDark] = useState(true);

  const toggleDarkMode = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle('dark');
  };


  useEffect(() => {
    // Check user session on mount
    checkSession();
  }, []);

  const checkSession = async () => {
    try {
      const response = await fetch('/api/me');
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Session check failed:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/logout', { method: 'POST' });
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handlePreferenceChange = (key: string, value: any) => {
    const newPreferences = { ...preferences, [key]: value };
    setPreferences(newPreferences);
    localStorage.setItem('userPreferences', JSON.stringify(newPreferences));
    setCurrentPage(1); // Reset to first page when preferences change
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <Router>
      <div className="min-h-screen flex flex-col dark:bg-slate-800">
        <Navigation
          user={user}
          preferences={preferences}
          onPreferenceChange={handlePreferenceChange}
          onLogout={handleLogout}
        />

        <main className="flex-1 container main-container">
          <Routes>
            <Route
              path="/"
              element={
                <MediaGallery
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
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
          <div className="container mx-auto text-center">
            © 2024 Teledeck
          </div>
        </footer>
      </div>
    </Router>
  );
};

export default App;