import React, { useEffect } from 'react';
import { X } from 'lucide-react';

type FullscreenViewProps = {
  item: any,
  onClose: () => {}
}

const FullscreenView: React.FC<FullscreenViewProps> = ({ item, onClose }) => {

  // Install keyboard listener; remove on cleanup
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { onClose(); }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  const isVideo = item.mediaType.includes('video');

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center"
      onClick={() => {onClose()}}
    >
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-white p-2 hover:bg-white/10 rounded-full transition-colors"
      >
        <X className="w-6 h-6" />
      </button>

      <div
        className="max-w-[90vw] max-h-[90vh]"
        onClick={e => e.stopPropagation()}
      >
        {isVideo ? (
          <video
            className="max-w-full max-h-[90vh] rounded-lg"
            controls
            autoPlay
            src={`/media/${item.fileName}`}
          />
        ) : (
          <img
            src={`/media/${item.fileName}`}
            alt={item.fileName}
            className="max-w-full max-h-[90vh] rounded-lg object-contain"
          />
        )}
      </div>
    </div>
  );
};

export default FullscreenView;