const defaultPreferences = {
  sort: 'date_desc',
  videos: false,
  favorites: 'all',
  search: '',
};

function getPreferences() {
  const storedPrefs = JSON.parse(localStorage.getItem('userPreferences'));

  let page = new URLSearchParams(window.location.search).get('page');
  page = page ? parseInt(page) : 1;

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

function getPrefValues() {
  const prefs = getPreferences();
  return {
    sort: prefs.sort,
    videos: prefs.videos,
    favorites: prefs.favorites,
    page: prefs.page,
    search: prefs.search,
  };
}

function updateGallery() {
  htmx.ajax('GET', '/', {
    target: '#media-index',
    swap: 'innerHTML',
    values: getPrefValues(),
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const prefs = applyPreferences();
  console.log("Preferences loaded", prefs);
  updateGallery();

  // Add preference query parameters
  document.body.addEventListener('htmx:configRequest', function(evt) {
    console.log("Request get!");
    console.log(evt.detail.parameters);
    console.log(evt)
    evt.detail.useUrlParams = true;
    const prefs = getPrefValues();
    for (const pref in prefs) {
      evt.detail.parameters[pref] = prefs[pref];
    }
  });

  document.body.addEventListener('htmx:beforeRequest', function(evt) {
    console.log("Request sent!");
    console.log(evt.detail.xhr);
    console.log(evt.detail.requestConfig);
  });
});


