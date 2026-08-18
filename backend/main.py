from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, interfaces, bandwidth, packet_capture, protocol_analysis, ip_analysis

app = FastAPI(
    title="NetScope API",
    description="Real-Time Network Bandwidth Analyzer & Traffic Monitor",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5175", "http://127.0.0.1:5175"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(interfaces.router, prefix="/api", tags=["interfaces"])
app.include_router(bandwidth.router, prefix="/api", tags=["bandwidth"])
app.include_router(packet_capture.router, prefix="/api", tags=["packet-capture"])
app.include_router(protocol_analysis.router, prefix="/api", tags=["protocol-analysis"])
app.include_router(ip_analysis.router, prefix="/api", tags=["ip-analysis"])

@app.get("/")
async def root():
    return {"message": "NetScope API is running"}