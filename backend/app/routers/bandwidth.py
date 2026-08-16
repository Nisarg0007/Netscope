from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.bandwidth_monitor import bandwidth_monitor
import asyncio
import json

router = APIRouter()

@router.get("/stats/current")
async def get_current_stats():
    """Get current bandwidth statistics for selected interface"""
    stats = bandwidth_monitor.get_selected_interface_stats()
    return stats

@router.websocket("/ws/bandwidth")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time bandwidth updates"""
    await websocket.accept()
    print("WebSocket client connected")
    try:
        while True:
            # Get current stats for selected interface
            stats = bandwidth_monitor.get_selected_interface_stats()
            if stats:
                await websocket.send_text(json.dumps(stats))
                print(f"Sent stats: {stats}")
            # Wait 1 second before sending next update
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Note: We don't stop monitoring here as other clients might be connected
        pass