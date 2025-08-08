import React from 'react';
import { Button } from '@radix-ui/themes';
import { useGalleryMutations } from '@media/api';

interface UndoButtonProps {
  disabled?: boolean;
}

const UndoButton: React.FC<UndoButtonProps> = ({ disabled = false }) => {
  const { undoDelete } = useGalleryMutations();

  const handleUndo = () => {
    undoDelete.mutate();
  };

  return (
    <Button
      onClick={handleUndo}
      disabled={disabled || undoDelete.isPending}
      style={{
        position: 'absolute',
        bottom: '20px',
        right: '20px',
        zIndex: 10,
        borderRadius: '50%',
        width: '60px',
        height: '60px',
        backgroundColor: '#ff6b35',
        color: 'white',
        border: 'none',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        cursor: disabled || undoDelete.isPending ? 'not-allowed' : 'pointer',
        opacity: disabled || undoDelete.isPending ? 0.6 : 1,
        transition: 'all 0.2s ease',
      }}
      onMouseEnter={(e) => {
        if (!disabled && !undoDelete.isPending) {
          e.currentTarget.style.backgroundColor = '#e55a2e';
          e.currentTarget.style.transform = 'scale(1.05)';
        }
      }}
      onMouseLeave={(e) => {
        if (!disabled && !undoDelete.isPending) {
          e.currentTarget.style.backgroundColor = '#ff6b35';
          e.currentTarget.style.transform = 'scale(1)';
        }
      }}
    >
      {undoDelete.isPending ? '...' : '↶'}
    </Button>
  );
};

export default UndoButton;