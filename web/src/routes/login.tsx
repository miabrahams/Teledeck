import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Login } from '@auth/components/Auth'
import { useUser } from '@auth/api'

export const Route = createFileRoute('/login')({
  component: LoginPage,
})

function LoginPage() {
  const { data: user } = useUser()
  const navigate = useNavigate()

  if (user) {
    // Redirect to home if already logged in
    navigate({ to: '/' })
    return null
  }

  return <Login />
}
