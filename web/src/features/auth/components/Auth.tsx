import React, { useState } from 'react';
import { useNavigate, Link } from '@tanstack/react-router';
// import { Alert, AlertDescription } from '@/components/ui/alert';

const Alert: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="p-4 mb-4 text-sm bg-red-100 rounded-lg dark:bg-red-200" role="alert">
      {children}
    </div>
  );
};

const AlertDescription: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <p className="text-sm text-red-700 dark:text-red-800">{children}</p>;
}

type AuthError = {
  message: string;
} | null;

// TODO: Refactor to use API layer. Currently login/logout are not implemented

export const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<AuthError>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          email,
          password,
        }),
      });

      if (!response.ok) {
        throw new Error('Invalid email or password');
      }

      navigate({ to: '/' });
    } catch (err) {
      setError({ message: err instanceof Error ? err.message : 'Login failed' });
    }
  };

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white dark:bg-slate-700 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-6 dark:text-gray-200">
        Sign in to your account
      </h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <Alert>
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        )}
        <div>
          <label htmlFor="email" className="block text-sm font-medium dark:text-gray-200">
            Your email
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="name@company.com"
            required
            autoComplete="email"
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium dark:text-gray-200">
            Password
          </label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="••••••••"
            required
            autoComplete="current-password"
          />
        </div>
        <button
          type="submit"
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Sign in
        </button>
        <p className="text-sm text-center dark:text-gray-300">
          Don't have an account yet?{' '}
          <Link to="/register" className="text-primary-600 hover:text-primary-500">
            Register
          </Link>
        </p>
      </form>
    </div>
  );
};

export const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<AuthError>(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          email,
          password,
        }),
      });

      if (!response.ok) {
        throw new Error('Registration failed');
      }

      setSuccess(true);
      setTimeout(() => navigate({ to: '/login' }), 2000);
    } catch (err) {
      setError({ message: err instanceof Error ? err.message : 'Registration failed' });
    }
  };

  if (success) {
    return (
      <div className="max-w-md mx-auto mt-8 p-6 bg-white dark:bg-slate-700 rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-4 dark:text-gray-200">Registration successful</h1>
        <p className="dark:text-gray-300">
          Redirecting to <Link to="/login" className="text-primary-600 hover:text-primary-500">login</Link>...
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-8 p-6 bg-white dark:bg-slate-700 rounded-lg shadow-md">
      <h1 className="text-2xl font-bold mb-6 dark:text-gray-200">
        Register an account
      </h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <Alert>
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        )}
        <div>
          <label htmlFor="email" className="block text-sm font-medium dark:text-gray-200">
            Your email
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="name@company.com"
            required
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-sm font-medium dark:text-gray-200">
            Password
          </label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            placeholder="••••••••"
            required
          />
        </div>
        <button
          type="submit"
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          Register
        </button>
        <p className="text-sm text-center dark:text-gray-300">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-600 hover:text-primary-500">
            Login
          </Link>
        </p>
      </form>
    </div>
  );
};