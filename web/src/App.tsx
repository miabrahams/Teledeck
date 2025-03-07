import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import Navigation from '@navigation/components/Navigation';
import { Login, Register } from '@auth/components/Auth';
import { useUser, useLogout } from '@auth/api';
import GalleryWrapper from '@gallery/components/GalleryWrapper';

const App: React.FC = () => {
  const { data: user } = useUser();
  const logout = useLogout();

  return (
    <Router>
      <div className="min-h-screen flex flex-col dark:bg-slate-800">
        <Navigation
          user={user}
          onLogout={() => { logout.mutate }}
        />

        <main>
          <Routes>
            <Route
              path="/"
              element={
                <GalleryWrapper />
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

export default App;
