import React from 'react'
import { Download, Star, Trash, Tag, BarChart2 } from 'lucide-react';
import { useMediaControls } from '@media/hooks/useMediaControls';
import { ContextMenuState } from '@gallery/hooks/useContextMenu';


type ContextMenuProps = { state: ContextMenuState, menuRef: React.RefObject<HTMLDivElement>  }

export const ContextMenu: React.FC<ContextMenuProps> = ({ state, menuRef }) => {

  const {handleFavorite, handleDelete, handleDownload } = useMediaControls(state.item?.id || '');

  const actions = [
    { icon: <Download size={16} />, label: 'Download', action: () => {handleDownload(state.item?.file_name ?? "")} },
    { icon: <Star size={16} />, label: 'Favorite', action: handleFavorite },
    { icon: <Trash size={16} />, label: 'Delete', action: handleDelete },
    { icon: <Tag size={16} />, label: 'Tags', action: () => {console.log("NOT IMPLEMENTED: 'tags'")} },
    { icon: <BarChart2 size={16} />, label: 'Score', action: () => {console.log("NOT IMPLEMENTED: 'score'")} },
  ];

  return (
    <div
      ref={menuRef}
      className="absolute bg-[#1b1a1a] border border-gray-700 rounded-lg shadow-lg p-1 z-50"
      style={{ top: state.y, left: state.x }}
    >
      {actions.map(({ icon, label, action }) => (
        <button
          key={label}
          onClick={action}
          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-gray-200 hover:bg-[#343434] rounded"
        >
          {icon}
          {label}
        </button>
      ))}
    </div>
  );
};
