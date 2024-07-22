

function clampInsideScope(mouseX, mouseY, scope, innerElement) {
  const { left: scopeOffsetX, top: scopeOffsetY, width: scopeWidth, height: scopeHeight } = scope.getBoundingClientRect();
  const innerWidth = innerElement.clientWidth;
  const innerHeight = innerElement.clientHeight;

  const clampedX = Math.min(Math.max(mouseX, scopeOffsetX), scopeOffsetX + scopeWidth - innerWidth);
  const clampedY = Math.min(Math.max(mouseY, scopeOffsetY), scopeOffsetY + scopeHeight - innerHeight);
  return { clampedX, clampedY };
}

function setupContextMenu() {
  const scope = document.querySelector('main');
  const contextMenu = document.getElementById('context-menu');
  const contextState = {
    mediaItem : null,
    mediaId : null,
    mediaFileName : null
  };

  function closeContextMenu() {
      contextState.mediaItem = null;
      contextState.mediaId = null;
      contextState.mediaFileName = null;
      contextMenu.classList.remove('visible');
  }

  scope.addEventListener('contextmenu', (contextEvent) => {
    const mediaItem = contextEvent.target.closest('.media-item');
    if (mediaItem === null) return
    contextEvent.preventDefault();

    contextMenu.classList.remove('visible');

    const { clientX, clientY } = contextEvent;
    const { clampedX, clampedY } = clampInsideScope(clientX, clientY, scope, contextMenu);

    contextMenu.style.left = `${clampedX}px`;
    contextMenu.style.top = `${clampedY}px`;

    setTimeout(() => {
        contextState.mediaItem = mediaItem
        contextState.mediaId = mediaItem.dataset.id;
        contextState.mediaFileName = mediaItem.dataset.fileName;
        contextMenu.classList.add('visible');
    }, 0);
  }, false);

  document.addEventListener('click', (clickEvent) => {
    if (clickEvent.target.offsetParent != contextMenu) {
      closeContextMenu()
    }
  });

  downloadItem = contextMenu.querySelector('.download-button');
  favoriteItem = contextMenu.querySelector('.favorite-button');
  deleteItem = contextMenu.querySelector('.delete-button');

  downloadItem.addEventListener('click', (e) => {
    if (contextState.mediaItem) {
      // Implement this some otherway like create an <a> element?
      contextState.mediaItem.querySelector('.download-link').click();
      console.error("Not implemented.");
    }
    closeContextMenu()
    e.preventDefault();
  });

  favoriteItem.addEventListener('click', (e) => {
    if (contextState.mediaItem) {
      contextState.mediaItem.querySelector('.favorite-button').click();
    }
    closeContextMenu()
    e.preventDefault();
  });

  deleteItem.addEventListener('click', (e) => {
    if (contextState.mediaItem) {
      contextState.mediaItem.querySelector('.delete-button').click();
    }
    closeContextMenu()
    e.preventDefault();
  });



}

function setupModalView() {
  window.fullscreenView = null;
  document.addEventListener('click', (clickEvent) => {
    if (window.fullscreenView !== null) {
      console.log('Closing modal');
      console.log(window.fullscreenView.restoreTarget);
      window.fullscreenView.restoreTarget.appendChild(
        window.fullscreenView.mediaItem
      );
      window.fullscreenView.remove();
      window.fullscreenView = null;
      clickEvent.preventDefault();
    }

    const mediaContainer = clickEvent.target.closest(
      '[data-fullscreen="true"]'
    );
    if (mediaContainer && !clickEvent.target.closest('.download-button')) {
      console.log('Clicked on media content');
      const fullscreenView = document.createElement('div');
      fullscreenView.className = 'fullscreen-view';
      fullscreenView.innerHTML = `<div class="fullscreen-content"></div>`;
      console.log(fullscreenView.innerHTML);

      document.body.appendChild(fullscreenView);
      const mediaItem = mediaContainer.children[0];
      fullscreenView.appendChild(mediaItem);
      fullscreenView.restoreTarget = mediaContainer;
      fullscreenView.mediaItem = mediaItem;
      window.fullscreenView = fullscreenView;
    }
  });
}

function setupAutoplay() {
  window.addEventListener('load', function () {
    for (video of document.querySelectorAll('video')) {
      video.muted = 1;
      video.addEventListener('mouseover', video.play);
      video.addEventListener('mouseout', video.pause);
      video.addEventListener('click', () => {
        video.muted = 0;
      });
    }
  });
}

(function () {
  setupContextMenu();
  setupModalView();
  setupAutoplay();
})();
