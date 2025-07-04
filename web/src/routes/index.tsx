import { createFileRoute } from '@tanstack/react-router'
import PaginatedMediaGallery from '@gallery/components/MediaGallery'

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
  return <PaginatedMediaGallery />
}
