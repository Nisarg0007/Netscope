const WS_URL = 'ws://127.0.0.1:8004/api/ws/bandwidth';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.listeners = [];
  }

  connect() {
    console.log(`Attempting to connect to WebSocket: ${WS_URL}`);
    this.ws = new WebSocket(WS_URL);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      console.log('WebSocket message received:', event.data);
      const data = JSON.parse(event.data);
      this.listeners.forEach(listener => listener(data));
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Try to reconnect after 3 seconds
      setTimeout(() => this.connect(), 3000);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect() {
    console.log('WebSocket disconnecting');
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(callback) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter(l => l !== callback);
    };
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

export const wsService = new WebSocketService();