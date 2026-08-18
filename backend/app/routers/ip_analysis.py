from fastapi import APIRouter, HTTPException, Query
from app.services.ip_analysis import ip_analysis_service

router = APIRouter()

@router.get("/ip-analysis/stats/source")
async def get_top_source_ips(
    limit: int = Query(10, ge=1, le=1000, description="Maximum number of results to return"),
    sort_by: str = Query("bytes", regex="^(bytes|packet_count)$", description="Field to sort by: 'bytes' or 'packet_count'")
):
    """Get top source IP addresses by traffic volume"""
    try:
        stats = ip_analysis_service.get_top_source_ips(limit=limit, sort_by=sort_by)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get source IP stats: {str(e)}")

@router.get("/ip-analysis/stats/destination")
async def get_top_destination_ips(
    limit: int = Query(10, ge=1, le=1000, description="Maximum number of results to return"),
    sort_by: str = Query("bytes", regex="^(bytes|packet_count)$", description="Field to sort by: 'bytes' or 'packet_count'")
):
    """Get top destination IP addresses by traffic volume"""
    try:
        stats = ip_analysis_service.get_top_destination_ips(limit=limit, sort_by=sort_by)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get destination IP stats: {str(e)}")

@router.get("/ip-analysis/stats/summary")
async def get_ip_traffic_summary(
    limit: int = Query(10, ge=1, le=1000, description="Maximum number of results to return for each"),
    sort_by: str = Query("bytes", regex="^(bytes|packet_count)$", description="Field to sort by: 'bytes' or 'packet_count'")
):
    """Get combined IP traffic statistics for both source and destination IPs"""
    try:
        stats = ip_analysis_service.get_ip_traffic_summary(limit=limit, sort_by=sort_by)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get IP traffic summary: {str(e)}")