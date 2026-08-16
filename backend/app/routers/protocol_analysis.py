from fastapi import APIRouter, HTTPException
from app.services.protocol_analysis import protocol_analysis_service

router = APIRouter()

@router.get("/protocol-analysis/stats")
async def get_protocol_stats():
    """Get protocol traffic analysis statistics"""
    try:
        stats = protocol_analysis_service.get_protocol_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get protocol stats: {str(e)}")

@router.get("/protocol-analysis/stats/simple")
async def get_protocol_stats_simple():
    """Get simplified protocol traffic analysis statistics"""
    try:
        stats = protocol_analysis_service.get_protocol_stats_simple()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get protocol stats: {str(e)}")