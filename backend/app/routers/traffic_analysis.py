from fastapi import APIRouter, HTTPException, Query
from app.services.traffic_analysis import traffic_analysis_service

router = APIRouter()

@router.get("/traffic-analysis/summary")
async def get_unified_traffic_summary(
    limit: int = Query(10, ge=1, le=1000, description="Maximum number of results to return for IP and port sections"),
    sort_by: str = Query("bytes", regex="^(bytes|packet_count)$", description="Field to sort by: 'bytes' or 'packet_count'")
):
    """Get unified traffic analysis summary"""
    try:
        stats = traffic_analysis_service.get_unified_traffic_summary(limit=limit, sort_by=sort_by)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get unified traffic summary: {str(e)}")