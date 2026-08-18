import threading
import logging
from typing import Dict, Any
from datetime import datetime
from app.services.packet_capture import packet_capture_service
from app.services.protocol_analysis import protocol_analysis_service
from app.services.ip_analysis import ip_analysis_service
from app.services.port_analysis import port_analysis_service

logger = logging.getLogger(__name__)


class TrafficAnalysisService:
    def __init__(self):
        self.lock = threading.RLock()

    def get_unified_traffic_summary(self, limit: int = 10, sort_by: str = "bytes") -> Dict[str, Any]:
        """
        Get a unified summary of all traffic analysis data.

        Args:
            limit: Maximum number of results to return for IP and port sections (default 10)
            sort_by: Field to sort by for IP and port sections - "bytes" or "packet_count" (default "bytes")

        Returns:
            Dictionary containing overall, protocols, source_ips, destination_ips,
            source_ports, destination_ports, and timestamp
        """
        # Validate inputs
        if limit < 1:
            limit = 1
        elif limit > 1000:
            limit = 1000

        if sort_by not in ["bytes", "packet_count"]:
            sort_by = "bytes"

        # Initialize response structure
        result = {
            "overall": {},
            "protocols": {},
            "source_ips": [],
            "destination_ips": [],
            "source_ports": [],
            "destination_ports": [],
            "timestamp": datetime.now().isoformat()
        }

        # Get protocol stats (overall and protocols)
        try:
            with self.lock:
                protocol_stats = protocol_analysis_service.get_protocol_stats()
            result["overall"] = protocol_stats.get("overall", {})
            result["protocols"] = protocol_stats.get("protocols", {})
            # Use the timestamp from protocol stats if available, otherwise keep current time
            if "timestamp" in protocol_stats:
                result["timestamp"] = protocol_stats["timestamp"]
        except Exception as e:
            logger.error(f"Failed to get protocol stats: {e}")
            # Keep empty overall and protocols

        # Get source IPs
        try:
            with self.lock:
                source_ips_data = ip_analysis_service.get_top_source_ips(limit=limit, sort_by=sort_by)
            result["source_ips"] = source_ips_data.get("source_ips", [])
        except Exception as e:
            logger.error(f"Failed to get source IP stats: {e}")
            result["source_ips"] = []

        # Get destination IPs
        try:
            with self.lock:
                dest_ips_data = ip_analysis_service.get_top_destination_ips(limit=limit, sort_by=sort_by)
            result["destination_ips"] = dest_ips_data.get("destination_ips", [])
        except Exception as e:
            logger.error(f"Failed to get destination IP stats: {e}")
            result["destination_ips"] = []

        # Get source ports
        try:
            with self.lock:
                source_ports_data = port_analysis_service.get_top_source_ports(limit=limit, sort_by=sort_by)
            result["source_ports"] = source_ports_data.get("source_ports", [])
        except Exception as e:
            logger.error(f"Failed to get source port stats: {e}")
            result["source_ports"] = []

        # Get destination ports
        try:
            with self.lock:
                dest_ports_data = port_analysis_service.get_top_destination_ports(limit=limit, sort_by=sort_by)
            result["destination_ports"] = dest_ports_data.get("destination_ports", [])
        except Exception as e:
            logger.error(f"Failed to get destination port stats: {e}")
            result["destination_ports"] = []

        return result


# Global instance
traffic_analysis_service = TrafficAnalysisService()