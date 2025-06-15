import { createRootRoute, Outlet, useNavigate } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import Navigation from '@navigation/components/Navigation'
import { useUser, useLogout } from '@auth/api'

export const Route = createRootRoute({
  component: () => {
    const { data: user } = useUser()
    const logout = useLogout()
    const navigate = useNavigate()

    const handleLogout = () => {
      logout.mutate(undefined, {
        onSuccess: () => {
          navigate({ to: '/login' })
        }
      })
    }

    return (
      <div className="min-h-screen flex flex-col dark:bg-slate-800">
        <Navigation
          user={user}
          onLogout={handleLogout}
        />

        <main>
          <Outlet />
        </main>

        <footer className="bg-neutral-200 dark:bg-dark-surface text-neutral-600 dark:text-neutral-400 p-4 mt-8">
          <div className="container mx-auto text-center">© 2025 Teledeck</div>
        </footer>

        {import.meta.env.DEV && <TanStackRouterDevtools />}
      </div>
    )
  },
})
