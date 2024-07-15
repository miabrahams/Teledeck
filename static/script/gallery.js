
window.fullscreenView = null;

document.addEventListener('click', function(e) {
    if (window.fullscreenView !== null) {
        console.log("Closing modal");
        window.fullscreenView.remove();
        window.fullscreenView = null;
        return e.preventDefault();
    }

    const mediaContent = e.target.closest('[data-fullscreen="true"]');
    if (mediaContent && !e.target.closest('.download-button')) {
      console.log("Clicked on media content");
      const fullscreenView = document.createElement('div');
      fullscreenView.className = 'fullscreen-view';
      fullscreenView.innerHTML = `
          <div class="fullscreen-content">
              ${mediaContent.outerHTML}
          </div>
      `;
      console.log(fullscreenView.innerHTML);

      document.body.appendChild(fullscreenView);
      window.fullscreenView = fullscreenView;
    }
});


// Targeting video element


window.addEventListener("load", function() {
  for (video of document.querySelectorAll("video")) {
    console.log(video);
    /* Applying mouseover event on video clip
    and then we call play() function to play
    the video when the mouse is over the video */
    video.addEventListener("mouseover", video.play)

    /* Applying mouseout event on video clip
    and then we call pause() function to stop
    the video when the mouse is out the video */
    video.addEventListener("mouseout", video.pause)
  }
});