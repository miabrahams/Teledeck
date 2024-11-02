import { ChevronLeft, ChevronRight } from 'lucide-react';
import { usePageNavigation } from '@gallery/hooks/usePageNavigation';

const Pagination: React.FC = () => {

  const { currentPage, totalPages, nextPage, previousPage, hasNextPage, hasPreviousPage } = usePageNavigation()

  return (
    <div className="flex justify-center items-center gap-4 mt-8">
      {hasPreviousPage && (
        <button
          onClick={previousPage}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          <ChevronLeft className="w-4 h-4" />
          Previous
        </button>
      )}

      <span className="text-sm text-gray-600 dark:text-gray-400">
        Page {currentPage} of {totalPages}
      </span>

      {hasNextPage && (
        <button
          onClick={nextPage}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Next
          <ChevronRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

export default Pagination