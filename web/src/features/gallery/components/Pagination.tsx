
// src/features/gallery/components/Pagination.tsx
import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { usePageNavigation } from '@gallery/hooks/usePageNavigation';
import {
  Flex,
  Button,
  Text,
  Select
} from '@radix-ui/themes';

const PAGE_SIZE = 20; // Adjust based on your needs

const Pagination: React.FC = () => {
  const {
    currentPage,
    totalPages,
    nextPage,
    previousPage,
    hasNextPage,
    hasPreviousPage,
    changePage
  } = usePageNavigation();

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

  return (
    <Flex
      direction="column"
      align="center"
      gap="3"
      py="6"
    >
      {/* Main pagination controls */}
      <Flex align="center" gap="2">
        <Button
          variant="soft"
          disabled={!hasPreviousPage}
          onClick={previousPage}
        >
          <ChevronLeft width="16" height="16" />
          Previous
        </Button>

        <Flex align="center" gap="2" mx="4">
          {pageNumbers.map((pageNum, idx) =>
            pageNum === -1 ? (
              <Text key={`ellipsis-${idx}`} size="2" color="gray">...</Text>
            ) : (
              <Button
                key={pageNum}
                variant={currentPage === pageNum ? "solid" : "soft"}
                onClick={() => changePage(pageNum)}
                size="1"
              >
                {pageNum}
              </Button>
            )
          )}
        </Flex>

        <Button
          variant="soft"
          disabled={!hasNextPage}
          onClick={nextPage}
        >
          Next
          <ChevronRight width="16" height="16" />
        </Button>
      </Flex>

      {/* Page size selector and info */}
      <Flex align="center" gap="3">
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