import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.services.packet_capture import packet_capture_service


class PortAnalysisService:
    def __init__(self):
        self.lock = threading.RLock()
        # Common port to service mapping
        self.common_ports = {
            20: "FTP",
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            67: "DHCP",
            68: "DHCP",
            80: "HTTP",
            110: "POP3",
            123: "NTP",
            143: "IMAP",
            161: "SNMP",
            443: "HTTPS",
            3306: "MySQL",
            5432: "PostgreSQL",
            6379: "Redis",
            8080: "HTTP Alternate"
        }

    def _get_common_service(self, port: int, protocol: str) -> str:
        """
        Get common service name for a port, returns "Unknown" if not found.
        Note: Same port number can have different services for TCP/UDP, but we keep it simple.
        """
        return self.common_ports.get(port, "Unknown")

    def get_top_source_ports(self, limit: int = 10, sort_by: str = "bytes") -> Dict[str, Any]:
        """
        Get top source ports by packet count or byte count for TCP/UDP packets.

        Args:
            limit: Maximum number of results to return (default 10)
            sort_by: Field to sort by - "bytes" or "packet_count" (default "bytes")

        Returns:
            Dictionary containing port statistics
        """
        # Validate inputs
        if limit < 1:
            limit = 1
        elif limit > 1000:
            limit = 1000

        if sort_by not in ["bytes", "packet_count"]:
            sort_by = "bytes"

        with self.lock:
            packets = packet_capture_service.packets.copy()

        # Aggregate by source port and protocol
        port_stats = {}  # key: (port, protocol)

        for packet in packets:
            # Only process TCP and UDP packets that have source port
            protocol = packet.get('protocol')
            src_port = packet.get('src_port')
            if protocol not in ['tcp', 'udp'] or src_port is None:
                continue

            key = (src_port, protocol.upper())  # Store protocol as uppercase for consistency

            if key not in port_stats:
                port_stats[key] = {
                    'port': src_port,
                    'protocol': protocol.upper(),
                    'common_service': self._get_common_service(src_port, protocol),
                    'packet_count': 0,
                    'total_bytes': 0
                }

            port_stats[key]['packet_count'] += 1
            port_stats[key]['total_bytes'] += packet.get('length', 0)

        # Convert to list and calculate percentages
        port_list = list(port_stats.values())

        # Calculate total for percentage calculation (only TCP/UDP packets)
        total_packets = sum(item['packet_count'] for item in port_list)
        total_bytes = sum(item['total_bytes'] for item in port_list)

        for item in port_list:
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
            port_list.sort(key=lambda x: x['total_bytes'], reverse=reverse)
        else:  # sort_by == "packet_count"
            port_list.sort(key=lambda x: x['packet_count'], reverse=reverse)

        # Apply limit
        limited_list = port_list[:limit]

        return {
            'source_ports': limited_list,
            'total_unique_ports': len(port_list),
            'total_packets': total_packets,
            'total_bytes': total_bytes,
            'timestamp': datetime.now().isoformat()
        }

    def get_top_destination_ports(self, limit: int = 10, sort_by: str = "bytes") -> Dict[str, Any]:
        """
        Get top destination ports by packet count or byte count for TCP/UDP packets.

        Args:
            limit: Maximum number of results to return (default 10)
            sort_by: Field to sort by - "bytes" or "packet_count" (default "bytes")

        Returns:
            Dictionary containing port statistics
        """
        # Validate inputs
        if limit < 1:
            limit = 1
        elif limit > 1000:
            limit = 1000

        if sort_by not in ["bytes", "packet_count"]:
            sort_by = "bytes"

        with self.lock:
            packets = packet_capture_service.packets.copy()

        # Aggregate by destination port and protocol
        port_stats = {}  # key: (port, protocol)

        for packet in packets:
            # Only process TCP and UDP packets that have destination port
            protocol = packet.get('protocol')
            dst_port = packet.get('dst_port')
            if protocol not in ['tcp', 'udp'] or dst_port is None:
                continue

            key = (dst_port, protocol.upper())  # Store protocol as uppercase for consistency

            if key not in port_stats:
                port_stats[key] = {
                    'port': dst_port,
                    'protocol': protocol.upper(),
                    'common_service': self._get_common_service(dst_port, protocol),
                    'packet_count': 0,
                    'total_bytes': 0
                }

            port_stats[key]['packet_count'] += 1
            port_stats[key]['total_bytes'] += packet.get('length', 0)

        # Convert to list and calculate percentages
        port_list = list(port_stats.values())

        # Calculate total for percentage calculation (only TCP/UDP packets)
        total_packets = sum(item['packet_count'] for item in port_list)
        total_bytes = sum(item['total_bytes'] for item in port_list)

        for item in port_list:
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
            port_list.sort(key=lambda x: x['total_bytes'], reverse=reverse)
        else:  # sort_by == "packet_count"
            port_list.sort(key=lambda x: x['packet_count'], reverse=reverse)

        # Apply limit
        limited_list = port_list[:limit]

        return {
            'destination_ports': limited_list,
            'total_unique_ports': len(port_list),
            'total_packets': total_packets,
            'total_bytes': total_bytes,
            'timestamp': datetime.now().isoformat()
        }

    def get_port_traffic_summary(self, limit: int = 10, sort_by: str = "bytes") -> Dict[str, Any]:
        """
        Get combined port traffic statistics (both source and destination)

        Args:
            limit: Maximum number of results to return for each (default 10)
            sort_by: Field to sort by - "bytes" or "packet_count" (default "bytes")

        Returns:
            Dictionary containing both source and destination port statistics
        """
        source_data = self.get_top_source_ports(limit=limit, sort_by=sort_by)
        dest_data = self.get_top_destination_ports(limit=limit, sort_by=sort_by)

        return {
            'source_ports': source_data['source_ports'],
            'destination_ports': dest_data['destination_ports'],
            'summary': {
                'total_unique_source_ports': source_data['total_unique_ports'],
                'total_unique_destination_ports': dest_data['total_unique_ports'],
                'total_packets': source_data['total_packets'],  # Should be same as dest
                'total_bytes': source_data['total_bytes']       # Should be same as dest
            },
            'timestamp': source_data['timestamp']
        }


# Global instance
port_analysis_service = PortAnalysisService()