

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

  scope.addEventListener('contextmenu', (contextEvent) => {
    contextEvent.preventDefault();
    const { clientX, clientY } = contextEvent;
    const { clampedX, clampedY } = clampInsideScope(clientX, clientY, scope, contextMenu);

    contextMenu.style.left = `${clampedX}px`;
    contextMenu.style.top = `${clampedY}px`;

    contextMenu.classList.remove('visible');
    setTimeout(() => { contextMenu.classList.add('visible'); });

    // const mediaItem = contextEvent.target.closest('media-item');
  });

  document.addEventListener('click', (clickEvent) => {
    if (clickEvent.target.offsetParent != contextMenu) {
      contextMenu.classList.remove('visible');
    }
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
      return clickEvent.preventDefault();
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
