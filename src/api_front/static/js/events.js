(() => {
  const list = document.getElementById('events');
  const status = document.getElementById('connection-status');
  if (!list || !status) return;
  let lastEventId = null;

  const connect = () => {
    const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const cursor = lastEventId ? `?since=${encodeURIComponent(lastEventId)}` : '';
    const socket = new WebSocket(`${scheme}//${location.host}/ws/events${cursor}`);
    socket.onopen = () => { status.textContent = 'Connecté'; };
    socket.onmessage = ({ data }) => {
      try {
        const message = JSON.parse(data);
        const item = document.createElement('li');
        const time = document.createElement('small');
        time.textContent = new Date().toLocaleTimeString('fr-FR');
        const event = document.createElement('span');
        event.textContent = `${message.type || 'Événement'} · ${JSON.stringify(message.event)}`;
        item.append(time, event);
        list.prepend(item);
        lastEventId = message.id;
        while (list.children.length > 100) list.lastElementChild.remove();
      } catch { status.textContent = 'Message non reconnu'; }
    };
    socket.onclose = () => { status.textContent = 'Reconnexion…'; setTimeout(connect, 5000); };
  };
  connect();
})();