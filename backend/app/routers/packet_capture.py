from fastapi import APIRouter, HTTPException
from app.services.packet_capture import packet_capture_service

router = APIRouter()

@router.get("/packet-capture/status")
async def get_capture_status():
    """Get packet capture status"""
    return packet_capture_service.get_capture_status()

@router.post("/packet-capture/start/{interface_name}")
async def start_capture(interface_name: str):
    """Start packet capture on specified interface"""
    success = packet_capture_service.start_capture(interface_name)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to start packet capture")
    return {"message": f"Packet capture started on interface {interface_name}"}

@router.post("/packet-capture/stop")
async def stop_capture():
    """Stop packet capture"""
    success = packet_capture_service.stop_capture()
    if not success:
        raise HTTPException(status_code=400, detail="Failed to stop packet capture")
    return {"message": "Packet capture stopped"}

@router.get("/packet-capture/packets")
async def get_packets(limit: int = 100):
    """Get captured packets"""
    packets = packet_capture_service.get_packets(limit=limit)
    return {"packets": packets}

@router.post("/packet-capture/clear")
async def clear_packets():
    """Clear captured packets"""
    packet_capture_service.clear_packets()
    return {"message": "Packet capture cleared"}
