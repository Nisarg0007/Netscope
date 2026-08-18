import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.services.packet_capture import packet_capture_service


class IPAnalysisService:
    def __init__(self):
        self.lock = threading.RLock()  # Using RLock for potential nested locking scenarios
        # We'll compute on-demand from packet_capture_service rather than storing duplicated data
        # This ensures consistency and avoids synchronization issues

    def get_top_source_ips(self, limit: int = 10, sort_by: str = "bytes") -> Dict[str, Any]:
        """
        Get top source IPs by packet count or byte count

        Args:
            limit: Maximum number of results to return (default 10)
            sort_by: Field to sort by - "bytes" or "packet_count" (default "bytes")

        Returns:
            Dictionary containing IP statistics
        """
        # Validate inputs
        if limit < 1:
            limit = 1
        elif limit > 1000:  # Reasonable upper bound
            limit = 1000

        if sort_by not in ["bytes", "packet_count"]:
            sort_by = "bytes"

        with self.lock:
            # Get a copy of packets to avoid holding lock during processing
            packets = packet_capture_service.packets.copy()

        # Aggregate by source IP
        ip_stats = {}

        for packet in packets:
            src_ip = packet.get('src_ip')
            if not src_ip:
                continue

            if src_ip not in ip_stats:
                ip_stats[src_ip] = {
                    'ip_address': src_ip,
                    'packet_count': 0,
                    'total_bytes': 0
                }

            ip_stats[src_ip]['packet_count'] += 1
            ip_stats[src_ip]['total_bytes'] += packet.get('length', 0)

        # Convert to list and calculate percentages
        ip_list = list(ip_stats.values())

        # Calculate total for percentage calculation
        total_packets = sum(item['packet_count'] for item in ip_list)
        total_bytes = sum(item['total_bytes'] for item in ip_list)

        for item in ip_list:
            if total_packets > 0:
                item['packet_percentage'] = round((item['packet_count'] / total_packets) * 100, 2)
            else:
                item['packet_percentage'] = 0.0

            if total_bytes > 0:
                item['byte_percentage'] = round((item['total_bytes'] / total_bytes) * 100, 2)
            else:
                item['byte_percentage'] = 0.0

        # Sort based on sort_by parameter
        reverse = True  # Descending order (top values first)
        if sort_by == "bytes":
            ip_list.sort(key=lambda x: x['total_bytes'], reverse=reverse)
        else:  # sort_by == "packet_count"
            ip_list.sort(key=lambda x: x['packet_count'], reverse=reverse)

        # Apply limit
        limited_list = ip_list[:limit]

        return {
            'source_ips': limited_list,
            'total_unique_ips': len(ip_list),
            'total_packets': total_packets,
            'total_bytes': total_bytes,
            'timestamp': datetime.now().isoformat()
        }

    def get_top_destination_ips(self, limit: int = 10, sort_by: str = "bytes") -> Dict[str, Any]:
        """
        Get top destination IPs by packet count or byte count

        Args:
            limit: Maximum number of results to return (default 10)
            sort_by: Field to sort by - "bytes" or "packet_count" (default "bytes")

        Returns:
            Dictionary containing IP statistics
        """
        # Validate inputs
        if limit < 1:
            limit = 1
        elif limit > 1000:  # Reasonable upper bound
            limit = 1000

        if sort_by not in ["bytes", "packet_count"]:
            sort_by = "bytes"

        with self.lock:
            # Get a copy of packets to avoid holding lock during processing
            packets = packet_capture_service.packets.copy()

        # Aggregate by destination IP
        ip_stats = {}

        for packet in packets:
            dst_ip = packet.get('dst_ip')
            if not dst_ip:
                continue

            if dst_ip not in ip_stats:
                ip_stats[dst_ip] = {
                    'ip_address': dst_ip,
                    'packet_count': 0,
                    'total_bytes': 0
                }

            ip_stats[dst_ip]['packet_count'] += 1
            ip_stats[dst_ip]['total_bytes'] += packet.get('length', 0)

        # Convert to list and calculate percentages
        ip_list = list(ip_stats.values())

        # Calculate total for percentage calculation
        total_packets = sum(item['packet_count'] for item in ip_list)
        total_bytes = sum(item['total_bytes'] for item in ip_list)

        for item in ip_list:
            if total_packets > 0:
                item['packet_percentage'] = round((item['packet_count'] / total_packets) * 100, 2)
            else:
                item['packet_percentage'] = 0.0

            if total_bytes > 0:
                item['byte_percentage'] = round((item['total_bytes'] / total_bytes) * 100, 2)
            else:
                item['byte_percentage'] = 0.0

        # Sort based on sort_by parameter
        reverse = True  # Descending order (top values first)
        if sort_by == "bytes":
            ip_list.sort(key=lambda x: x['total_bytes'], reverse=reverse)
        else:  # sort_by == "packet_count"
            ip_list.sort(key=lambda x: x['packet_count'], reverse=reverse)

        # Apply limit
        limited_list = ip_list[:limit]

        return {
            'destination_ips': limited_list,
            'total_unique_ips': len(ip_list),
            'total_packets': total_packets,
            'total_bytes': total_bytes,
            'timestamp': datetime.now().isoformat()
        }

    def get_ip_traffic_summary(self, limit: int = 10, sort_by: str = "bytes") -> Dict[str, Any]:
        """
        Get combined IP traffic statistics (both source and destination)

        Args:
            limit: Maximum number of results to return for each (default 10)
            sort_by: Field to sort by - "bytes" or "packet_count" (default "bytes")

        Returns:
            Dictionary containing both source and destination IP statistics
        """
        source_data = self.get_top_source_ips(limit=limit, sort_by=sort_by)
        dest_data = self.get_top_destination_ips(limit=limit, sort_by=sort_by)

        return {
            'source_ips': source_data['source_ips'],
            'destination_ips': dest_data['destination_ips'],
            'summary': {
                'total_unique_source_ips': source_data['total_unique_ips'],
                'total_unique_destination_ips': dest_data['total_unique_ips'],
                'total_packets': source_data['total_packets'],  # Should be same as dest
                'total_bytes': source_data['total_bytes']       # Should be same as dest
            },
            'timestamp': source_data['timestamp']
        }


# Global instance
ip_analysis_service = IPAnalysisService()