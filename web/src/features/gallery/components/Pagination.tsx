
// src/features/gallery/components/Pagination.tsx
import React from 'react';
import { ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';
import { pageNavigationParams } from '@gallery/hooks/usePageNavigation';
import { useDeletePage, useGallery } from '@gallery/api';
import { useAtomValue } from 'jotai';
import { searchPrefsAtom } from '@preferences/state';
import {
  Flex,
  Button,
  Text,
  Select,
  AlertDialog,
  Box
} from '@radix-ui/themes';

const PAGE_SIZE = 20; // Adjust based on your needs

const Pagination: React.FC<pageNavigationParams> = ({ currentPage, totalPages, nextPage, previousPage, hasNextPage, hasPreviousPage, changePage }) => {

  const searchPrefs = useAtomValue(searchPrefsAtom);
  const { data: currentPageItems } = useGallery(searchPrefs, currentPage);
  const deletePageMutation = useDeletePage();
  const [showConfirmDialog, setShowConfirmDialog] = React.useState(false);

  const handleClearPage = () => {
    if (!currentPageItems || currentPageItems.length === 0) return;

    const itemIds = currentPageItems.map(item => item.id);
    deletePageMutation.mutate({
      itemIds,
      preferences: searchPrefs,
      page: currentPage
    }, {
      onSuccess: () => {
        setShowConfirmDialog(false);
      }
    });
  };

  const nonFavoriteCount = currentPageItems?.length || 0;
  const hasItems = nonFavoriteCount > 0;

  // Generate array of page numbers for quick navigation
  const pageNumbers = React.useMemo(() => {
    const numbers = [];
    const range = 2; // Show 2 pages before and after current page

    for (let i = 1; i <= totalPages; i++) {
      if (
        i === 1 || // Always show first page
        i === totalPages || // Always show last page
        (i >= currentPage - range && i <= currentPage + range) // Show pages around current
      ) {
        numbers.push(i);
      } else if (numbers[numbers.length - 1] !== -1) {
        numbers.push(-1); // Add ellipsis marker
      }
    }
    return numbers;
  }, [currentPage, totalPages]);

  if (currentPage > totalPages) {
    changePage(totalPages);
  }
  if (currentPage < 1) {
    changePage(1);
  }

  return (
    <Flex
      direction="column"
      align="center"
      gap="3"
      py="4"
      px="3"
      style={{
        borderTop: '1px solid var(--gray-a4)',
      }}
    >
      {/* Main pagination controls */}
      <Flex align="center" justify="center" gap="2" wrap="wrap" style={{ width: '100%' }}>
        <Button
          variant="soft"
          size="2"
          disabled={!hasPreviousPage}
          onClick={previousPage}
        >
          <ChevronLeft width="16" height="16" />
          Previous
        </Button>

        {/* Page numbers: horizontally scrollable to avoid overflow */}
        <Box
          mx="3"
          style={{
            maxWidth: 'min(100%, 720px)',
            overflowX: 'auto',
            scrollbarWidth: 'thin',
            WebkitOverflowScrolling: 'touch',
          }}
        >
          <Flex align="center" gap="2" px="1">
            {pageNumbers.map((pageNum, idx) =>
              pageNum === -1 ? (
                <Text key={`ellipsis-${idx}`} size="2" color="gray">…</Text>
              ) : (
                <Button
                  key={pageNum}
                  variant={currentPage === pageNum ? 'solid' : 'soft'}
                  onClick={() => changePage(pageNum)}
                  size="1"
                >
                  {pageNum}
                </Button>
              )
            )}
          </Flex>
        </Box>

        <Button
          variant="soft"
          size="2"
          disabled={!hasNextPage}
          onClick={nextPage}
        >
          Next
          <ChevronRight width="16" height="16" />
        </Button>

        {/* Clear Page Button */}
        <AlertDialog.Root open={showConfirmDialog} onOpenChange={setShowConfirmDialog}>
          <AlertDialog.Trigger>
            <Button
              variant="outline"
              color="red"
              disabled={!hasItems || deletePageMutation.isPending}
              size="2"
            >
              <Trash2 width="16" height="16" />
              Clear Page
            </Button>
          </AlertDialog.Trigger>

          <AlertDialog.Content>
            <AlertDialog.Title>Clear Current Page</AlertDialog.Title>
            <AlertDialog.Description>
              Are you sure you want to delete all {nonFavoriteCount} items on this page?
              Favorite items will be skipped. This action cannot be undone.
            </AlertDialog.Description>
            <Flex gap="3" mt="4" justify="end">
              <AlertDialog.Cancel>
                <Button variant="soft" color="gray">
                  Cancel
                </Button>
              </AlertDialog.Cancel>
              <AlertDialog.Action>
                <Button
                  variant="solid"
                  color="red"
                  onClick={handleClearPage}
                  disabled={deletePageMutation.isPending}
                >
                  {deletePageMutation.isPending ? 'Deleting...' : 'Delete All'}
                </Button>
              </AlertDialog.Action>
            </Flex>
          </AlertDialog.Content>
        </AlertDialog.Root>
      </Flex>

      {/* Page size selector and info */}
      <Flex align="center" gap="3" wrap="wrap" justify="center">
        <Text size="2" color="gray">
          Page {currentPage} of {totalPages}
        </Text>

        <Select.Root defaultValue={PAGE_SIZE.toString()}>
          <Select.Trigger />
          <Select.Content>
            <Select.Group>
              <Select.Label>Items per page</Select.Label>
              {[10, 20, 50, 100].map(size => (
                <Select.Item key={size} value={size.toString()}>
                  {size} items
                </Select.Item>
              ))}
            </Select.Group>
          </Select.Content>
        </Select.Root>
      </Flex>
    </Flex>
  );
};

export default Pagination;