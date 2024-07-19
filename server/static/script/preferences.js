const defaultPreferences = {
  sort: 'date_desc',
  videosOnly: false,
  favoritesOnly: false,
};

function getPreferences() {
  const storedPrefs = localStorage.getItem('userPreferences');
  const page = new URLSearchParams(window.location.search).get('page', 1);
  updatedPrefs = Object.assign(defaultPreferences, JSON.parse(storedPrefs) || {}, {page});
  console.log(updatedPrefs)
  return updatedPrefs;
}

function setPreference(key, value) {
  const prefs = getPreferences();
  prefs[key] = value;
  prefs['page'] = undefined;
  localStorage.setItem('userPreferences', JSON.stringify(prefs));
}

function applyPreferences() {
  const prefs = getPreferences();
  document.getElementById('sort-select').value = prefs.sort;
  document.getElementById('videos-check').checked = prefs.videosOnly;
  document.getElementById('favorites-check').checked = prefs.favoritesOnly;
}

function updateGallery() {
  const prefs = getPreferences();
  htmx.ajax('GET', '/', {
    target: '#media-index',
    swap: 'innerHTML',
    values: {
      sort: prefs.sort,
      videos: prefs.videosOnly,
      favorites: prefs.favoritesOnly,
      page: prefs.page
    },
  });
}

document.addEventListener('DOMContentLoaded', () => {
  applyPreferences();
  updateGallery();
});