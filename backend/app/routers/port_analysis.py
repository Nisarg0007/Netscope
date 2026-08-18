from fastapi import APIRouter, HTTPException, Query
from app.services.port_analysis import port_analysis_service

router = APIRouter()

@router.get("/port-analysis/stats/source")
async def get_top_source_ports(
    limit: int = Query(10, ge=1, le=1000, description="Maximum number of results to return"),
    sort_by: str = Query("bytes", regex="^(bytes|packet_count)$", description="Field to sort by: 'bytes' or 'packet_count'")
):
    """Get top source ports by traffic volume"""
    try:
        stats = port_analysis_service.get_top_source_ports(limit=limit, sort_by=sort_by)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get source port stats: {str(e)}")

@router.get("/port-analysis/stats/destination")
async def get_top_destination_ports(
    limit: int = Query(10, ge=1, le=1000, description="Maximum number of results to return"),
    sort_by: str = Query("bytes", regex="^(bytes|packet_count)$", description="Field to sort by: 'bytes' or 'packet_count'")
):
    """Get top destination ports by traffic volume"""
    try:
        stats = port_analysis_service.get_top_destination_ports(limit=limit, sort_by=sort_by)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get destination port stats: {str(e)}")

@router.get("/port-analysis/stats/summary")
async def get_port_traffic_summary(
    limit: int = Query(10, ge=1, le=1000, description="Maximum number of results to return for each"),
    sort_by: str = Query("bytes", regex="^(bytes|packet_count)$", description="Field to sort by: 'bytes' or 'packet_count'")
):
    """Get combined port traffic statistics for both source and destination ports"""
    try:
        stats = port_analysis_service.get_port_traffic_summary(limit=limit, sort_by=sort_by)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get port traffic summary: {str(e)}")