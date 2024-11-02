import React, { useRef, useEffect } from 'react'
import { Download, Star, Trash, Tag, BarChart2 } from 'lucide-react';
import { MediaItem } from '@/lib/types';

export type ContextMenuState = { x: number, y: number, item: MediaItem | null }

type ContextMenuProps = ContextMenuState & { onClose: Function,  onAction: Function }

export const ContextMenu: React.FC<ContextMenuProps> = ({ x, y, onClose, onAction, item }) => {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const actions = [
    { icon: <Download size={16} />, label: 'Download', action: 'download' },
    { icon: <Star size={16} />, label: 'Favorite', action: 'favorite' },
    { icon: <Trash size={16} />, label: 'Delete', action: 'delete' },
    { icon: <Tag size={16} />, label: 'Tags', action: 'tags' },
    { icon: <BarChart2 size={16} />, label: 'Score', action: 'score' },
  ];

  return (
    <div
      ref={menuRef}
      className="absolute bg-[#1b1a1a] border border-gray-700 rounded-lg shadow-lg p-1 z-50"
      style={{ top: y, left: x }}
    >
      {actions.map(({ icon, label, action }) => (
        <button
          key={action}
          onClick={() => onAction(action, item)}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-200 hover:bg-[#343434] rounded"
        >
          {icon}
          {label}
        </button>
      ))}
    </div>
  );
};
