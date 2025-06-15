import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/about')({
  component: About,
})

function About() {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6 dark:text-gray-200">About Teledeck</h1>
      <div className="prose dark:prose-invert">
        <p className="text-lg mb-4 dark:text-gray-300">
          Teledeck is a modern media gallery application for managing and viewing your media collection.
        </p>
        <p className="mb-4 dark:text-gray-300">
          Built with React, TanStack Router, and other modern web technologies, Teledeck provides
          a fast and intuitive interface for browsing, organizing, and managing your media files.
        </p>
      </div>
    </div>
  )
}
