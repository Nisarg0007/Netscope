import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8004/api/ws/bandwidth"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")
            while True:
                response = await websocket.recv()
                print("Received:", response)
                # Parse JSON to see the stats
                data = json.loads(response)
                print("Parsed stats:", data)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_websocket())