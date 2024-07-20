
window.fullscreenView = null;

document.addEventListener('click', function(e) {
    if (window.fullscreenView !== null) {
        console.log("Closing modal");
        console.log(window.fullscreenView.restoreTarget)
        window.fullscreenView.restoreTarget.appendChild(window.fullscreenView.mediaItem);
        window.fullscreenView.remove();
        window.fullscreenView = null;
        return e.preventDefault();
    }

    const mediaContainer = e.target.closest('[data-fullscreen="true"]');
    if (mediaContainer && !e.target.closest('.download-button')) {
      console.log("Clicked on media content");
      const fullscreenView = document.createElement('div');
      fullscreenView.className = 'fullscreen-view';
      fullscreenView.innerHTML = `<div class="fullscreen-content"></div>`;
      console.log(fullscreenView.innerHTML);

      document.body.appendChild(fullscreenView);
      const mediaItem = mediaContainer.children[0];
      fullscreenView.appendChild(mediaItem);
      fullscreenView.restoreTarget = mediaContainer;
      fullscreenView.mediaItem = mediaItem
      window.fullscreenView = fullscreenView;
    }
});



// Autoplay on hover
window.addEventListener("load", function() {
  for (video of document.querySelectorAll("video")) {
    video.addEventListener("mouseover", video.play)
    video.addEventListener("mouseout", video.pause)
  }
});
