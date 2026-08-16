# NetScope — Real-Time Network Bandwidth Analyzer & Traffic Monitor

A computer networks course project for monitoring and analyzing real-time network traffic.

## Project Structure

```
netscope/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── app/                    # Application modules
│   │   ├── api/                # API route definitions
│   │   ├── core/               # Core configuration and utilities
│   │   ├── db/                 # Database models and setup
│   │   ├── models/             # SQLAlchemy models
│   │   ├── routers/            # API routers
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Service layers (bandwidth monitoring)
│   │   └── utils/              # Utility functions
│   ├── requirements.txt        # Python dependencies
│   └── .env                    # Environment variables
├── frontend/
│   ├── src/
│   │   ├── components/         # React components (InterfaceSelector, BandwidthDisplay)
│   │   ├── services/           # API service calls (apiService, wsService)
│   │   ├── utils/              # Utility functions
│   │   └── styles/             # CSS/Tailwind styles
│   ├── public/                 # Static assets
│   ├── package.json            # Frontend dependencies
│   ├── vite.config.js          # Vite configuration
│   └── tailwind.config.js      # Tailwind CSS configuration
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Features

- Network interface discovery (IPv4, IPv6, MAC, status, traffic stats)
- Real-time network bandwidth monitoring with live updates
- Upload/download speed calculation (bps, Mbps)
- Packet rate monitoring (packets/sec)
- Total data transferred tracking
- WebSocket connection for real-time updates
- Interface selection for targeted monitoring
- RESTful API backend
- React frontend with Tailwind CSS

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn
- Administrator privileges (required for full network access)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the development server:
   ```bash
   uvicorn main:app --reload --host 127.0.0.1 --port 8003
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

### Access the Application

- Backend API: http://127.0.0.1:8003
- Frontend: http://localhost:5173
- Health Check: http://127.0.0.1:8003/api/health

## API Endpoints

- `GET /` - Root endpoint with welcome message
- `GET /api/health` - Health check endpoint
- `GET /api/interfaces` - Get all network interfaces
- `POST /api/interfaces/select/{interface_name}` - Select interface for monitoring
- `POST /api/interfaces/deselect` - Stop monitoring selected interface
- `GET /api/stats/current` - Get current bandwidth statistics for selected interface
- `WS /api/ws/bandwidth` - WebSocket endpoint for real-time bandwidth updates

## Real-Time Bandwidth Monitoring

The bandwidth monitoring feature provides:

1. **Interface Selection**: Choose which network interface to monitor
2. **Live Updates**: WebSocket connection pushes updates every second
3. **Speed Calculations**:
   - Download/Upload speed in bits per second (bps)
   - Download/Upload speed in megabits per second (Mbps)
4. **Packet Statistics**:
   - Packets received/second (pps)
   - Packets sent/second (pps)
5. **Cumulative counters**:
   - Total bytes sent/received
   - Total packets sent/received

## Usage Instructions

1. **Start both servers** (backend and frontend) as described above
2. **Open your browser** to `http://localhost:5173`
3. **Select an interface** from the list (look for interfaces with status "up")
4. **View live bandwidth data** in the Bandwidth Display section
5. **Generate network traffic** by browsing websites, downloading files, or streaming video to see the values change
6. **Stop monitoring** by clicking the "Stop Monitoring" button when desired

## Windows-Specific Notes

- Requires **administrator privileges** for full network interface access
- Tested on Windows 11 with various network adapters (Wi-Fi, Ethernet)
- All data is real - no mock or simulated values are used
- Uses actual OS network counters through the `psutil` library

## How It Works

### Bandwidth Calculation
The system calculates real transfer rates by:
1. Taking two measurements of network counters (bytes sent/received, packets sent/received)
2. Measuring the time elapsed between measurements
3. Calculating the rate: `(current_value - previous_value) / time_elapsed`

### WebSocket Connection
- The frontend establishes a WebSocket connection to `/api/ws/bandwidth`
- The server sends updated statistics every second
- The frontend updates the display without requiring page refreshes

## Monitoring Capabilities

When monitoring an interface, you can observe:

- **Instantaneous speeds**: Current upload/download rates
- **Data volumes**: Total bytes transferred since monitoring started
- **Packet rates**: How many packets are flowing in each direction
- **Interface utilization**: Percentage of bandwidth being used (calculate from Mbps vs interface speed)

## Example Values to Expect

- **Idle connection**: 0-100 Kbps (background system traffic)
- **Web browsing**: 1-10 Mbps (bursty as pages load)
- **Video streaming**: 5-25 Mbps (depending on quality)
- **File download**: Varies widely based on connection speed
- **Packet rates**: Typically 10-1000+ pps during active usage

## Technologies Used

- **Backend**: FastAPI, Uvicorn, Psutil, WebSockets
- **Frontend**: React, Vite, Tailwind CSS, WebSocket API
- **Communication**: REST API (control) + WebSocket (real-time data)

## License

MIT License - Feel free to use and modify for educational purposes.