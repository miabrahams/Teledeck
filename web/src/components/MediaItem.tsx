import React, { useState } from 'react';
import { Play, Pause, Download, Star, Trash } from 'lucide-react';
import { MediaItemType } from '@/lib/types';

type MediaItemProps = {
  item: MediaItemType;
  onFavorite: Function;
  onDelete: Function;
  onOpenFullscreen: Function;
  className?: string;
};

/*
templ GalleryItem(item *models.MediaItemWithMetadata) {

    <div
        class={ favoriteClass(&item.MediaItem) }
        id={ itemID(&item.MediaItem) }
        data-id={ item.ID }
        data-filename={ item.FileName }
    >
		<div class="media-item-content cursor-pointer" data-fullscreen="true">
			if models.IsImgElement(item.MediaType) {
				<img src={ "/media/" + item.FileName } alt={ item.FileName }/>
			} else if models.IsVideoElement(item.MediaType) {
				<video controls loop >
					<source src={ "/media/" + item.FileName } type="video/mp4"/>
					Your browser does not support the video tag.
				</video>
			}
		</div>
		<div class="media-info">
			<h2 class="media-meta media-filename">
				{ item.FileName } ({ item.MediaType })
				if item.Favorite {
					<span class="favorite-star">&#9733;</span>
				}
			</h2>
			<p class="media-meta media-channel">Channel: { item.ChannelTitle }</p>
			<p class="media-meta media-date">Date: { item.CreatedAt.Format("2006-01-02 15:04:05") }</p>
			<p class="media-meta media-text">{ item.TelegramText }</p>
		</div>
		<div class="controls">
			@downloadButton(item)
			@deleteButton(item)
			@favoriteButton(item)
			@scoreButton(item)
		</div>
	</div>
}
*/

const VideoItem: React.FC<{ item: MediaItemType }> = ({ item }) => {
  const [isPlaying, setIsPlaying] = useState(false);

  const handleVideoToggle = (videoEl: HTMLVideoElement) => {
    if (isPlaying) {
      videoEl.pause();
    } else {
      videoEl.play();
    }
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="media-item-content cursor-pointer">
      <video
        className="w-full h-64 object-cover rounded-t-lg"
        src={`/media/${item.file_name}`}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onClick={(e) => handleVideoToggle(e.target)}
      />
      <button
        className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={(e) => {
          e.stopPropagation();
          const video = e.target.parentElement.querySelector('video');
          handleVideoToggle(video);
        }}
      >
        {isPlaying ? (
          <Pause className="w-12 h-12 text-white" />
        ) : (
          <Play className="w-12 h-12 text-white" />
        )}
      </button>
    </div>
  );
};


const MediaInfo: React.FC<{ item: MediaItemType }> = ({ item }) => {

      return (
      <div className="media-info">
        <div className="flex justify-between items-start mb-2">
          <h2 className="media-meta media-filename"> {item.file_name} </h2>
          {item.favorite && ( <Star className="w-5 h-5 text-yellow-500 fill-current" />)}
        </div>

        <div className="media-meta media-channel">
          <p>Channel: {item.channelTitle}</p>
        </div>
        <p className="media-meta media-date">Date: {new Date(item.created_at).toLocaleDateString()}</p>
        {item.TelegramText && <p className="media-meta media-text truncate">{item.TelegramText}</p>}
        </div>
    )};

const MediaControls: React.FC<{ item: MediaItemType, isHovering: boolean, onFavorite: Function, onDelete: Function }> = ({ item, isHovering, onFavorite, onDelete }) => {
  // `absolute top-2 right-2 flex gap-2 ${isHovering ? 'opacity-100' : 'opacity-0'} transition-opacity duration-200`

  const controlClass = `controls ${isHovering ? 'opacity-100' : 'opacity-0'} transition-opacity duration-200`
  return (
      <div className={controlClass} >
        <button
          onClick={() => window.open(`/media/${item.file_name}`, '_blank')}
          className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
        >
          <Download className="w-4 h-4" />
        </button>
        <button
          onClick={() => onFavorite(item)}
          className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
        >
          <Star
            className={`w-4 h-4 ${item.favorite ? 'fill-yellow-500' : ''}`}
          />
        </button>
        {!item.favorite && (
          <button
            onClick={() => onDelete(item)}
            className="p-2 bg-gray-900 bg-opacity-75 rounded-full text-white hover:bg-opacity-90"
          >
            <Trash className="w-4 h-4" />
          </button>
        )}
      </div>
  )};

const MediaItem: React.FC<MediaItemProps> = ({
  item,
  onFavorite,
  onDelete,
  onOpenFullscreen,
}) => {
  const [isHovering, setIsHovering] = useState(false);

  const isVideo = item.MediaType.includes('video');
  const isImage = ['image', 'photo'].includes(item.MediaType)

  const renderMedia = () => {
    if (isVideo) {
      return <VideoItem item={item} />;
    } else if (isImage) {
      return (
        <img
          src={`/media/${item.file_name}`}
          alt={item.file_name}
          onClick={() => onOpenFullscreen(item)}
        />
      );
    }
    return null;
  };

  return (
    <div
      className={
        'media-item relative group' + (item.favorite ? ' favorite' : '')
      }
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
    >
      <div className={'media-item-content cursor-pointer'}>{renderMedia()}</div>
      <MediaInfo item={item} />
      <MediaControls item={item} isHovering={isHovering} onFavorite={onFavorite} onDelete={onDelete} />
    </div>
  );
};

export default MediaItem;
