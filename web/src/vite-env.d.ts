/// <reference types="vite/client" />

import { router } from './router'

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
