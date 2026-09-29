(() => {
  const eventsBody = document.getElementById('events');
  const status = document.getElementById('connection-status');
  if (!eventsBody || !status) return;
  let lastEventId = null;

  const magnitudeScales = {
    m: 'm',
    mb: 'Mb',
    mc: 'Mc',
    ml: 'ML',
    md: 'MD',
    mw: 'MW',
  };
  const eventTypeLabels = {
    earthquakes: 'Séisme',
    flood: 'Inondation',
    floods: 'Inondation',
  };

  const capitalize = (value) => {
    if (typeof value !== 'string' || !value.trim()) return 'Inconnu';
    const normalized = value.trim().toLocaleLowerCase('fr-FR');
    return normalized.charAt(0).toLocaleUpperCase('fr-FR') + normalized.slice(1);
  };

  const formatNumber = (value, maximumFractionDigits = 2) => {
    if (!Number.isFinite(value)) return 'inconnue';
    return new Intl.NumberFormat('fr-FR', { maximumFractionDigits }).format(value);
  };

  const formatCoordinate = (value) => Number.isFinite(value) ? value.toFixed(4) : 'inconnue';

  const formatEventTime = (value) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return null;
    return {
      dateTime: date.toISOString(),
      date: new Intl.DateTimeFormat('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        timeZone: 'UTC',
      }).format(date),
      time: new Intl.DateTimeFormat('fr-FR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hourCycle: 'h23',
        timeZone: 'UTC',
      }).format(date),
    };
  };

  const createBadge = (label, className) => {
    const badge = document.createElement('span');
    badge.className = className;
    badge.textContent = label;
    return badge;
  };

  const renderEvent = (message) => {
    const feature = message.event && typeof message.event === 'object' ? message.event : {};
    const properties = feature.properties && typeof feature.properties === 'object'
      ? feature.properties
      : {};
    const coordinates = Array.isArray(feature.geometry?.coordinates)
      ? feature.geometry.coordinates
      : [];
    const latitude = Number.isFinite(properties.lat) ? properties.lat : coordinates[1];
    const longitude = Number.isFinite(properties.lon) ? properties.lon : coordinates[0];
    const scaleKey = typeof properties.magtype === 'string'
      ? properties.magtype.trim().toLowerCase()
      : '';
    const scale = magnitudeScales[scaleKey] || properties.magtype || 'échelle inconnue';
    const eventTime = formatEventTime(properties.time);

    const row = document.createElement('tr');
    const dateCell = document.createElement('td');
    const timeCell = document.createElement('td');
    if (eventTime) {
      const time = document.createElement('time');
      time.dateTime = eventTime.dateTime;
      time.textContent = eventTime.date;
      dateCell.append(time);
      timeCell.textContent = eventTime.time;
    } else {
      dateCell.textContent = 'Date inconnue';
      timeCell.textContent = 'Heure inconnue';
    }

    const typeCell = document.createElement('td');
    const type = typeof message.type === 'string' ? message.type.toLowerCase() : '';
    const typeLabel = eventTypeLabels[type] || capitalize(message.type);
    const typeClass = type === 'earthquakes' ? 'event-badge--earthquake' : 'event-badge--flood';
    typeCell.append(createBadge(typeLabel, `event-badge ${typeClass}`));

    const geographyCell = document.createElement('td');
    geographyCell.className = 'event-geography';
    geographyCell.append(
      createBadge(properties.continent || 'Continent inconnu', 'event-badge event-badge--geography'),
      createBadge(properties.country || 'Pays inconnu', 'event-badge event-badge--geography'),
    );

    const metricsCell = document.createElement('td');
    metricsCell.className = 'event-metrics';
    const magnitude = document.createElement('strong');
    magnitude.textContent = `${formatNumber(properties.mag)} ${scale}`;
    const depth = document.createElement('span');
    depth.textContent = `Profondeur ${formatNumber(properties.depth, 1)} km`;
    const coordinatesText = document.createElement('span');
    coordinatesText.textContent = `Coordonnées ${formatCoordinate(latitude)}, ${formatCoordinate(longitude)}`;
    metricsCell.append(magnitude, depth, coordinatesText);

    row.append(dateCell, timeCell, typeCell, geographyCell, metricsCell);
    return row;
  };

  const connect = () => {
    const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const cursor = lastEventId ? `?since=${encodeURIComponent(lastEventId)}` : '';
    const socket = new WebSocket(`${scheme}//${location.host}/ws/events${cursor}`);
    socket.onopen = () => { status.textContent = 'Connecté'; };
    socket.onmessage = ({ data }) => {
      try {
        const message = JSON.parse(data);
        eventsBody.prepend(renderEvent(message));
        lastEventId = message.id;
        while (eventsBody.children.length > 100) eventsBody.lastElementChild.remove();
      } catch { status.textContent = 'Message non reconnu'; }
    };
    socket.onclose = () => { status.textContent = 'Reconnexion…'; setTimeout(connect, 5000); };
  };
  connect();
})();