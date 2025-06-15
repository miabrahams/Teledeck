import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { Register } from '@auth/components/Auth'
import { useUser } from '@auth/api'

export const Route = createFileRoute('/register')({
  component: RegisterPage,
})

function RegisterPage() {
  const { data: user } = useUser()
  const navigate = useNavigate()

  if (user) {
    // Redirect to home if already logged in
    navigate({ to: '/' })
    return null
  }

  return <Register />
}
