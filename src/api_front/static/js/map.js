(() => {
  const container = document.getElementById('event-map');
  if (!container) return;
  const form = document.getElementById('map-period-form');
  const startInput = document.getElementById('map-start');
  const endInput = document.getElementById('map-end');
  const apply = document.getElementById('map-apply');
  const status = document.getElementById('map-status');
  const error = document.getElementById('map-error');
  const count = document.getElementById('map-count');
  const period = document.getElementById('map-period');
  const filters = document.getElementById('map-filters');
  const localFilters = document.getElementById('map-local-filters');
  const earthquakes = document.getElementById('map-earthquakes');
  const minimum = document.getElementById('map-mag-min');
  const maximum = document.getElementById('map-mag-max');

  const showError = (message) => {
    error.textContent = message;
    error.hidden = !message;
  };
  if (!window.L || !window.Supercluster || !window.OverlappingMarkerSpiderfier) {
    showError('Bibliothèques cartographiques indisponibles. Rechargez la page.');
    apply.disabled = true;
    return;
  }

  const map = L.map(container, { minZoom: 2, maxZoom: 19, worldCopyJump: true }).setView([22, 0], 2);
  const tiles = L.tileLayer(container.dataset.tileUrl, {
    maxZoom: 19,
    attribution: container.dataset.tileAttribution,
  }).addTo(map);
  tiles.on('tileerror', () => showError('Certaines tuiles OpenStreetMap ne sont pas disponibles.'));
  const markers = L.layerGroup().addTo(map);
  const spiderfier = new OverlappingMarkerSpiderfier(map, { keepSpiderfied: true });
  const numberFormat = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 4 });
  const dateFormat = new Intl.DateTimeFormat('fr-FR', { timeZone: 'UTC' });
  const dateTimeFormat = new Intl.DateTimeFormat('fr-FR', {
    dateStyle: 'short', timeStyle: 'medium', timeZone: 'UTC',
  });
  const scales = { m: 'm', mb: 'Mb', mc: 'Mc', ml: 'ML', md: 'MD', mw: 'MW' };
  let features = [];
  let index = null;
  let loaded = false;
  let controller = null;
  let popupPan = false;

  const formatValue = (value) => Number.isFinite(value) ? numberFormat.format(value) : 'Non renseigné';
  const formatDate = (value) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? 'Non renseignée' : `${dateTimeFormat.format(date)} UTC`;
  };
  const popup = (feature) => {
    const content = document.createElement('section');
    content.className = 'map-popup';
    const title = document.createElement('h2');
    title.textContent = 'Séisme';
    const details = document.createElement('dl');
    const properties = feature.properties;
    const scale = properties.magtype || '';
    const [longitude, latitude] = feature.geometry.coordinates;
    const region = properties.flynn_region;
    const entries = [
      ['Date', formatDate(properties.time)],
      ['Région', typeof region === 'string' ? region.charAt(0).toUpperCase() + region.slice(1).toLowerCase() : 'Non renseignée'],
      ['Pays / continent', `${properties.country || 'Inconnu'} / ${properties.continent || 'Inconnu'}`],
      ['Magnitude', `${formatValue(properties.mag)} ${scales[scale.toLowerCase()] || scale}`],
      ['Profondeur', Number.isFinite(properties.depth) ? `${formatValue(properties.depth)} km` : 'Non renseignée'],
      ['Latitude, longitude', `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`],
      ['Mise à jour', formatDate(properties.lastupdate)],
    ];
    for (const [label, value] of entries) {
      const term = document.createElement('dt');
      const description = document.createElement('dd');
      term.textContent = label;
      description.textContent = value;
      details.append(term, description);
    }
    content.append(title, details);
    return content;
  };

  spiderfier.addListener('click', (marker) => {
    L.popup({ maxWidth: 300, maxHeight: Math.max(180, map.getSize().y - 80) }).setLatLng(marker.getLatLng())
      .setContent(popup(marker.feature)).openOn(map);
  });
  spiderfier.addListener('spiderfy', () => map.closePopup());

  const draw = () => {
    spiderfier.unspiderfy();
    spiderfier.clearMarkers();
    markers.clearLayers();
    map.closePopup();
    if (!index) return;
    const bounds = map.getBounds();
    const west = bounds.getWest();
    const east = bounds.getEast();
    const normalize = (longitude) => ((longitude + 180) % 360 + 360) % 360 - 180;
    const bbox = east - west >= 360
      ? [-180, bounds.getSouth(), 180, bounds.getNorth()]
      : [normalize(west), bounds.getSouth(), normalize(east), bounds.getNorth()];
    const center = map.getCenter().lng;
    for (const feature of index.getClusters(bbox, Math.floor(map.getZoom()))) {
      const [longitude, latitude] = feature.geometry.coordinates;
      const position = [latitude, longitude + 360 * Math.round((center - longitude) / 360)];
      const properties = feature.properties;
      if (properties.cluster) {
        const label = document.createElement('span');
        label.textContent = numberFormat.format(properties.point_count);
        const marker = L.marker(position, {
          icon: L.divIcon({ className: 'map-cluster', html: label, iconSize: [48, 48] }),
          title: `${properties.point_count} séismes : zoomer`,
        }).addTo(markers);
        marker.on('click', () => {
          map.setView(position, Math.min(19, index.getClusterExpansionZoom(properties.cluster_id)));
        });
      } else {
        const marker = L.marker(position, {
          icon: L.divIcon({ className: 'map-point', html: '', iconSize: [18, 18] }),
          title: `Séisme · ${formatValue(properties.mag)} ${properties.magtype || ''}`,
        }).addTo(markers);
        marker.feature = feature;
        spiderfier.addMarker(marker);
      }
    }
  };

  const filterEvents = () => {
    const lower = minimum.value === '' ? -Infinity : minimum.valueAsNumber;
    const upper = maximum.value === '' ? Infinity : maximum.valueAsNumber;
    maximum.setCustomValidity(lower > upper ? 'Le maximum doit être supérieur ou égal au minimum.' : '');
    if (!minimum.checkValidity() || !maximum.checkValidity()) {
      status.textContent = 'Bornes de magnitude invalides. Les derniers filtres valides restent appliqués.';
      return;
    }
    const selected = earthquakes.checked ? features.filter((feature) => {
      const magnitude = feature.properties.mag;
      return (lower === -Infinity && upper === Infinity)
        || (Number.isFinite(magnitude) && magnitude >= lower && magnitude <= upper);
    }) : [];
    index = new Supercluster({ radius: 50, maxZoom: 18 }).load(selected);
    count.textContent = `${numberFormat.format(selected.length)} / ${numberFormat.format(features.length)} séismes`;
    status.textContent = selected.length ? '' : (features.length ? 'Aucun séisme ne correspond aux filtres.' : 'Aucun séisme sur cette période.');
    draw();
  };

  const validatePeriod = () => {
    endInput.setCustomValidity('');
    if (!startInput.value) return;
    const start = new Date(`${startInput.value}T00:00:00Z`);
    if (Number.isNaN(start.getTime())) return;
    const nextMonth = new Date(start);
    nextMonth.setUTCDate(1);
    nextMonth.setUTCMonth(nextMonth.getUTCMonth() + 1);
    const lastDay = new Date(nextMonth);
    lastDay.setUTCMonth(lastDay.getUTCMonth() + 1, 0);
    nextMonth.setUTCDate(Math.min(start.getUTCDate(), lastDay.getUTCDate()));
    endInput.min = startInput.value;
    endInput.max = nextMonth.toISOString().slice(0, 10);
    if (endInput.value && (endInput.value < endInput.min || endInput.value > endInput.max)) {
      endInput.setCustomValidity('Choisissez une fin comprise entre le début et un mois calendaire plus tard.');
    }
  };
  validatePeriod();
  startInput.addEventListener('input', validatePeriod);
  endInput.addEventListener('input', validatePeriod);
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    validatePeriod();
    if (!form.reportValidity()) return;
    if (loaded && (!minimum.reportValidity() || !maximum.reportValidity())) return;
    controller?.abort();
    const requestController = new AbortController();
    controller = requestController;
    const start = startInput.value;
    const end = endInput.value;
    const query = new URLSearchParams({ start, end });
    apply.disabled = true;
    localFilters.disabled = true;
    apply.textContent = 'Chargement…';
    container.setAttribute('aria-busy', 'true');
    status.textContent = 'Chargement des séismes…';
    showError('');
    try {
      const response = await fetch(`${form.dataset.endpoint}?${query}`, {
        signal: requestController.signal, credentials: 'same-origin', cache: 'no-store',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Chargement impossible.');
      if (data.type !== 'FeatureCollection' || !Array.isArray(data.features)) {
        throw new Error('Réponse géographique non reconnue.');
      }
      if (!data.features.every((feature) => feature.type === 'Feature'
        && feature.geometry?.type === 'Point' && feature.properties
        && Array.isArray(feature.geometry.coordinates) && feature.geometry.coordinates.length >= 2
        && feature.geometry.coordinates.slice(0, 2).every(Number.isFinite))) {
        throw new Error('Certaines coordonnées reçues sont invalides.');
      }
      features = data.features;
      loaded = true;
      localFilters.disabled = false;
      period.textContent = `${dateFormat.format(new Date(`${start}T00:00:00Z`))} – ${dateFormat.format(new Date(`${end}T00:00:00Z`))} · UTC`;
      filterEvents();
      if (matchMedia('(max-width: 750px)').matches) filters.open = false;
    } catch (error_) {
      if (error_.name !== 'AbortError') {
        showError(error_.message || 'Connexion au serveur impossible.');
        status.textContent = loaded ? 'La période précédente reste affichée.' : 'Aucune période chargée.';
      }
    } finally {
      if (controller === requestController) {
        apply.disabled = false;
        localFilters.disabled = !loaded;
        apply.textContent = 'Appliquer la période';
        container.removeAttribute('aria-busy');
      }
    }
  });
  for (const control of [earthquakes, minimum, maximum]) control.addEventListener('input', filterEvents);
  if (matchMedia('(max-width: 750px)').matches) filters.open = false;
  filters.addEventListener('toggle', () => map.invalidateSize());
  new ResizeObserver(() => map.invalidateSize()).observe(container);
  map.on('autopanstart', () => { popupPan = true; });
  map.on('moveend', () => {
    if (popupPan) {
      popupPan = false;
      return;
    }
    draw();
  });
})();