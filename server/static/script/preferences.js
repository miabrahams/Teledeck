const defaultPreferences = {
  sort: 'date_desc',
  videos: false,
  favorites: 'all',
  search: '',
};

function getPreferences() {
  const storedPrefs = JSON.parse(localStorage.getItem('userPreferences'));

  const page = new URLSearchParams(window.location.search).get('page', 1);
  const updatedPrefs = Object.assign({}, defaultPreferences, {page})
  for (const key in storedPrefs) {
    updatedPrefs[key] = storedPrefs[key];
  }
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
  document.getElementById('favorites-select').value = prefs.favorites;
  document.getElementById('videos-check').checked = prefs.videos;
  document.getElementById('search-field').value = prefs.search;
  return prefs;
}

function updateGallery() {
  const prefs = getPreferences();
  htmx.ajax('GET', '/', {
    target: '#media-index',
    swap: 'innerHTML',
    values: {
      sort: prefs.sort,
      videos: prefs.videos,
      favorites: prefs.favorites,
      page: prefs.page,
      search: prefs.search
    },
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const prefs = applyPreferences();
  console.log("Preferences loaded", prefs);
  updateGallery();
});