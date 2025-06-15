import { createFileRoute } from '@tanstack/react-router'
import { PaginatedMediaGallery } from '@gallery/components/PaginatedGallery'

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
  return <PaginatedMediaGallery />
}
